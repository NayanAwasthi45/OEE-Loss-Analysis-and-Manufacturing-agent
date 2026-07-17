# Business Impact Engine Documentation

This document outlines the formulas, logic, and configurations used by the Business Impact Engine (Phase B) to translate operational OEE metrics into financial loss and priority rankings.

## 1. Configurable Assumptions
The financial calculations rely on three key configurable variables stored in `business_config.json`. These values can be updated at any time without code changes:

- **`downtime_cost_per_minute`**: The estimated overhead cost (labor, fixed operational expenses) wasted per minute of unplanned downtime.
- **`scrap_cost_per_part`**: The estimated cost of material and labor wasted for every defective part produced.
- **`production_value_per_part`**: The estimated missed revenue or margin for every unit of expected production that was not completed.

---

## 2. Operational Formulas

The engine first calculates the theoretical maximums to determine units lost.

### Expected Production
The total number of units that *should* have been produced during the full planned shift if the machine ran at its ideal cycle time.
> **Formula:** `Expected Production = Planned Time (min) / Ideal Cycle Time (min/unit)`

### Production Loss (units)
The absolute number of units lost against the shift's total theoretical capacity.
> **Formula:** `Production Loss (units) = Expected Production - Total Parts Produced`

### Throughput Loss (units)
The number of units lost specifically due to micro-stoppages or speed reductions while the machine was actively operating. This isolates Performance Loss from Availability Loss.
> **Formula:** `Throughput Loss (units) = (Operating Time (min) / Ideal Cycle Time) - Total Parts Produced`

---

## 3. Financial Formulas

The engine converts time and unit losses into financial impact.

### Downtime Cost
> **Formula:** `Downtime (min) × downtime_cost_per_minute`

### Scrap Cost
> **Formula:** `Defective Parts × scrap_cost_per_part`

### Production Loss Cost
> **Formula:** `Production Loss (units) × production_value_per_part`

### Estimated Business Loss
The total aggregated financial impact of the production record.
> **Formula:** `Downtime Cost + Scrap Cost + Production Loss Cost`

### Primary Business Driver
Identifies which of the three cost categories (Downtime, Scrap, or Production Loss) contributes the largest amount to the Estimated Business Loss.

### Business Loss Breakdown
A transparent string representation of the total loss, formatted as:
`Downtime (₹X) + Scrap (₹Y) + Prod. Loss (₹Z)`

---

## 4. Priority Scoring Model

To help plant managers prioritize which issues to tackle first, the engine calculates a **Priority Score (0 to 100)** using a weighted multifactor model.

### Weighting Breakdown
1. **OEE (30%)**: Inversely proportional. A lower OEE yields a higher score.
   - `Score Component = ((100 - OEE) / 100) × 30`
2. **Business Loss (40%)**: Normalized against the highest business loss in the current dataset.
   - `Score Component = (Estimated Business Loss / Max Dataset Loss) × 40`
3. **Downtime (20%)**: Normalized against the highest downtime in the current dataset.
   - `Score Component = (Downtime / Max Dataset Downtime) × 20`
4. **Severity (10%)**: Based on the expected severity of the error code category.
   - **Critical (10 points)**: `DT-01` (Breakdown)
   - **High (8 points)**: `DT-02`, `DT-03` (Electrical / Changeover)
   - **Medium (6 points)**: `DT-05`, `DT-06`, `DT-07` (Speed / Quality drops)
   - **Low (4 points)**: `DT-04` (Small Stops)
   - **None (0 points)**: `DT-00` (Healthy)

### Priority Levels
The total 0-100 score is then categorized into actionable Priority Levels:
- **Critical**: Score ≥ 80
- **High**: Score ≥ 60
- **Medium**: Score ≥ 40
- **Low**: Score < 40

### Top Loss Driver Rank
A dense ranking (1, 2, 3...) applied to the dataset based on the `Estimated Business Loss` in descending order. The record with the highest financial loss is ranked #1.
