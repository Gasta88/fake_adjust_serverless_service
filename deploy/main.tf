provider "google" {
  region = "us-central1"
  project = "justplay-data"
}

terraform {
  required_version = ">= 0.14"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
  backend "gcs" {}
}

#--------------------------- Cloud Storage

resource "google_storage_bucket" "gcf-storage" {
  name     = "fass-${terraform.workspace}"
  location = "us-central1"
  lifecycle {
    prevent_destroy = false
  }
  force_destroy = true
  public_access_prevention = "enforced"
}   

data "archive_file" "orchestrator" {
  type        = "zip"
  source_dir  = "../orchestrator_func"
  output_path = "../orchestrator.zip"
  excludes = ["test"]
}

data "archive_file" "executor" {
  type        = "zip"
  source_dir  = "../executor_func"
  output_path = "../executor.zip"
  excludes = ["test"]
}


resource "google_storage_bucket_object" "orchestrator-archive" {
  name   = "script/orchestrator.zip"
  bucket = google_storage_bucket.gcf-storage.name
  source = "../orchestrator.zip"
  depends_on = [ data.archive_file.orchestrator ]
}

resource "google_storage_bucket_object" "executor-archive" {
  name   = "script/executor.zip"
  bucket = google_storage_bucket.gcf-storage.name
  source = "../executor.zip"
  depends_on = [ data.archive_file.executor ]
}


#--------------------------- Cloud Schedulers

resource "google_cloud_scheduler_job" "every-2-hours" {
  paused           = false
  name             = "fass-2h-trigger-${terraform.workspace}"
  description      = "Trigger Fake Adjust Serverless Service every 2 hours"
  schedule         = "0 5,7,9,11,13,15,17,19,21 * * *"
  time_zone        = "Europe/Berlin"
  attempt_deadline = "1200s"

  retry_config {
    retry_count = 0
  }

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions2_function.orchestrator-function.url
    body        = base64encode("{\"scheduler_id\":\"2h\"}")
    headers = {
      "Content-Type" = "application/json"
    }
    oidc_token {
      service_account_email = "821345582451-compute@developer.gserviceaccount.com"
      audience = google_cloudfunctions2_function.orchestrator-function.url
    }
  }

  
}

resource "google_cloud_scheduler_job" "every-7-days" {
  paused           = false
  name             = "fass-7d-trigger-${terraform.workspace}"
  description      = "Trigger Fake Adjust Serverless Service every 7 days"
  schedule         = "45 0 * * 0"
  time_zone        = "Europe/Berlin"
  attempt_deadline = "1200s"

  retry_config {
    retry_count = 0
  }

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions2_function.orchestrator-function.url
    body        = base64encode("{\"scheduler_id\":\"7d\"}")
    headers = {
      "Content-Type" = "application/json"
    }
    oidc_token {
      service_account_email = "821345582451-compute@developer.gserviceaccount.com"
      audience = google_cloudfunctions2_function.orchestrator-function.url
    }
  }

}

resource "google_cloud_scheduler_job" "every-1-month" {
  paused           = false
  name             = "fass-1m-trigger-${terraform.workspace}"
  description      = "Trigger Fake Adjust Serverless Service every 1 month"
  schedule         = "0 0 1 * *"
  time_zone        = "Europe/Berlin"
  attempt_deadline = "1200s"

  retry_config {
    retry_count = 0
  }

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions2_function.orchestrator-function.url
    body        = base64encode("{\"scheduler_id\":\"1m\"}")
    headers = {
      "Content-Type" = "application/json"
    }
    oidc_token {
      service_account_email = "821345582451-compute@developer.gserviceaccount.com"
      audience = google_cloudfunctions2_function.orchestrator-function.url
    }
  }

}

#--------------------------- Cloud Functions

resource "google_cloudfunctions2_function" "orchestrator-function" {
  name = "fass-orchestrator-${terraform.workspace}"
  location = "us-central1"
  description = "Coordinate Fake Adjust Report API executor and loader functions"

  build_config {
    runtime = "python311"
    entry_point = "handle_adjust_api_calls"
    source {
      storage_source {
        bucket = google_storage_bucket.gcf-storage.name
        object = google_storage_bucket_object.orchestrator-archive.name
      }
    }
  }

  service_config {
    max_instance_count  = 3
    available_memory    = "512M"
    timeout_seconds     = 1920
    environment_variables = {
        EXECUTOR_URL = google_cloudfunctions2_function.executor-function.url
        GCS_BUCKET = google_storage_bucket.gcf-storage.name
    }
  }
}

resource "google_cloudfunctions2_function" "executor-function" {
  name = "fass-executor-${terraform.workspace}"
  location = "us-central1"
  description = "Call Fake Adjust Report API for data extraction"

  build_config {
    runtime = "python311"
    entry_point = "call_adjust_api"
    source {
      storage_source {
        bucket = google_storage_bucket.gcf-storage.name
        object = google_storage_bucket_object.executor-archive.name
      }
    }
  }

  service_config {
    max_instance_count  = 31
    available_memory    = "2Gi"
    available_cpu = "2"
    timeout_seconds     = 1200
    environment_variables = {
        GCS_BUCKET = google_storage_bucket.gcf-storage.name
    }
  }
}
