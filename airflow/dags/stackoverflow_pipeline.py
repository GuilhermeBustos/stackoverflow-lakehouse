from airflow.decorators import dag
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.transfers.bigquery_to_gcs import (
    BigQueryToGCSOperator,
)
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import (
    GCSToBigQueryOperator,
)
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import TaskGroup
import pendulum
import os

GCP_CONN_ID = "google_cloud_default"
BQ_PROJECT = os.environ.get("GCP_PROJECT_ID")
GCP_BUCKET = os.environ.get("GCS_RAW_BUCKET")
RAW_DATASET = os.environ.get("BQ_RAW_DATASET")
YEARS = list(range(2008, 2026))


@dag(
    dag_id="stackoverflow",
    schedule="@monthly",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    max_active_tasks=8,
    tags=["stackoverflow"],
)
def stackoverflow_pipeline():

    def build_export_config(table, year):
        return {
            "query": {
                "query": f"""
                    EXPORT DATA OPTIONS (
                        uri='gs://{GCP_BUCKET}/{table}/year={year}/*.parquet',
                        format='PARQUET',
                        overwrite=true
                    ) AS
                    SELECT
                        *
                    FROM `bigquery-public-data.stackoverflow.{table}`
                    WHERE EXTRACT(YEAR FROM creation_date) = {year}
            """,
                "useLegacySql": False,
            }
        }

    with TaskGroup("extract_to_gcs") as extract:
        export_questions = BigQueryInsertJobOperator.partial(
            task_id="export_posts_questions",
            gcp_conn_id=GCP_CONN_ID,
            project_id=BQ_PROJECT,
            location="US",
        ).expand(
            configuration=[
                build_export_config("posts_questions", year) for year in YEARS
            ]
        )

        export_answers = BigQueryInsertJobOperator.partial(
            task_id="export_posts_answers",
            gcp_conn_id=GCP_CONN_ID,
            project_id=BQ_PROJECT,
            location="US",
        ).expand(
            configuration=[build_export_config("posts_answers", year) for year in YEARS]
        )

        export_users = BigQueryToGCSOperator(
            task_id="export_users",
            source_project_dataset_table="bigquery-public-data.stackoverflow.users",
            destination_cloud_storage_uris=[
                f"gs://{GCP_BUCKET}/users/snapshot_date={{{{ ds }}}}/data.parquet"
            ],
            export_format="PARQUET",
            gcp_conn_id=GCP_CONN_ID,
        )

        export_tags = BigQueryToGCSOperator(
            task_id="export_tags",
            source_project_dataset_table="bigquery-public-data.stackoverflow.tags",
            destination_cloud_storage_uris=[
                f"gs://{GCP_BUCKET}/tags/snapshot_date={{{{ ds }}}}/data.parquet"
            ],
            export_format="PARQUET",
            gcp_conn_id=GCP_CONN_ID,
        )

    with TaskGroup("load_to_bigquery") as load:
        load_questions = GCSToBigQueryOperator(
            task_id="load_posts_questions",
            bucket=GCP_BUCKET,
            source_objects=["posts_questions/year=*/*.parquet"],
            destination_project_dataset_table=f"{BQ_PROJECT}.{RAW_DATASET}.posts_questions",
            source_format="PARQUET",
            write_disposition="WRITE_TRUNCATE",
            autodetect=True,
            location="US",
            project_id=BQ_PROJECT,
            gcp_conn_id=GCP_CONN_ID,
        )

        load_answers = GCSToBigQueryOperator(
            task_id="load_posts_answers",
            bucket=GCP_BUCKET,
            source_objects=["posts_answers/year=*/*.parquet"],
            destination_project_dataset_table=f"{BQ_PROJECT}.{RAW_DATASET}.posts_answers",
            source_format="PARQUET",
            write_disposition="WRITE_TRUNCATE",
            autodetect=True,
            location="US",
            project_id=BQ_PROJECT,
            gcp_conn_id=GCP_CONN_ID,
        )

        load_users = GCSToBigQueryOperator(
            task_id="load_users",
            bucket=GCP_BUCKET,
            source_objects=["users/snapshot_date={{ ds }}/data.parquet"],
            destination_project_dataset_table=f"{BQ_PROJECT}.{RAW_DATASET}.users",
            source_format="PARQUET",
            write_disposition="WRITE_TRUNCATE",
            autodetect=True,
            location="US",
            project_id=BQ_PROJECT,
            gcp_conn_id=GCP_CONN_ID,
        )

        load_tags = GCSToBigQueryOperator(
            task_id="load_tags",
            bucket=GCP_BUCKET,
            source_objects=["tags/snapshot_date={{ ds }}/data.parquet"],
            destination_project_dataset_table=f"{BQ_PROJECT}.{RAW_DATASET}.tags",
            source_format="PARQUET",
            write_disposition="WRITE_TRUNCATE",
            autodetect=True,
            location="US",
            project_id=BQ_PROJECT,
            gcp_conn_id=GCP_CONN_ID,
        )

    with TaskGroup("transform") as transform:
        dbt_staging = BashOperator(
            task_id="dbt_run_staging",
            bash_command="cd /opt/airflow/dbt && dbt run --select staging",
        )

        dbt_mart = BashOperator(
            task_id="dbt_run_mart",
            bash_command="cd /opt/airflow/dbt && dbt run --select mart",
        )

        dbt_staging >> dbt_mart

    extract >> load >> transform


dag = stackoverflow_pipeline()
