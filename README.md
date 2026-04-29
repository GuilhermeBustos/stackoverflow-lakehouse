# Stack Overflow Analytics Pipeline

End-to-end batch ELT pipeline that ingests Stack Overflow public data from BigQuery, lands it in Google Cloud Storage as Parquet, loads it into a BigQuery warehouse, and transforms it through a medallion-style layering (raw → trusted → marts) using dbt. Built as the capstone project for the [DataTalksClub Data Engineering Zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp).

## Problem

Stack Overflow's public dataset offers ~15 years of question, answer, user and tag activity — a rich substrate for understanding technology adoption trends, community engagement patterns, and answer-quality dynamics. The raw tables are large, denormalized, and inconvenient to query directly for analytics. This pipeline turns them into a partitioned, clustered, analytics-ready warehouse layered for BI consumption.

## Architecture

A medallion-style batch ELT pipeline on GCP. GCS is used as a _staging zone_ (Parquet landing area) — BigQuery is the system of record. This is a **warehouse-centric** architecture, not a lakehouse: the `raw` dataset is a managed BigQuery dataset, not external/BigLake tables over GCS.

```
┌─────────────────────────────────────┐
│  bigquery-public-data.stackoverflow │
└────────────────┬────────────────────┘
                 │  Airflow — BigQueryInsertJob (EXPORT DATA) / BigQueryToGCSOperator
                 ▼
┌─────────────────────────────────────┐
│  GCS bucket — Parquet staging       │
│  posts_*/year=YYYY/                 │
│  users|tags/snapshot_date=YYYY-MM-DD│
└────────────────┬────────────────────┘
                 │  Airflow — BigQueryInsertJob load / GCSToBigQueryOperator
                 ▼
┌─────────────────────────────────────┐
│  BigQuery — raw      (stackoverflow_raw)      │  ← native managed tables
└────────────────┬────────────────────┘
                 │  Airflow — dbt run --select staging
                 ▼
┌─────────────────────────────────────┐
│  BigQuery — trusted  (stackoverflow_trusted)  │  ← partitioned + clustered
└────────────────┬────────────────────┘
                 │  dbt run --select marts  (planned)
                 ▼
┌─────────────────────────────────────┐
│  BigQuery — marts    (stackoverflow_marts)    │  dataset provisioned; models pending
└────────────────┬────────────────────┘
                 │
                 ▼
          Looker Studio  (planned)
```

## Tech stack

| Layer           | Tool                                |
| --------------- | ----------------------------------- |
| Cloud           | GCP                                 |
| Infrastructure  | Terraform                           |
| Orchestration   | Apache Airflow 3.2 (Docker Compose) |
| Staging storage | Google Cloud Storage (Parquet)      |
| Data warehouse  | BigQuery                            |
| Transformation  | dbt (`dbt-bigquery`)                |
| Dashboard       | Looker Studio _(planned)_           |

## Status

| Area                                                                                                | Status     |
| --------------------------------------------------------------------------------------------------- | ---------- |
| GCP infrastructure (GCS bucket, 3 BigQuery datasets) via Terraform                                  | ✅ Done    |
| Airflow stack (Docker Compose, scheduler, API server, dag-processor, triggerer, Postgres metastore) | ✅ Done    |
| Ingestion DAG: BQ public → GCS → BQ raw, monthly schedule, mapped tasks per year                    | ✅ Done    |
| dbt staging layer: `posts_questions`, `posts_answers`, `users`, `tags` (partitioned + clustered)    | ✅ Done    |
| dbt marts layer (technology trends, user engagement, question quality, answer performance)          | 🚧 Pending |
| dbt tests (schema + data quality)                                                                   | 🚧 Pending |
| Looker Studio dashboard                                                                             | 🚧 Pending |

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the full phase-by-phase plan.

## Dataset

