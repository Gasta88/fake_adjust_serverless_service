provider "google" {
  region = "us-central1"
  project = "eighth-duality-457819-r4"
}

terraform {
  required_version = ">= 0.14"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
  backend "gcs" {}
}

#--------------------------- Cloud Storage

resource "google_storage_bucket" "gcf_storage" {
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


resource "google_storage_bucket_object" "orchestrator_archive" {
  name   = "script/orchestrator.zip"
  bucket = google_storage_bucket.gcf_storage.name
  source = "../orchestrator.zip"
  depends_on = [ data.archive_file.orchestrator ]
}

resource "google_storage_bucket_object" "executor_archive" {
  name   = "script/executor.zip"
  bucket = google_storage_bucket.gcf_storage.name
  source = "../executor.zip"
  depends_on = [ data.archive_file.executor ]
}


#--------------------------- Cloud Schedulers

resource "google_cloud_scheduler_job" "every_2_hours" {
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
    uri         = google_cloudfunctions2_function.orchestrator_function.url
    body        = base64encode("{\"scheduler_id\":\"2h\"}")
    headers = {
      "Content-Type" = "application/json"
    }
    oidc_token {
      service_account_email = "874544665874-compute@developer.gserviceaccount.com"
      audience = google_cloudfunctions2_function.orchestrator_function.url
    }
  }

  
}

resource "google_cloud_scheduler_job" "every_7_days" {
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
    uri         = google_cloudfunctions2_function.orchestrator_function.url
    body        = base64encode("{\"scheduler_id\":\"7d\"}")
    headers = {
      "Content-Type" = "application/json"
    }
    oidc_token {
      service_account_email = "874544665874-compute@developer.gserviceaccount.com"
      audience = google_cloudfunctions2_function.orchestrator_function.url
    }
  }

}

resource "google_cloud_scheduler_job" "every_1_month" {
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
    uri         = google_cloudfunctions2_function.orchestrator_function.url
    body        = base64encode("{\"scheduler_id\":\"1m\"}")
    headers = {
      "Content-Type" = "application/json"
    }
    oidc_token {
      service_account_email = "874544665874-compute@developer.gserviceaccount.com"
      audience = google_cloudfunctions2_function.orchestrator_function.url
    }
  }

}

#--------------------------- Cloud Functions

resource "google_cloudfunctions2_function" "orchestrator_function" {
  name = "fass-orchestrator-${terraform.workspace}"
  location = "us-central1"
  description = "Coordinate Fake Adjust Report API executor and loader functions"

  build_config {
    runtime = "python311"
    entry_point = "handle_adjust_api_calls"
    source {
      storage_source {
        bucket = google_storage_bucket.gcf_storage.name
        object = google_storage_bucket_object.orchestrator_archive.name
      }
    }
  }

  service_config {
    max_instance_count  = 3
    available_memory    = "512M"
    timeout_seconds     = 1920
    environment_variables = {
        EXECUTOR_URL = google_cloudfunctions2_function.executor_function.url
        GCS_BUCKET = google_storage_bucket.gcf_storage.name
    }
  }
}

resource "google_cloudfunctions2_function" "executor_function" {
  name = "fass-executor-${terraform.workspace}"
  location = "us-central1"
  description = "Call Fake Adjust Report API for data extraction"

  build_config {
    runtime = "python311"
    entry_point = "call_adjust_api"
    source {
      storage_source {
        bucket = google_storage_bucket.gcf_storage.name
        object = google_storage_bucket_object.executor_archive.name
      }
    }
  }

  service_config {
    max_instance_count  = 31
    available_memory    = "2Gi"
    available_cpu = "2"
    timeout_seconds     = 1200
    environment_variables = {
        GCS_BUCKET = google_storage_bucket.gcf_storage.name
    }
  }
}

#--------------------------- Cloud Run

# data "google_artifact_registry_repository" "docker_registry" {
#   location = "us-central1"
#   repository_id = "data-ecr"
# }

# resource "null_resource" "build_and_push_image" {
#   provisioner "local-exec" {
#     command = "docker build ../fake_adjust_api --file ../fake_adjust_api/Dockerfile --tag gcr.io/us-central1-docker.pkg.dev/eighth-duality-457819-r4/${data.google_artifact_registry_repository.docker_registry.name}/fake_adjust:latest && docker push gcr.io/us-central1-docker.pkg.dev/eighth-duality-457819-r4/${data.google_artifact_registry_repository.docker_registry.name}/fake_adjust:latest"
#   }
#   depends_on = [ data.google_artifact_registry_repository.docker_registry ]
# }

# resource "google_cloud_run_service" "fake_api" {
#   name = "fake-adjust-api"
#   location = "us-central1"
#   template {
#     spec {
#       containers {
#         image = "gcr.io/us-central1-docker.pkg.dev/eighth-duality-457819-r4/${data.google_artifact_registry_repository.docker_registry.name}/fake_adjust:latest"
#       }
#     }
#   }
#   depends_on = [ null_resource.build_and_push_image ]
# }
