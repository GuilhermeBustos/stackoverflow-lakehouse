output "raw_bucket_url" {
  value = google_storage_bucket.raw.url
}

output "raw_dataset_id" {
  value = google_bigquery_dataset.raw.dataset_id
}

output "trusted_dataset_id" {
  value = google_bigquery_dataset.trusted.dataset_id
}

output "marts_dataset_id" {
  value = google_bigquery_dataset.marts.dataset_id
}