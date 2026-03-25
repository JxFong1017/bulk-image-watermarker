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
    - **Positioning:** Place the logo in the **upper-right** corner with a **3% margin** (based on the longest side).
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

Prerequisites
  Make sure you have these installed on your local machine:
   1. Google Cloud SDK (gcloud): Install Link (https://cloud.google.com/sdk/docs/install)
   2. Terraform: Install Link (https://developer.hashicorp.com/terraform/downloads)

  ---

  Step 1: Authenticate with Google Cloud
  Open your terminal and run these commands to log in:
   1 gcloud auth login
   2 gcloud auth application-default login

  Step 2: Get your Project ID
  Find your Project ID from the GCP Console (https://console.cloud.google.com/). It usually looks like my-project-12345.   

  Step 3: Run the Deployment Script
  I've written a deploy.sh script that handles everything (enabling APIs, building the container, and running Terraform).  

   1. Navigate to the pipeline folder:
   1     cd gcp-pipeline
   2. Make the script executable:

   1     chmod +x deploy.sh
   3. Run the deployment (replace <YOUR_PROJECT_ID> with your actual ID):
   1     ./deploy.sh <YOUR_PROJECT_ID> us-central1

  Step 4: Upload your Watermark Logo
  The system expects your logo to be in the assets bucket. Once the script finishes, it will show you the bucket names.    

   1. Find the assets bucket name (it will look like <project-id>-assets).
   2. Upload your watermark.png to that bucket:
   1     gcloud storage cp ../watermark.png gs://<YOUR_PROJECT_ID>-assets/

  Step 5: Test the Automation!
   1. Upload any photo (HEIC, JPG, or PNG) to the raw-images bucket.
   2. Wait about 5-10 seconds.
   3. Check the watermarked-images bucket. Your processed image will appear there automatically!

  ----
  Would you like me to help you find your Project ID or walk through any of these commands?
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
 > gcloud : The term 'gcloud' is not recognized as
   the name of a cmdlet, function, script file, or
   operable program. Check the spelling of the name,
   or if a path was included, verify that the path
   is correct and try again.
   At line:1 char:1
   + gcloud auth login
   + ~~~~~~
       + CategoryInfo          : ObjectNotFound: (gc
      loud:String) [], CommandNotFoundException
       + FullyQualifiedErrorId : CommandNotFoundExce
      ption
▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
✦ It looks like the Google Cloud SDK is not yet installed on your machine or its path isn't configured in your terminal.   
  Since you are on Windows, you have two options to fix this:

  Option 1: Install the SDK (Recommended)
   1. Download the Installer: Google Cloud SDK Windows Installer
      (https://dl.google.com/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe)
   2. Run the .exe: Follow the prompts. Make sure the option to "Add to PATH" is checked.
   3. Restart your Terminal: Close your current terminal/PowerShell and open a new one so it recognizes the new gcloud     
      command.

  Option 2: Use the Google Cloud Shell (Fastest/No Install)
  If you don't want to install anything locally, you can do everything through your browser:
   1. Go to the GCP Console (https://console.cloud.google.com/).
   2. In the top-right corner, click the "Activate Cloud Shell" icon (looks like >_).
   3. A terminal will open at the bottom of your browser.
   4. Upload your project files: Click the "three dots" menu in the Cloud Shell toolbar and select Upload. Upload the      
      contents of your gcp-pipeline/ folder and your watermark.png.
   5. Run the commands: You can run gcloud and terraform directly from there without any setup.

  ---
Once the deployment script finishes successfully, follow these steps in order to test your
  automated pipeline:

  Step 1: Upload your Watermark Logo
  The Cloud Run service needs your logo to be in the assets bucket to use it.
   1. Find the assets bucket name (it will be gdgoc-um-assets based on your project ID).
   2. Upload the logo from your project folder:

   1     gcloud storage cp ../watermark.png gs://gdgoc-um-assets/

  Step 2: Prepare a Test Image
  Pick a photo (HEIC, JPG, or PNG) from your computer.
   * Tip: Use an iPhone HEIC photo to test if the orientation fix and format conversion work        
     correctly.

  Step 3: Trigger the Pipeline
  Upload your test photo to the raw-images bucket:
   1. Run this command (replace my-photo.jpg with your filename):
   1     gcloud storage cp C:\Path\To\Your\photo.jpg gs://gdgoc-um-raw-images/
   2. Alternatively, go to the GCS Console
      (https://console.cloud.google.com/storage/browser/gdgoc-um-raw-images) and drag-and-drop the
      file.

  Step 4: Monitor the Processing (Real-time)
  If you want to see the automation "thinking," you can watch the Cloud Run logs:
   1. Go to the Cloud Run Console
      (https://console.cloud.google.com/run/detail/us-central1/image-watermarker/logs).
   2. You should see logs appearing like: Processing image: photo.jpg, Logo scaled to: ..., and
      Successfully uploaded to....

  Step 5: Verify the Result
   1. Wait about 5–10 seconds after the upload.
   2. Check the output bucket:

   1     gcloud storage ls gs://gdgoc-um-watermarked-images/
   3. Download and view the result:
   1     gcloud storage cp gs://gdgoc-um-watermarked-images/watermarked_photo.jpg . 
      (Open the downloaded file to see if the watermark is in the bottom-right corner at 40% size!)

  ---

  Troubleshooting Common Issues:
   * No output file? Check the Cloud Run logs (Step 4). The most common error is a missing
     watermark.png in the assets bucket.
   * Permission Error? Ensure you ran the deploy.ps1 script to completion, as it sets up the
     necessary IAM permissions for the Service Account.