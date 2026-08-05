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
import threading
import sqlite3
from typing import Optional

import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_FILE_PATH
from database.init_db import initialize_database
from database.database import Database
from database.repositories import ProductionRepository
from core.query_service import QueryService
from core.filter_service import FilterService
from core.validator import DataValidator
from core.oee_calculator import OEECalculator
from analysis.error_code_resolver import ErrorCodeResolver
from analysis.loss_analyzer import LossAnalyzer
from analysis.business_impact import BusinessImpactEngine

from rag.document_loader import DocumentLoader
from rag.text_chunker import TextChunker
from rag.embedding_service import EmbeddingService
from rag.vector_store import VectorStore
from rag.retriever import Retriever

# Copilot Imports
from copilot.memory import SessionMemory
from copilot.chat_service import CopilotChatService

from api.auth import router as auth_router, get_current_user

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

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])


# ── Request / Response Models ────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    query: Optional[str] = ""
    plant: Optional[str] = None
    line: Optional[str] = None
    machine: Optional[str] = None
    shift: Optional[str] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None


class ChatRequest(BaseModel):
    session_id: str
    message: str
    mode: str = "ask_anything" # "ask_anything", "recommendation", "simulation"
    analytics_context: Optional[dict] = None

class TicketCreate(BaseModel):
    date: str
    shift: str
    line: Optional[str] = "Unknown"
    machine_id: str
    ticket_status: Optional[str] = "Open"

class HealthResponse(BaseModel):
    status: str
    database: str
    machines_count: int


# ── Pipeline Singleton ───────────────────────────────────────────────

