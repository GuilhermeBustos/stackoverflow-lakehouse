# Stack Overflow Lakehouse

End-to-end batch data engineering pipeline built on GCP, developed as the capstone project for the [DataTalksClub Data Engineering Zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp).

## What is being built

A medallion lakehouse pipeline that extracts Stack Overflow data from BigQuery public datasets, processes it through GCS and BigQuery, transforms it with dbt, and visualizes it in Looker Studio.

## Architecture

```
BigQuery Public Data  (bigquery-public-data.stackoverflow)
        │
        │  Airflow — BigQueryToGCSOperator
        ▼
  GCS Raw Bucket      (Parquet, partitioned by year/month)
        │
        │  Airflow — GCSToBigQueryOperator
        ▼
BigQuery Raw Dataset  (stackoverflow_raw)
        │
        │  Airflow — dbt run
        ▼
BigQuery Trusted      (stackoverflow_trusted)  ← dbt staging models
        │
        ▼
BigQuery Marts        (stackoverflow_marts)    ← dbt mart models
        │
        ▼
  Looker Studio Dashboard
```

## Tech Stack

| Layer | Tool |
|---|---|
| Cloud | GCP |
| Infrastructure | Terraform |
| Orchestration | Apache Airflow (Docker) |
| Storage | Google Cloud Storage |
| Data Warehouse | BigQuery |
| Transformation | dbt |
| Dashboard | Looker Studio |

## Dataset

[Stack Overflow — BigQuery Public Data](https://console.cloud.google.com/marketplace/product/stack-exchange/stack-overflow)

Tables used: `posts_questions`, `posts_answers`, `users`, `tags`, `votes`

## Repository Structure

```
├── airflow/
│   ├── dags/              # Airflow DAG definitions
│   └── docker-compose.yaml
├── dbt/
│   ├── models/
│   │   ├── staging/       # Trusted layer — cleaning and standardization
│   │   └── marts/         # Aggregated layer — analytics-ready tables
│   ├── tests/
│   └── dbt_project.yml
├── terraform/
│   ├── main.tf            # GCS bucket + BigQuery datasets
│   ├── variables.tf
│   └── outputs.tf
├── .env.example           # Required environment variables (no values)
└── README.md
```

## Prerequisites

- GCP account with billing enabled
- [Terraform](https://developer.hashicorp.com/terraform/install)
- [Docker & Docker Compose](https://docs.docker.com/get-docker/)
- [dbt CLI](https://docs.getdbt.com/docs/core/installation)
- GCP service account with `BigQuery Admin` and `Storage Admin` roles

## Setup

> Full setup instructions will be added as the project progresses.

1. Clone this repository
2. Copy `.env.example` to `.env` and fill in your values
3. Apply Terraform to provision GCP resources
4. Start Airflow with Docker Compose
5. Trigger the ingestion DAGs
6. Run dbt models
7. Connect Looker Studio to the `stackoverflow_marts` dataset

## Dashboard

> Link will be added after deployment.
