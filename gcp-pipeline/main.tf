terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project_id" {
  description = "Your GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region to deploy to"
  type        = string
  default     = "us-central1"
}

variable "image_uri" {
  description = "Full Artifact Registry image URI for the Cloud Run service"
  type        = string
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Storage Buckets ──────────────────────────────────────────────────────────

resource "google_storage_bucket" "raw_images" {
  name                        = "${var.project_id}-raw-images"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "watermarked_images" {
  name                        = "${var.project_id}-watermarked-images"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "assets" {
  name                        = "${var.project_id}-assets"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true
}

# ── Service Account ───────────────────────────────────────────────────────────

resource "google_service_account" "watermarker_sa" {
  account_id   = "watermarker-sa"
  display_name = "Watermarker Cloud Run Service Account"
}

# Grant objectAdmin on all three buckets
resource "google_storage_bucket_iam_member" "raw_admin" {
  bucket = google_storage_bucket.raw_images.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.watermarker_sa.email}"
}

resource "google_storage_bucket_iam_member" "output_admin" {
  bucket = google_storage_bucket.watermarked_images.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.watermarker_sa.email}"
}

resource "google_storage_bucket_iam_member" "assets_admin" {
  bucket = google_storage_bucket.assets.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.watermarker_sa.email}"
}

# ── Cloud Run Service ─────────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "watermarker" {
  name     = "image-watermarker"
  location = var.region

  template {
    service_account = google_service_account.watermarker_sa.email

    containers {
      image = var.image_uri

      env {
        name  = "INPUT_BUCKET"
        value = google_storage_bucket.raw_images.name
      }
      env {
        name  = "OUTPUT_BUCKET"
        value = google_storage_bucket.watermarked_images.name
      }
      env {
        name  = "ASSETS_BUCKET"
        value = google_storage_bucket.assets.name
      }
      env {
        name  = "WATERMARK_OBJECT"
        value = "watermark.png"
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }
    }
  }
}

# ── Eventarc Trigger ──────────────────────────────────────────────────────────

# Allow Eventarc to invoke the Cloud Run service
resource "google_cloud_run_v2_service_iam_member" "eventarc_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.watermarker.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.watermarker_sa.email}"
}

resource "google_eventarc_trigger" "gcs_trigger" {
  name     = "gcs-image-upload-trigger"
  location = var.region

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.finalized"
  }

  matching_criteria {
    attribute = "bucket"
    value     = google_storage_bucket.raw_images.name
  }

  destination {
    cloud_run_service {
      service = google_cloud_run_v2_service.watermarker.name
      region  = var.region
      path    = "/"
    }
  }

  service_account = google_service_account.watermarker_sa.email

  depends_on = [google_cloud_run_v2_service.watermarker]
}

# ── Outputs ───────────────────────────────────────────────────────────────────

output "cloud_run_url" {
  value = google_cloud_run_v2_service.watermarker.uri
}

output "raw_images_bucket" {
  value = google_storage_bucket.raw_images.name
}

output "watermarked_images_bucket" {
  value = google_storage_bucket.watermarked_images.name
}

output "assets_bucket" {
  value = google_storage_bucket.assets.name
}