class Pipeline:
    """Singleton that initializes pipeline components once."""

    _instance: Optional["Pipeline"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        if not os.path.exists(DB_FILE_PATH):
            initialize_database()

        self.db = Database()
        self.repo = ProductionRepository(self.db)
        self.available_machines = self.repo.get_available_machines()
        self.query_service = QueryService()
        self.filter_service = FilterService(DB_FILE_PATH)
        self.validator = DataValidator()
        self.calculator = OEECalculator()
        self.resolver = ErrorCodeResolver()
        self.analyzer = LossAnalyzer()
        self.business_engine = BusinessImpactEngine()
        
        # RAG Initialization
        try:
            self.document_loader = DocumentLoader(os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge"))
            self.text_chunker = TextChunker()
            self.embedding_service = EmbeddingService()
            self.vector_store = VectorStore()
            self.retriever = Retriever(self.vector_store, self.embedding_service)
            
            # Auto-ingest if empty
            try:
                if self.vector_store.get_collection_count() == 0:
                    logger.info("ChromaDB is empty. Auto-ingesting documents...")
                    docs = self.document_loader.load_all_documents()
                    if docs:
                        chunks = self.text_chunker.chunk_documents(docs)
                        texts = [c["text"] for c in chunks]
                        embeddings = self.embedding_service.embed_texts(texts)
                        self.vector_store.add_documents(chunks, embeddings)
                        logger.info(f"Auto-ingestion complete. {len(texts)} vectors added.")
            except Exception as ingest_e:
                logger.error(f"Auto-ingestion failed during startup: {ingest_e}")
            
            # Copilot Initialization
            self.session_memory = SessionMemory()
            self.chat_service = CopilotChatService(self.retriever, self.session_memory)
        except Exception as e:
            logger.error(f"Failed to initialize RAG components: {e}")
            self.chat_service = None

    @classmethod
    def get(cls) -> "Pipeline":
        if cls._instance is None:
            with cls._lock:
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
def health_check(current_user: dict = Depends(get_current_user)) -> dict:
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


@app.get("/api/filters/plants")
def get_plants(current_user: dict = Depends(get_current_user)) -> dict:
    """Returns available plants."""
    pipe = Pipeline.get()
    return {"plants": pipe.repo.get_plants()}


@app.get("/api/filters/lines")
def get_lines(plant: Optional[str] = None, current_user: dict = Depends(get_current_user)) -> dict:
    """Returns available lines, optionally filtered by plant."""
    pipe = Pipeline.get()
    return {"lines": pipe.repo.get_lines(plant)}


@app.get("/api/filters/shifts")
def get_shifts(current_user: dict = Depends(get_current_user)) -> dict:
    """Returns available shifts."""
    pipe = Pipeline.get()
    return {"shifts": pipe.repo.get_available_shifts()}


@app.get("/api/machines")
def get_machines(line: Optional[str] = None, plant: Optional[str] = None, current_user: dict = Depends(get_current_user)) -> dict:
    """Returns available machine list, optionally filtered by line and/or plant."""
    pipe = Pipeline.get()
    return {"machines": pipe.repo.get_available_machines(line, plant)}

@app.post("/api/tickets")
def create_ticket(ticket: TicketCreate, current_user: dict = Depends(get_current_user)) -> dict:
    """Creates a new maintenance ticket."""
    pipe = Pipeline.get()
    try:
        with pipe.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Resolve actual line from machine_id
            resolved_line = ticket.line
            if not resolved_line or resolved_line == "Unknown":
                cursor.execute('''
                    SELECT l.line_name 
                    FROM dim_line l 
                    JOIN dim_machine m ON l.line_id = m.line_id 
                    WHERE m.machine_code = ?
                ''', (ticket.machine_id,))
                line_row = cursor.fetchone()
                if line_row:
                    resolved_line = line_row[0]
                    
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ticket (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    shift TEXT NOT NULL,
                    line TEXT NOT NULL,
                    machine_id TEXT NOT NULL,
                    ticket_status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, shift, machine_id)
                )
            ''')
            
            cursor.execute('''
                INSERT OR IGNORE INTO ticket (date, shift, line, machine_id, ticket_status)
                VALUES (?, ?, ?, ?, ?)
            ''', (ticket.date, ticket.shift, resolved_line, ticket.machine_id, ticket.ticket_status))
            conn.commit()
            return {"status": "success", "message": "Ticket raised successfully", "ticket_id": cursor.lastrowid}
    except Exception as e:
        logger.error(f"Failed to create ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tickets")
def get_tickets(current_user: dict = Depends(get_current_user)) -> dict:
    """Retrieves all tickets."""
    pipe = Pipeline.get()
    try:
        with pipe.db.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ticket ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return {"tickets": [dict(row) for row in rows]}
    except Exception as e:
        logger.error(f"Failed to fetch tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest, current_user: dict = Depends(get_current_user)) -> dict:
    """
    Runs the full analysis pipeline for a natural language query.

    Returns structured JSON with:
      - summary: KPI statistics
      - records: Full enriched record list
      - ai_stats: AI processing statistics
      - query_context: Parsed filter details
    """
    pipe = Pipeline.get()

    # 1. Routing: NL-to-SQL vs Explicit Filters
    try:
        if request.query and request.query.strip():
            logger.info("Routing to QueryService (NL-to-SQL)")
            raw_df, valid_sql = pipe.query_service.process_query(request.query)
        else:
            logger.info("Routing to FilterService (Explicit Filters)")
            raw_df, valid_sql = pipe.filter_service.process_filters(
                plant=request.plant,
                line=request.line,
                machine=request.machine,
                shift=request.shift,
                from_date=request.from_date,
                to_date=request.to_date
            )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process query/filters: {e}",
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

    # 7.5 Agentic Ticketing
    try:
        with pipe.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ticket (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    shift TEXT NOT NULL,
                    line TEXT NOT NULL,
                    machine_id TEXT NOT NULL,
                    ticket_status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, shift, machine_id)
                )
            ''')
            for _, row in analysis_df.iterrows():
                oee = row.get("OEE", 100)
                ai_val = str(row.get("AI Validation", ""))
                loss = row.get("Estimated Business Loss", 0)
                
                if pd.isna(oee): oee = 100
                if pd.isna(loss): loss = 0
                
                if oee < 50 or ai_val.strip() == "Mismatch" or loss > 1000:
                    cursor.execute('''
                        INSERT OR IGNORE INTO ticket (date, shift, line, machine_id, ticket_status)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        str(row.get("Date", "Unknown")),
                        str(row.get("Shift", "Unknown")),
                        str(row.get("Line", "Unknown")),
                        str(row.get("Machine ID", "Unknown")),
                        "Open (Auto-Generated)"
                    ))
            conn.commit()
    except Exception as e:
        logger.error(f"Agentic ticket generation failed: {e}")

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

# ── RAG Chat Endpoints ───────────────────────────────────────────────

@app.post("/api/chat/ingest")
def ingest_knowledge(current_user: dict = Depends(get_current_user)) -> dict:
    """Admin endpoint to ingest PDFs into ChromaDB."""
    pipe = Pipeline.get()
    if not pipe.chat_service:
        raise HTTPException(status_code=500, detail="RAG system failed to initialize.")
        
    try:
        docs = pipe.document_loader.load_all_documents()
        if not docs:
            return {"status": "success", "message": "No documents found to ingest.", "count": 0}
            
        chunks = pipe.text_chunker.chunk_documents(docs)
        texts = [c["text"] for c in chunks]
        embeddings = pipe.embedding_service.embed_texts(texts)
        
        pipe.vector_store.add_documents(chunks, embeddings)
        count = pipe.vector_store.get_collection_count()
        return {"status": "success", "message": "Ingestion complete", "total_vectors": count}
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/message")
def chat_message(request: ChatRequest, current_user: dict = Depends(get_current_user)) -> dict:
    """Main interaction endpoint for the AI Assistant."""
    pipe = Pipeline.get()
    if not pipe.chat_service:
        raise HTTPException(status_code=500, detail="RAG system is offline.")
        
    try:
        response = pipe.chat_service.process_message(
            session_id=request.session_id,
            message=request.message,
            mode=request.mode,
            analytics_context=request.analytics_context
        )
        return response
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
