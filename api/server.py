"""
FastAPI Server for the OEE Manufacturing Analytics Assistant.

Provides a thin REST API layer over the existing pipeline components.
Does NOT modify any backend logic — simply reuses the existing classes.

Endpoints:
    GET  /api/health    — System health check
    GET  /api/machines  — Available machine list
    POST /api/analyze   — Run full pipeline for a natural language query
"""

import os
import sys
import logging
import time
from typing import Optional

import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_FILE_PATH
from database.init_db import initialize_database
from database.database import Database
from database.repositories import ProductionRepository
from core.query_service import QueryService
from core.validator import DataValidator
from core.oee_calculator import OEECalculator
from analysis.error_code_resolver import ErrorCodeResolver
from analysis.loss_analyzer import LossAnalyzer
from analysis.business_impact import BusinessImpactEngine

logger = logging.getLogger(__name__)

# ── FastAPI App ──────────────────────────────────────────────────────

app = FastAPI(
    title="OEE Manufacturing Analytics API",
    version="1.0.0",
    description="REST API for OEE Manufacturing Intelligence",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    query: str


class HealthResponse(BaseModel):
    status: str
    database: str
    machines_count: int


# ── Pipeline Singleton ───────────────────────────────────────────────

class Pipeline:
    """Singleton that initializes pipeline components once."""

    _instance: Optional["Pipeline"] = None

    def __init__(self) -> None:
        if not os.path.exists(DB_FILE_PATH):
            initialize_database()

        self.db = Database()
        self.repo = ProductionRepository(self.db)
        self.available_machines = self.repo.get_available_machines()
        self.query_service = QueryService()
        self.validator = DataValidator()
        self.calculator = OEECalculator()
        self.resolver = ErrorCodeResolver()
        self.analyzer = LossAnalyzer()
        self.business_engine = BusinessImpactEngine()

    @classmethod
    def get(cls) -> "Pipeline":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# ── Helper: DataFrame → JSON-safe dict ───────────────────────────────

def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Converts DataFrame to JSON-serializable list of dicts."""
    result = df.copy()
    for col in result.columns:
        if result[col].dtype == "object":
            continue
        result[col] = result[col].apply(
            lambda x: None if (isinstance(x, float) and np.isnan(x)) else x
        )
    return result.to_dict(orient="records")


# ── Endpoints ────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check() -> dict:
    """System health check."""
    try:
        pipe = Pipeline.get()
        return {
            "status": "healthy",
            "database": "connected",
            "machines_count": len(pipe.available_machines),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/machines")
def get_machines() -> dict:
    """Returns available machine list."""
    pipe = Pipeline.get()
    return {"machines": pipe.available_machines}


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    """
    Runs the full analysis pipeline for a natural language query.

    Returns structured JSON with:
      - summary: KPI statistics
      - records: Full enriched record list
      - ai_stats: AI processing statistics
      - query_context: Parsed filter details
    """
    pipe = Pipeline.get()

    # 1. NL-to-SQL (Query Service)
    try:
        raw_df, valid_sql = pipe.query_service.process_query(request.query)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to generate valid SQL for your query: {e}",
        )

    if raw_df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No records found for query. SQL Executed:\n{valid_sql}",
        )

    # 3. Validate
    validated_df = pipe.validator.validate(raw_df)

    # 4. OEE Calculation
    oee_df = pipe.calculator.calculate(validated_df)

    # 5. Error Code Resolution
    resolved_df = pipe.resolver.resolve(oee_df)

    # 6. AI Manufacturing Intelligence
    start_time = time.time()
    ai_df = pipe.analyzer.analyze(resolved_df)
    groq_time = time.time() - start_time

    # 7. Business Impact
    analysis_df = pipe.business_engine.calculate(ai_df)

    # 8. Export CSVs (Sync with UI)
    try:
        from main import _generate_runtime_csvs
        _generate_runtime_csvs(raw_df, validated_df, oee_df, analysis_df)
    except Exception as e:
        logger.error(f"Failed to generate CSVs: {e}")

    # ── Build Response ───────────────────────────────────────────

    records = _df_to_records(analysis_df)

    # Summary KPIs
    summary = {
        "records_count": len(analysis_df),
        "avg_oee": round(float(analysis_df["OEE"].mean()), 2),
        "max_oee": round(float(analysis_df["OEE"].max()), 2),
        "min_oee": round(float(analysis_df["OEE"].min()), 2),
        "avg_availability": round(float(analysis_df["Availability"].mean()), 2),
        "avg_performance": round(float(analysis_df["Performance"].mean()), 2),
        "avg_quality": round(float(analysis_df["Quality"].mean()), 2),
    }

    # Business impact summary
    if "Estimated Business Loss" in analysis_df.columns:
        summary["total_business_loss"] = round(
            float(analysis_df["Estimated Business Loss"].sum()), 2
        )
        summary["avg_business_loss"] = round(
            float(analysis_df["Estimated Business Loss"].mean()), 2
        )
        summary["max_business_loss"] = round(
            float(analysis_df["Estimated Business Loss"].max()), 2
        )

    # AI validation distribution
    ai_dist = {}
    if "AI Validation" in analysis_df.columns:
        ai_dist = analysis_df["AI Validation"].value_counts().to_dict()

    # Loss distribution for charts
    loss_distribution = {}
    if "Dominant Loss" in analysis_df.columns:
        loss_distribution = (
            analysis_df["Dominant Loss"].value_counts().to_dict()
        )

    return {
        "summary": summary,
        "records": records,
        "ai_stats": {
            "processed": pipe.analyzer.ai_processed_count,
            "skipped": pipe.analyzer.ai_skipped_count,
            "response_time": round(groq_time, 2),
        },
        "ai_distribution": ai_dist,
        "loss_distribution": loss_distribution,
        "query_context": {
            "description": request.query,
            "generated_sql": valid_sql
        },
    }