[Stack Overflow — BigQuery Public Data](https://console.cloud.google.com/marketplace/product/stack-exchange/stack-overflow)

Tables currently ingested: `posts_questions`, `posts_answers`, `users`, `tags`.

`posts_questions` and `posts_answers` are exported per year (2008–2022) using `EXPORT DATA` to keep file sizes manageable and enable mapped Airflow tasks. `users` and `tags` are exported as full snapshots keyed by `ds`.

## Repository structure

```
.
├── airflow/
│   └── dags/
│       └── stackoverflow_pipeline.py    # extract → load → transform DAG
├── dbt/
│   ├── profiles.yml                      # dbt-bigquery profile (env-var driven)
│   └── stackoverflow/
│       ├── dbt_project.yml
│       ├── packages.yml                  # dbt-labs/codegen
│       └── models/
│           └── staging/
│               ├── _stackoverflow__sources.yml
│               ├── stg_stackoverflow__posts_questions.sql
│               ├── stg_stackoverflow__posts_answers.sql
│               ├── stg_stackoverflow__users.sql
│               └── stg_stackoverflow__tags.sql
├── terraform/
│   ├── main.tf                           # GCS bucket + 3 BQ datasets
│   ├── variables.tf
│   ├── outputs.tf
│   └── providers.tf
├── credentials/                          # service-account JSON (gitignored)
├── docker-compose.yaml                   # Airflow stack
├── Dockerfile                            # apache/airflow:3.2.1 + google provider + dbt-bigquery
├── .env.example
└── PROJECT_PLAN.md
```

## BigQuery layout & optimization

Staging models are materialized as **tables** (not views) so downstream marts and Looker Studio benefit from columnar storage and pruning.

| Model                                | Partition (monthly) | Cluster                            |
| ------------------------------------ | ------------------- | ---------------------------------- |
| `stg_stackoverflow__posts_questions` | `creation_date`     | `owner_user_id`, `id`              |
| `stg_stackoverflow__posts_answers`   | `creation_date`     | `parent_id`, `owner_user_id`, `id` |
| `stg_stackoverflow__users`           | `creation_date`     | `id`                               |
| `stg_stackoverflow__tags`            | —                   | —                                  |

**Why these choices:** all analytical queries filter on time, so monthly partitioning on `creation_date` minimizes scanned bytes. Clustering on `owner_user_id` / `id` accelerates user-level joins (questions ↔ answers ↔ users) and primary-key lookups; clustering `posts_answers` additionally on `parent_id` accelerates the question-to-answer join, which is the most frequent join in the planned marts.

## Prerequisites

- GCP account with billing enabled
- A GCP project (note the project ID)
- A service account with roles `BigQuery Admin` and `Storage Admin`, plus a downloaded JSON key
- [Terraform](https://developer.hashicorp.com/terraform/install) ≥ 1.5
- [Docker & Docker Compose](https://docs.docker.com/get-docker/)

> dbt is **not** required locally — it runs inside the Airflow container (see [Dockerfile](Dockerfile)).

## Setup

### 1. Clone and configure

```bash
git clone <this-repo-url>
cd stackoverflow-analytics-warehouse
cp .env.example .env
```

Edit `.env` and fill in the values. See [Environment variables](#environment-variables) below.

Place your service-account key at `credentials/terraform-runner-service-account.json` (the path expected by [docker-compose.yaml](docker-compose.yaml)). The `credentials/` directory is gitignored.

### 2. Provision GCP infrastructure

```bash
cd terraform
terraform init
terraform plan -var "project_id=$GCP_PROJECT_ID" \
               -var "region=$GCP_REGION" \
               -var "bucket_name=$GCS_RAW_BUCKET"
terraform apply -var "project_id=$GCP_PROJECT_ID" \
                -var "region=$GCP_REGION" \
                -var "bucket_name=$GCS_RAW_BUCKET"
cd ..
```

This creates:

- `google_storage_bucket.raw` — Parquet staging bucket (`force_destroy = true`, uniform bucket-level access)
- Three BigQuery datasets: `stackoverflow_raw`, `stackoverflow_trusted`, `stackoverflow_marts`

### 3. Start the Airflow stack

```bash
docker compose up -d
```

The image is built from [Dockerfile](Dockerfile) (`apache/airflow:3.2.1` + `apache-airflow-providers-google` + `dbt-bigquery`).

The Airflow UI is at `http://localhost:8080`. Sign in with the user defined in `_AIRFLOW_WWW_USER_USERNAME` (SimpleAuthManager — see Airflow logs for the auto-generated password on first start).

### 4. Run the pipeline

In the Airflow UI, unpause the `stackoverflow` DAG and trigger it. It runs three task groups in order:

1. **`extract_to_gcs`** — exports each table to GCS as Parquet. `posts_questions` and `posts_answers` are mapped per year (2008–2022).
2. **`load_to_bigquery`** — loads the Parquet files into `stackoverflow_raw` (`WRITE_TRUNCATE`).
3. **`transform`** — runs `dbt run --select staging`, then `dbt run --select marts` (the latter is a no-op until marts models are added).

## Environment variables

Required (no defaults):

| Variable                         | Description                                                                                                      |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `GCP_PROJECT_ID`                 | GCP project ID                                                                                                   |
| `GCP_REGION`                     | GCP region (e.g. `us-central1`) — must match the BigQuery dataset location                                       |
| `GCS_RAW_BUCKET`                 | Name of the Parquet staging bucket                                                                               |
| `BQ_RAW_DATASET`                 | Defaults to `stackoverflow_raw`                                                                                  |
| `BQ_TRUSTED_DATASET`             | Defaults to `stackoverflow_trusted`                                                                              |
| `BQ_MARTS_DATASET`               | Defaults to `stackoverflow_marts`                                                                                |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path inside the Airflow container (`/opt/airflow/credentials/terraform-runner-service-account.json`)             |
| `AIRFLOW_UID`                    | Host user ID (`id -u`) — prevents root-owned files in mounted volumes                                            |
| `CREDENTIALS_PATH`               | Host path to the directory containing the service-account JSON                                                   |
| `FERNET_KEY`                     | Airflow Fernet key (`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`) |
| `_AIRFLOW_WWW_USER_USERNAME`     | Admin username for the Airflow UI                                                                                |

Optional (have defaults in [docker-compose.yaml](docker-compose.yaml)):

| Variable                        | Default              |
| ------------------------------- | -------------------- |
| `AIRFLOW__API_AUTH__JWT_SECRET` | `airflow_jwt_secret` |
| `AIRFLOW__API_AUTH__JWT_ISSUER` | `airflow`            |
| `ENV_FILE_PATH`                 | `.env`               |
| `AIRFLOW_PROJ_DIR`              | `.`                  |

## Dashboard

> Link and screenshot will be added once the marts layer and Looker Studio dashboard are built.
