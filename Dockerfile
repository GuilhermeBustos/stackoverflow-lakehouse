FROM apache/airflow:3.2.1

RUN pip install --no-cache-dir \
    apache-airflow-providers-google==21.1.0 \
    dbt-bigquery==1.11.1