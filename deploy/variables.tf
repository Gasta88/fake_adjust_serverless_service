variable "project_id" {
  description = "GCP project that hosts the Cloud Functions, Scheduler jobs and GCS buckets."
  type        = string
  default     = "eighth-duality-457819-r4"
}

variable "region" {
  description = "Region used by the Google provider."
  type        = string
  default     = "us-central1"
}

variable "service_account_email" {
  description = "Service account used by Cloud Scheduler to mint OIDC tokens for the orchestrator."
  type        = string
  default     = "874544665874-compute@developer.gserviceaccount.com"
}

variable "fass_api_url" {
  description = "Base URL of the stage-1 Fake Adjust API (deployed from Gasta88/fake_adjust)."
  type        = string
  default     = "https://fass-api-874544665874.us-central1.run.app/reporting"
}

variable "bq_project" {
  description = "Project that owns the production BigQuery dataset."
  type        = string
  default     = "bondola-ai"
}

variable "bq_dataset" {
  description = "BigQuery dataset that receives the raw and lookup tables."
  type        = string
  default     = "analytics"
}
