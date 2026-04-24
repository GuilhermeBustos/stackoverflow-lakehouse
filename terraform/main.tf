resource "google_storage_bucket" "raw" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = true
}

resource "google_bigquery_dataset" "raw" {
  dataset_id = "stackoverflow_raw"
  location   = var.region
}

resource "google_bigquery_dataset" "trusted" {
  dataset_id = "stackoverflow_trusted"
  location   = var.region
}

resource "google_bigquery_dataset" "marts" {
  dataset_id = "stackoverflow_marts"
  location   = var.region
}