# 🇿🇦 South African Economic Reform Agenda (SA-ERA)

![Project Status](https://img.shields.io/badge/Status-Active_Analysis-success)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Data Source](https://img.shields.io/badge/Data-PMG.org.za-orange)
![License](https://img.shields.io/badge/License-MIT-green)

**A data-driven analysis of 10 years of South African economic policy recommendations (2015-2025).**

## 📖 Project Overview
This project digitizes and analyzes a decade of **Budgetary Review and Recommendation Reports (BRRR)** to track government performance, fiscal compliance, and policy implementation. By processing **5,256 specific recommendations** across 50 parliamentary reports, we identify actionable "Quick Wins" and structural reforms needed to unlock economic growth.

* **Analysis Date:** November 24, 2025
* **Scope:** 6 Priority Sectors (Energy, Labour, Finance, SciTech, Infrastructure, Trade)
* **Dataset:** 50 Full-Text Parliamentary Reports

---

## ⚡ Executive Summary: Key Findings

We identified **5,256 recommendations** and scored them using an algorithmic framework based on *Impact*, *Feasibility*, and *Cost*.

| Category | Count | Description |
| :--- | :---: | :--- |
| **🚀 Quick Wins** | **441** | High-impact, low-cost actions implementable immediately (<6 months). |
| **🔥 High Priority** | **2,060** | Critical reforms scoring highly across all dimensions. |
| **🏛️ Institutional** | **1,473** | Deep systemic changes requiring legislative or major structural reform. |

### 🔍 Top Recurring Themes (10-Year Trend)
1. **Compliance & Reporting** (857)
2. **Budget Execution** (616)
3. **Service Delivery** (559)
4. **Unemployment** (400)
5. **Procurement/Supply Chain** (248)

---

## 📂 Deliverables & Repository Structure

### 1. Policy Documents
* [📄 **Executive Summary**](analysis/Executive_Summary.md) – *Start here for top 20 priorities.*
* [📘 **Full Policy Memo**](analysis/SA_Economic_Reform_Agenda.md) – *Comprehensive 37-page analysis including implementation roadmaps.*

### 2. Data Files
* `analysis/recommendations_prioritized.xlsx` – **Master Dataset**. Includes ROI scores and filtering flags (`is_quick_win`).
* `analysis/recommendations.json` – Machine-readable format for developers.
* `analysis/report_summaries.xlsx` – Metadata for all 50 analyzed reports.

### 3. Source Reports
* `brrr_reports/` – PDF archive organized by sector (Energy, Finance, Labour, etc.).

---

## 📊 Methodology

Our analysis pipeline uses Python (`PyMuPDF`) to extract text and a custom scoring algorithm to prioritize recommendations.

### The ROI Scoring Framework
Each recommendation is scored on three dimensions to calculate a final **ROI Score (1-10)**:

1.  **Feasibility (1-5):** From "Major Investment" (1) to "Administrative Action" (5).
2.  **Impact (1-5):** Based on sector importance and economic significance (e.g., Energy > Admin).
3.  **Cost (1-5):** From ">R1bn" (1) to "<R1m" (5).

> **Formula:** $ROI = \frac{Impact \times Feasibility}{Cost}$ (Normalized)

---

## 🚀 Usage Guide

### For Researchers & Developers
Reproduce the analysis by running the pipeline scripts in order:

```bash
# 1. Install Dependencies
pip install -r requirements.txt

# 2. Download latest BRRR reports from PMG
python scripts/download_brrr_direct.py

# 3. Extract text and identify recommendations
python scripts/analyze_brrr_reports.py

# 4. Run the scoring and prioritization algorithm
python scripts/prioritize_recommendations.py

# 5. Generate the Policy Memo Markdown files
python scripts/generate_policy_memo.py
