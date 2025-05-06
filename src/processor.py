from PIL import Image, ImageOps  # ImageOps is imported if you use it later
import os


class WatermarkError(Exception):
    pass


# Keep margin adjusted here
def calculate_position(base_width, base_height, wm_width, wm_height, position, margin=50):
    """Calculates the (x, y) coordinates for the watermark's top-left corner."""
    # --- Calculate x ---
    if position in ['Bottom-Right', 'Top-Right']:
        x = base_width - wm_width - margin
    elif position in ['Bottom-Left', 'Top-Left']:
        x = margin
    elif position == 'Center':
        x = (base_width - wm_width) // 2
    else:  # Default: Bottom-Right
        x = base_width - wm_width - margin

    # --- Calculate y ---
    if position in ['Top-Right', 'Top-Left']:
        y = margin
    elif position in ['Bottom-Right', 'Bottom-Left']:
        y = base_height - wm_height - margin
    elif position == 'Center':
        y = (base_height - wm_height) // 2
    else:  # Default: Bottom-Right
        y = base_height - wm_height - margin

    # Ensures coordinates are within image bounds and prevents negative values if watermark + margin is too big
    x = max(0, x)
    y = max(0, y)

    return (x, y)


def apply_watermark(image_path, watermark_image_rgba, output_path, position, quality=95):
    """
    Applies watermark (passed as RGBA Pillow object) to a single image
    and saves the result in the original image's format where possible.
    """
    try:
        # Open the base image
        base_image = Image.open(image_path)
        # Stores original format
        original_format = base_image.format.upper() if base_image.format else None
        print(f"   Original format: {original_format}")  # Log format

        # Prepares base image for pasting RGBA watermark
        # Convert to RGBA temporarily for the paste operation
        if base_image.mode != 'RGBA':
            base_for_paste = base_image.convert('RGBA')
        else:
            base_for_paste = base_image.copy()  # Work on a copy if already RGBA

        wm_image = watermark_image_rgba.copy()  # Watermark is already RGBA

        wm_width, wm_height = wm_image.size
        base_width, base_height = base_for_paste.size

        # Calculates Position
        pos = calculate_position(
            base_width, base_height, wm_width, wm_height, position)

        # Pastes Watermark
        base_for_paste.paste(wm_image, pos, wm_image)

        # Determines Output Format and Prepare Image
        save_options = {}
        save_format = None
        output_extension = None
        final_image_to_save = None

        if original_format == 'JPEG':
            # Converts to RGB (JPEG doesn't support alpha)
            final_image_to_save = base_for_paste.convert("RGB")
            output_extension = ".jpg"
            save_format = "JPEG"
            save_options = {'quality': quality,
                            'optimize': True}  # Adds optimize option
        elif original_format == 'PNG':
            # Keeps RGBA for PNG
            final_image_to_save = base_for_paste
            output_extension = ".png"
            save_format = "PNG"
            save_options = {'optimize': True}
        elif original_format == 'GIF':
            # GIF saved as PNG because its safer.
            print(
                "   Warning: Original format was GIF. Saving watermarked image as PNG to preserve transparency.")
            final_image_to_save = base_for_paste
            output_extension = ".png"  # Output PNG
            save_format = "PNG"
            save_options = {'optimize': True}
        elif original_format == 'TIFF':
            # Keep RGBA for TIFF
            final_image_to_save = base_for_paste
            output_extension = ".tiff"
            save_format = "TIFF"
            # Common compression
            save_options = {'compression': 'tiff_lzw'}
        elif original_format == 'BMP':
            # Converts to RGB for BMP
            final_image_to_save = base_for_paste.convert("RGB")
            output_extension = ".bmp"
            save_format = "BMP"
            save_options = {}
        elif original_format == 'WEBP':
            # Keep RGBA for WEBP (can handle transparency)
            final_image_to_save = base_for_paste
            output_extension = ".webp"
            save_format = "WEBP"
            # Choose lossless or lossy (with quality)
            save_options = {'quality': quality,
                            'lossless': False}  # lossy
            # Alternative lossless # save_options = {'lossless': True}
        else:
            # Fallback for unknown/unhandled formats: Save as PNG
            if original_format:
                print(
                    f"   Warning: Unsupported input format '{original_format}'. Saving as PNG.")
            else:
                print(f"   Warning: Could not determine original format. Saving as PNG.")
            final_image_to_save = base_for_paste
            output_extension = ".png"
            save_format = "PNG"
            save_options = {'optimize': True}

        # Constructs Output Filename AND Handle Collisions
        base_filename = os.path.basename(image_path)
        name, _ = os.path.splitext(base_filename)
        base_output_name = f"{name}_watermarked"

        output_filename = f"{base_output_name}{output_extension}"
        full_output_path = os.path.join(output_path, output_filename)
        counter = 1
        while os.path.exists(full_output_path):
            output_filename = f"{base_output_name}({counter}){output_extension}"
            full_output_path = os.path.join(output_path, output_filename)
            counter += 1

        # Save in Determined Format
        print(f"   Saving as {save_format} to: {output_filename}")
        final_image_to_save.save(
            full_output_path, format=save_format, **save_options)

        return True

    except Exception as e:
        print(
            f"Error processing {os.path.basename(image_path)}: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc()  # Print full traceback for debugging errors
        return False


def batch_watermark(image_paths, watermark_path, output_path, position, quality=95):
    """Processes a batch of images, saving results in original format where possible."""
    if not os.path.exists(watermark_path):
        raise FileNotFoundError(f"Watermark file not found: {watermark_path}")
    try:
        watermark_image_rgba = Image.open(watermark_path).convert("RGBA")
    except Exception as e:
        raise WatermarkError(
            f"Could not load or convert watermark file '{os.path.basename(watermark_path)}': {e}") from e

    success_count = 0
    total_images = len(image_paths)
    print(f"\nStarting batch processing for {total_images} images...")

    for i, img_path in enumerate(image_paths):
        print(
            f"Processing image {i+1}/{total_images}: {os.path.basename(img_path)} ...")
        # Pass quality setting down
        if apply_watermark(img_path, watermark_image_rgba, output_path, position, quality=quality):
            success_count += 1
        else:
            print(f" >> Failed to process {os.path.basename(img_path)}")

    print(
        f"Batch processing finished. {success_count}/{total_images} images processed successfully.")
    return success_count
