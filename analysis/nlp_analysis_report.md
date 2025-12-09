# NLP Analysis of BRRR Recommendations

## Executive Summary

This analysis applies Natural Language Processing techniques to 5,256 
Budget Review and Recommendations Report (BRRR) submissions to identify:
- **Sentiment patterns** - Are recommendations expressing concerns or progress?
- **Urgency levels** - Which issues require immediate attention?
- **Policy themes** - What topics are most frequently addressed?
- **High concern areas** - Where do urgency and negative sentiment intersect?

---

## Sentiment Analysis

### Overall Distribution

| Sentiment | Count | Percentage |
|-----------|-------|------------|
| Neutral | 3,137 | 59.7% |
| Positive | 1,590 | 30.3% |
| Negative | 529 | 10.1% |

**Average Sentiment Score:** 0.182 
*(Scale: -1 = very negative, 0 = neutral, +1 = very positive)*

### Urgency Distribution

| Urgency Level | Count | Percentage |
|---------------|-------|------------|
| Low | 4,774 | 90.8% |
| Medium | 427 | 8.1% |
| High | 55 | 1.0% |

---

## Policy Theme Analysis

Recommendations were analyzed for mentions of key policy themes:

| Theme | Mentions | % of Recommendations |
|-------|----------|---------------------|
| Service Delivery | 1,216 | 23.1% |
| Fiscal | 1,116 | 21.2% |
| Governance | 888 | 16.9% |
| Economic | 851 | 16.2% |
| Human Resources | 789 | 15.0% |
| Financial Management | 774 | 14.7% |
| Social | 460 | 8.8% |
| Soe | 357 | 6.8% |

---

## High Concern Areas

Recommendations flagged as **both high urgency AND negative sentiment**: **2**

These represent the most pressing issues identified in committee deliberations.

### Top Departments with Concerns

| Department | High Concern Count |
|------------|-------------------|
| labour | 2 |

---

## Monetary References

- Recommendations mentioning specific amounts: **1,033**
- Total value referenced: **R152340.98 billion**

---

## Methodology

### Sentiment Analysis
- **Positive indicators**: improve, enhance, progress, success, effective, etc.
- **Negative indicators**: concern, fail, inadequate, irregular, wasteful, etc.
- **Urgency indicators**: urgent, immediate, critical, must, imperative, etc.

### Entity Extraction
Key terms grouped into policy themes:
- **Fiscal**: budget, expenditure, revenue, deficit, appropriation
- **Governance**: accountability, transparency, audit, compliance
- **Service Delivery**: infrastructure, maintenance, performance, targets
- **Human Resources**: vacancy, staff, recruitment, capacity building
- **Financial Management**: procurement, supply chain, contracts
- **SOE**: state-owned enterprises, Eskom, Transnet, etc.
- **Social**: poverty, inequality, health, education, housing
- **Economic**: GDP, growth, investment, trade, productivity

---

*Generated using NLP analysis of BRRR recommendations data*
