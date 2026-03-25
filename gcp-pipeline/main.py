import io
import os
import logging
import flask
from google.cloud import storage
from PIL import Image, ImageOps
import pillow_heif

# Register HEIF/HEIC opener
pillow_heif.register_heif_opener()

logging.basicConfig(level=logging.INFO)
app = flask.Flask(__name__)

# Environment variables
INPUT_BUCKET = os.environ.get("INPUT_BUCKET", "raw-images")
OUTPUT_BUCKET = os.environ.get("OUTPUT_BUCKET", "watermarked-images")
ASSETS_BUCKET = os.environ.get("ASSETS_BUCKET", "assets")
WATERMARK_OBJECT = os.environ.get("WATERMARK_OBJECT", "watermark.png")

LOGO_SCALE = 0.40   # 40% of the longest side
MARGIN_PCT = 0.03   # 3% margin from corner

storage_client = storage.Client()

def load_watermark() -> Image.Image:
    """Load watermark PNG from the GCS assets bucket."""
    bucket = storage_client.bucket(ASSETS_BUCKET)
    blob = bucket.blob(WATERMARK_OBJECT)
    data = io.BytesIO(blob.download_as_bytes())
    logo = Image.open(data).convert("RGBA")
    return logo

def apply_watermark(img: Image.Image, logo: Image.Image) -> Image.Image:
    """
    Watermark an image:
    - Logo scaled to 40% of the longest side
    - Placed top-right with a 3% margin
    """
    img = ImageOps.exif_transpose(img)

    if img.mode != "RGBA":
        img = img.convert("RGBA")

    img_w, img_h = img.size
    longest = max(img_w, img_h)

    # Scale logo
    target_w = int(longest * LOGO_SCALE)
    aspect = logo.height / logo.width
    target_h = int(target_w * aspect)
    logo_resized = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # Position: top-right with 3% margin
    margin = int(longest * MARGIN_PCT)
    x = img_w - target_w - margin
    y = margin

    # Composite
    canvas = Image.new("RGBA", img.size, (0, 0, 0, 0))
    canvas.paste(img, (0, 0))
    canvas.paste(logo_resized, (x, y), mask=logo_resized)

    return canvas

@app.route("/", methods=["POST"])
def handle_event():
    """Receive Eventarc GCS finalized event and process the image."""
    envelope = flask.request.get_json(silent=True) or {}
    
    src_bucket_name = None
    object_name = None

    # First, check if bucket and name exist at the root (Binary mode/GCS notifications)
    if "bucket" in envelope and "name" in envelope:
        src_bucket_name = envelope.get("bucket")
        object_name = envelope.get("name")
    # If not found at the root, check inside a data field (Structured mode)
    elif "data" in envelope and isinstance(envelope["data"], dict):
        src_bucket_name = envelope["data"].get("bucket")
        object_name = envelope["data"].get("name")

    # Ensure Object Decoding
    if object_name:
        import urllib.parse
        object_name = urllib.parse.unquote(object_name)

    # If still not found, log the entire JSON payload as an error
    if not src_bucket_name or not object_name:
        import json
        logging.error(f"Missing bucket or name in event payload. Raw payload: {json.dumps(envelope)}")
        return "Bad Request: missing bucket/name", 400

    logging.info(f"Processing gs://{src_bucket_name}/{object_name}")

    # Download source image
    src_bucket = storage_client.bucket(src_bucket_name)
    src_blob = src_bucket.blob(object_name)
    img_bytes = io.BytesIO(src_blob.download_as_bytes())

    # Open and watermark
    img = Image.open(img_bytes)
    logo = load_watermark()
    result = apply_watermark(img, logo)

    # Save as JPEG
    output_buf = io.BytesIO()
    result.convert("RGB").save(output_buf, format="JPEG", quality=95)
    output_buf.seek(0)

    # Determine output filename (convert .heic/.heif to .jpg)
    base, ext = os.path.splitext(object_name)
    if ext.lower() in [".heic", ".heif"]:
        out_name = base + ".jpg"
    else:
        out_name = object_name

    out_name = "watermarked_" + out_name

    # Upload to output bucket
    out_bucket = storage_client.bucket(OUTPUT_BUCKET)
    out_blob = out_bucket.blob(out_name)
    out_blob.upload_from_file(output_buf, content_type="image/jpeg")

    logging.info(f"Uploaded watermarked image to gs://{OUTPUT_BUCKET}/{out_name}")
    return f"Processed {object_name}", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False)
