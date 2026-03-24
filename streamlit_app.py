import streamlit as st
import io
import zipfile
from PIL import Image, ImageOps
import pillow_heif

# Register HEIF opener so PIL can open .heic files
pillow_heif.register_heif_opener()

st.set_page_config(page_title="Bulk Image Watermarker", page_icon="💧", layout="wide")

st.title("GDGoC UM < > Image Watermarker")
st.write("Upload your photos and a logo to watermark them in bulk.")

# Hardcoded Logo Configuration
logo_file = "watermark.png"
watermark_size_pct = 40
watermark_opacity = 1.0
watermark_position = "Top Right"

# Main area for bulk upload
st.header("Upload Photos")
uploaded_files = st.file_uploader(
    "Drag and drop multiple files here (.png, .jpg, .jpeg, .heic)", 
    type=["png", "jpg", "jpeg", "heic"], 
    accept_multiple_files=True
)

def process_image(img_file, logo_img, size_pct, position, opacity):
    """
    Processes a single image: applies correct orientation, resizes & positions logo,
    applies opacity, and pastes the logo onto the image.
    Returns an RGBA Image object.
    """
    # Open image
    img = Image.open(img_file)
    
    # Correct orientation based on EXIF (crucial for iPhone photos)
    img = ImageOps.exif_transpose(img)
    
    # Ensure image is in RGBA mode for proper compositing
    if img.mode != 'RGBA':
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img = img.convert('RGBA')

    # Prepare logo
    logo = logo_img.copy()
    if logo.mode != 'RGBA':
        logo = logo.convert('RGBA')

    # Apply opacity to logo
    if opacity < 1.0:
        alpha = logo.split()[3]
        alpha = alpha.point(lambda p: p * opacity)
        logo.putalpha(alpha)

    # Calculate logo size
    img_width, img_height = img.size
    logo_width, logo_height = logo.size
    
    # Ensure consistent logo size regardless of horizontal/vertical orientation
    # by basing the scale on the maximum dimension
    max_dim = max(img_width, img_height)
    target_logo_width = int(max_dim * (size_pct / 100.0))
    # Maintain aspect ratio
    aspect_ratio = logo_height / float(logo_width)
    target_logo_height = int(target_logo_width * aspect_ratio)
    
    # Resize logo smoothly
    logo = logo.resize((target_logo_width, target_logo_height), Image.Resampling.LANCZOS)
    
    # Calculate position
    padding = int(img_width * 0.02) # 2% padding
    
    if position == "Bottom Right":
        x = img_width - target_logo_width - padding
        y = img_height - target_logo_height - padding
    elif position == "Bottom Left":
        x = padding
        y = img_height - target_logo_height - padding
    elif position == "Top Right":
        x = img_width - target_logo_width - padding
        y = padding
    elif position == "Top Left":
        x = padding
        y = padding
    else: # Center
        x = (img_width - target_logo_width) // 2
        y = (img_height - target_logo_height) // 2

    # Paste logo depending on its alpha channel
    # create a transparent layer the size of the image
    transparent = Image.new('RGBA', img.size, (0, 0, 0, 0))
    transparent.paste(img, (0, 0))
    transparent.paste(logo, (x, y), mask=logo)
    
    return transparent

if logo_file and uploaded_files:
    # Load the logo once
    logo_image = Image.open(logo_file)
    
    st.header("Live Preview")
    st.write("Preview of the first uploaded image:")
    
    # Show preview
    first_file = uploaded_files[0]
    with st.spinner("Generating preview..."):
        # We need to reset the file pointer because st.image might use it or we'll process it
        first_file.seek(0)
        preview_img_rgba = process_image(first_file, logo_image, watermark_size_pct, watermark_position, watermark_opacity)
        # Convert to RGB for Streamlit preview (to avoid transparent background blending issues)
        preview_img_rgb = preview_img_rgba.convert("RGB")
        st.image(preview_img_rgb, caption=f"Previewing: {first_file.name}", use_container_width=True)

    st.header("Process All Images")
    if st.button("Start Bulk Watermarking", type="primary"):
        # Create a BytesIO object to hold the ZIP file
        zip_buffer = io.BytesIO()
        
        # Progress bar setup
        progress_text = "Operation in progress. Please wait."
        my_bar = st.progress(0, text=progress_text)
        
        total_files = len(uploaded_files)
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for i, file in enumerate(uploaded_files):
                # Update progress
                progress_percent = (i) / total_files
                my_bar.progress(progress_percent, text=f"Processing {file.name} ({i+1}/{total_files})")
                
                # Reset file pointer just in case
                file.seek(0)
                
                # Process the image
                watermarked_img_rgba = process_image(file, logo_image, watermark_size_pct, watermark_position, watermark_opacity)
                
                # Save the processed image to a BytesIO object
                img_buffer = io.BytesIO()
                
                # Decide on save extension based on original, default to jpeg for heic
                ext = file.name.split('.')[-1].lower()
                save_format = "JPEG"
                if ext == "png":
                    save_format = "PNG"
                    watermarked_img = watermarked_img_rgba # Keep transparency if saving as PNG
                else:
                    watermarked_img = watermarked_img_rgba.convert('RGB')
                
                # change filename to end in jpg if original was heic or jpeg
                new_filename = file.name
                if ext in ['heic', 'heif', 'jpeg']:
                    new_filename = new_filename.rsplit('.', 1)[0] + ".jpg"

                # Save image to in-memory buffer
                watermarked_img.save(img_buffer, format=save_format, quality=95)
                
                # Write to zip file
                zip_file.writestr("watermarked_" + new_filename, img_buffer.getvalue())
                
        # Finalize progress bar
        my_bar.progress(1.0, text="Processing complete!")
        st.success(f"All {total_files} images successfully watermarked!")
        
        # Provide the download button
        st.download_button(
            label="Download ZIP with Watermarked Images",
            data=zip_buffer.getvalue(),
            file_name="watermarked_images.zip",
            mime="application/zip",
            type="primary"
        )
        
elif not logo_file and uploaded_files:
    st.warning("Please upload a Logo file in the sidebar to proceed.")
elif logo_file and not uploaded_files:
    st.info("Please upload photos to begin.")
