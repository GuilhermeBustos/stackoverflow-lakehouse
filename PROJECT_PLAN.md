# Project Plan: Stack Overflow Data Engineering Pipeline

## Overview

End-to-end data engineering pipeline built on GCP using a medallion lakehouse architecture. Raw Stack Overflow data is extracted from BigQuery public datasets, landed in GCS, transformed through dbt into trusted and aggregated layers in BigQuery, orchestrated with Airflow, and visualized in Looker Studio.

**Dataset:** [Stack Overflow — BigQuery Public Data](https://console.cloud.google.com/marketplace/product/stack-exchange/stack-overflow)

**Architecture:**

```
BigQuery Public Data
        ↓ (Airflow — BigQueryToGCSOperator)
    GCS Raw Bucket
        ↓ (Airflow — GCSToBigQueryOperator)
  BigQuery Raw Dataset
        ↓ (Airflow — dbt run)
BigQuery Trusted Dataset  ←  dbt Staging Models
        ↓
 BigQuery Marts Dataset  ←  dbt Mart Models
        ↓
   Looker Studio Dashboard
```

**Tech Stack:**
| Layer | Tool |
|---|---|
| Cloud | GCP |
| Infrastructure | Terraform |
| Orchestration | Apache Airflow (Docker) |
| Storage | Google Cloud Storage |
| Data Warehouse | BigQuery |
| Transformation | dbt |
| Dashboard | Looker Studio |

---

## Phase 1 — Repository & Project Setup

- [ ] **1.** Create a new GitHub repository with the following structure:

```
├── airflow/
│   ├── dags/
│   └── docker-compose.yaml
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   └── marts/
│   ├── tests/
│   └── dbt_project.yml
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── .env.example
├── .gitignore
└── README.md
```

- [ ] **2.** Configure `.gitignore` to exclude credentials, `.env`, `__pycache__`, dbt target directories, and Terraform state files
- [ ] **3.** Create `.env.example` documenting all required environment variables without values

---

## Phase 2 — GCP Infrastructure with Terraform

- [ ] **4.** Create a GCP project and a service account with the following roles:
  - `BigQuery Admin`
  - `Storage Admin`

- [ ] **5.** Write Terraform to provision:
  - **GCS bucket** — raw data landing zone (`stackoverflow-raw-<project-id>`)
  - **BigQuery dataset** — `stackoverflow_raw`
  - **BigQuery dataset** — `stackoverflow_trusted`
  - **BigQuery dataset** — `stackoverflow_marts`

- [ ] **6.** Apply Terraform and validate all resources are created in the GCP console

---

## Phase 3 — Data Ingestion Design

- [ ] **7.** Identify which Stack Overflow tables to extract from `bigquery-public-data.stackoverflow`:
  - `posts_questions` — question activity over time
  - `posts_answers` — answer metrics
  - `users` — user profiles and reputation
  - `tags` — technology tag usage
  - `votes` — voting patterns

- [ ] **8.** Design the extraction strategy: query BigQuery public data → export results to GCS as Parquet files, partitioned by year/month where applicable

- [ ] **9.** Define GCS naming convention for raw files:

```
gs://stackoverflow-raw/
  posts_questions/year=2024/month=01/data.parquet
  users/snapshot_date=2024-01-01/data.parquet
```

---

## Phase 4 — Airflow Setup & DAGs

- [ ] **10.** Set up Airflow locally using Docker Compose with the following providers:
  - `apache-airflow-providers-google` (BigQuery + GCS operators)
  - dbt CLI invocation via `BashOperator`

- [ ] **11.** Write DAGs using `BigQueryToGCSOperator` to extract from the public dataset and land data in the raw GCS bucket

- [ ] **12.** Write DAGs using `GCSToBigQueryOperator` to load raw Parquet files from GCS into the `stackoverflow_raw` BigQuery dataset

- [ ] **13.** Add a final DAG step that triggers dbt runs via `BashOperator`

- [ ] **14.** Schedule DAGs appropriately — Stack Overflow public data is updated periodically, so a weekly or monthly schedule is sufficient

---

## Phase 5 — dbt Trusted Layer (Staging Models)

- [ ] **15.** Initialize the dbt project inside the `dbt/` directory, configured to target the `stackoverflow_trusted` BigQuery dataset

- [ ] **16.** Create staging models for each raw table applying:
  - Column renaming to `snake_case` consistency
  - Type casting (timestamps, integers)
  - Null handling for optional fields
  - Deduplication where applicable

- [ ] **17.** Configure BigQuery-specific optimizations on staging models:
  - **Partition** `stg_posts_questions` by `creation_date`
  - **Cluster** by `tags` or `score`
  - Use `incremental` materialization for large tables

- [ ] **18.** Add dbt schema tests on staging models:
  - `not_null` on primary key columns (`id`)
  - `unique` on primary key columns
  - `accepted_values` on fields like `post_type_id`
  - `relationships` between questions and answers via `parent_id`

---

## Phase 6 — dbt Marts Layer (Aggregated Models)

- [ ] **19.** Create mart models targeting the `stackoverflow_marts` dataset:
  - **Technology trends** — monthly question count per tag (temporal + categorical)
  - **User engagement** — top users by reputation, answer rate, acceptance rate
  - **Question quality** — average score and answer count per tag per year
  - **Answer performance** — time to first answer by category

- [ ] **20.** Materialize all mart models as BigQuery **tables** (not views) for Looker Studio performance

- [ ] **21.** Add dbt data tests on mart models:
  - Validate aggregated counts are non-negative
  - Ensure no future dates in temporal columns
  - Check referential integrity between marts

---

## Phase 7 — Looker Studio Dashboard

- [ ] **22.** Connect Looker Studio directly to the `stackoverflow_marts` BigQuery dataset

- [ ] **23.** Build a dashboard with at minimum:
  - **Temporal chart** — question volume over time per top 10 tags (line chart)
  - **Categorical chart** — top technologies by total questions or average score (bar chart)

- [ ] **24.** Add filters for date range and tag selection to make the dashboard interactive

---

## Phase 8 — Documentation & Reproducibility

- [ ] **25.** Write a comprehensive `README.md` covering:
  - Project architecture diagram
  - Prerequisites (GCP account, Terraform, Docker, dbt)
  - Step-by-step setup instructions
  - How to run Terraform, start Airflow, trigger DAGs, and run dbt
  - Looker Studio dashboard link

- [ ] **26.** Validate full reproducibility from a clean environment before submission

---

## Execution Order

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 7 → Phase 8
                                                ↕
                                            Phase 6
```

> Phases 5 and 6 can be developed in parallel once raw data is flowing into BigQuery from Phase 4.

---

## Notes

- Never commit service account keys or `.env` files — use `.env.example` to document required variables
- The most common peer review failures are missing dependencies and hardcoded paths — validate reproducibility before submission
- dbt tests on both staging and mart layers demonstrate data quality awareness to reviewers
