# deploy.ps1 — Full GCP deployment for the Image Watermarker pipeline
# Usage: .\deploy.ps1 -ProjectId "your-project-id" -Region "us-central1"

param (
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    [string]$Region = "us-central1"
)

$ErrorActionPreference = "Stop"

$ServiceName = "image-watermarker"
$RepoName = "watermarker-repo"
$ImageUri = "${Region}-docker.pkg.dev/${ProjectId}/${RepoName}/${ServiceName}:latest"

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  PROJECT : $ProjectId"
Write-Host "  REGION  : $Region"
Write-Host "  IMAGE   : $ImageUri"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# ── 1. Enable required APIs ───────────────────────────────────────────────────
Write-Host "▶ Enabling GCP APIs..." -ForegroundColor Yellow
gcloud services enable `
  run.googleapis.com `
  eventarc.googleapis.com `
  artifactregistry.googleapis.com `
  cloudbuild.googleapis.com `
  storage.googleapis.com `
  --project=$ProjectId

# ── 2. Create Artifact Registry repository ───────────────────────────────────
Write-Host "▶ Creating Artifact Registry repository..." -ForegroundColor Yellow
try {
    gcloud artifacts repositories create $RepoName `
      --repository-format=docker `
      --location=$Region `
      --project=$ProjectId `
      --quiet
} catch {
    Write-Host "  (repository may already exist, continuing...)" -ForegroundColor Gray
}

# ── 3. Build and push container image ────────────────────────────────────────
Write-Host "▶ Building container with Cloud Build and pushing..." -ForegroundColor Yellow
gcloud builds submit . `
  --tag=$ImageUri `
  --project=$ProjectId

# ── 4. Terraform init + apply ─────────────────────────────────────────────────
Write-Host "▶ Running Terraform..." -ForegroundColor Yellow
terraform init

terraform apply `
  -var="project_id=$ProjectId" `
  -var="region=$Region" `
  -var="image_uri=$ImageUri" `
  -auto-approve

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "   Upload a test image to: gs://${ProjectId}-raw-images/"
Write-Host "   Watermarked results:    gs://${ProjectId}-watermarked-images/"
