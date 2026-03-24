#!/usr/bin/env bash
# deploy.sh — Full GCP deployment for the Image Watermarker pipeline
# Usage: ./deploy.sh <PROJECT_ID> <REGION>
# Example: ./deploy.sh my-gcp-project us-central1

set -euo pipefail

PROJECT_ID="${1:?Usage: ./deploy.sh <PROJECT_ID> [REGION]}"
REGION="${2:-us-central1}"
SERVICE_NAME="image-watermarker"
REPO_NAME="watermarker-repo"
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:latest"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PROJECT : $PROJECT_ID"
echo "  REGION  : $REGION"
echo "  IMAGE   : $IMAGE_URI"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. Enable required APIs ───────────────────────────────────────────────────
echo "▶ Enabling GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  eventarc.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  storage.googleapis.com \
  --project="${PROJECT_ID}"

# ── 2. Create Artifact Registry repository ───────────────────────────────────
echo "▶ Creating Artifact Registry repository..."
gcloud artifacts repositories create "${REPO_NAME}" \
  --repository-format=docker \
  --location="${REGION}" \
  --project="${PROJECT_ID}" \
  --quiet || echo "  (repository may already exist, continuing...)"

# ── 3. Build and push container image ────────────────────────────────────────
echo "▶ Building container with Cloud Build and pushing..."
gcloud builds submit . \
  --tag="${IMAGE_URI}" \
  --project="${PROJECT_ID}"

# ── 4. Terraform init + apply ─────────────────────────────────────────────────
echo "▶ Running Terraform..."
terraform init

terraform apply \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -var="image_uri=${IMAGE_URI}" \
  -auto-approve

echo ""
echo "✅ Deployment complete!"
echo "   Upload a test image to: gs://${PROJECT_ID}-raw-images/"
echo "   Watermarked results:    gs://${PROJECT_ID}-watermarked-images/"
