# Cloud Run & GCS Image Processing Pipeline Blueprint

Act as a **Google Cloud Solutions Architect**. Use this blueprint to implement a production-grade, event-driven image processing system.

## 🏗️ Architecture Specification

### 1. Storage Layout
- **Input Bucket (`raw-images`):** For user-uploaded HEIC, JPG, and PNG files.
- **Output Bucket (`watermarked-images`):** For processed, high-quality JPEGs.
- **Assets Bucket (`assets`):** Stores `watermark.png` and other static files.

### 2. Compute & Trigger (Eventarc)
- **Cloud Run Service:** A containerized Python (Flask/Functions Framework) service.
- **Eventarc Trigger:** Capture `google.cloud.storage.object.v1.finalized` events from the input bucket and route them via HTTP POST to the Cloud Run service.

### 3. Application Logic (Python/Pillow)
The service must perform the following:
- **Download:** Stream the uploaded image from GCS into memory (`io.BytesIO`).
- **EXIF Correction:** Use `ImageOps.exif_transpose` (critical for HEIC/iPhone photos).
- **Watermarking Logic:**
    - Load the logo from `gs://assets-bucket/watermark.png`.
    - **Scaling:** Resize the logo to exactly **40% of the longest side** of the target image.
    - **Positioning:** Place the logo in the **bottom-right** corner with a **3% margin** (based on the longest side).
- **Upload:** Save as JPEG (quality=95) to the output bucket.

## 📜 Deployment Prompt

Copy and use this prompt to generate the implementation:

> **Role:** Senior Cloud Engineer & Python Developer
>
> **Task:** Implement the GCP Image Processing Pipeline defined in the architecture blueprint.
>
> **Deliverables:**
> 1. `main.tf`: Terraform for GCS buckets, Cloud Run service, Eventarc trigger, and IAM roles (`storage.objectAdmin`).
> 2. `main.py`: Python service using `google-cloud-storage`, `Pillow`, and `pillow-heif`. Ensure it parses the Eventarc payload for `bucket` and `name`.
> 3. `Dockerfile`: Optimized for Python 3.11-slim.
> 4. `deploy.sh`: Sequence of `gcloud` commands to enable APIs, build the container to Artifact Registry, and apply Terraform.
>
> **Logic Constraints:** 
> - Support HEIC via `pillow_heif.register_heif_opener()`.
> - Scale logo to 40% of longest side.
> - Margin of 3% from bottom-right.
> - Avoid recursive trigger loops by ensuring output bucket is distinct from input.
