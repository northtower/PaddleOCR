#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Batch OCR Processing Script - Pure OCR Mode for Traditional Chinese Vertical Text
Processes all images in a directory using pure OCR (without ppstructure layout detection)
Optimized for traditional Chinese vertical text recognition
"""

import os
import glob
import subprocess
import sys
from pathlib import Path
import json

# Configuration
INPUT_DIR = r"C:\codeBase\pdf\pdf-parser-clib\build\output\h1"
OUTPUT_DIR = r".\output\vertical_zhtw_batch"
CONDA_ENV = "paddleocr310"

# Model paths
DET_MODEL = r"inference\ch_PP-OCRv3_det_infer"
REC_MODEL = r"inference\ch_PP-OCRv3_rec_infer"

# Dictionary and font paths
REC_DICT = r"..\ppocr\utils\ppocr_keys_v1.txt"
VIS_FONT = r"..\doc\fonts\chinese_cht.ttf"

# Optimized detection parameters for traditional Chinese vertical text
DET_DB_THRESH = "0.2"
DET_DB_BOX_THRESH = "0.45"
DET_DB_UNCLIP_RATIO = "1.6"
DET_LIMIT_SIDE_LEN = "1920"

# Supported image extensions
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']


def get_image_files(directory):
    """Get all image files from the specified directory"""
    image_files = []
    for ext in IMAGE_EXTENSIONS:
        # Use case-insensitive pattern matching
        pattern = os.path.join(directory, f"*{ext}")
        image_files.extend(glob.glob(pattern))
    
    # Remove duplicates and sort
    # Use set with normalized paths to avoid duplicates
    unique_files = list(set(os.path.normpath(f) for f in image_files))
    return sorted(unique_files)


def run_ocr(image_path, output_subdir):
    """Run pure OCR on a single image"""
    image_name = Path(image_path).stem
    print(f"\n{'='*60}")
    print(f"Processing: {Path(image_path).name}")
    print(f"{'='*60}")
    
    # Create output subdirectory for this image
    image_output_dir = os.path.join(output_subdir, image_name)
    os.makedirs(image_output_dir, exist_ok=True)
    
    # Build the command for pure OCR
    cmd = [
        "python", r"..\tools\infer\predict_system.py",
        f"--image_dir={image_path}",
        f"--det_model_dir={DET_MODEL}",
        f"--rec_model_dir={REC_MODEL}",
        f"--rec_char_dict_path={REC_DICT}",
        f"--vis_font_path={VIS_FONT}",
        f"--det_db_thresh={DET_DB_THRESH}",
        f"--det_db_box_thresh={DET_DB_BOX_THRESH}",
        f"--det_db_unclip_ratio={DET_DB_UNCLIP_RATIO}",
        f"--det_limit_side_len={DET_LIMIT_SIDE_LEN}",
        f"--draw_img_save_dir={image_output_dir}",
        f"--save_log_path={image_output_dir}",
        "--use_gpu=True",
        "--use_angle_cls=False"
    ]
    
    try:
        # Run the command
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        # Save the output to a text file
        output_txt = os.path.join(image_output_dir, "ocr_result.txt")
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write(f"OCR Results for: {Path(image_path).name}\n")
            f.write("=" * 60 + "\n\n")
            f.write(result.stdout)
            if result.stderr:
                f.write("\n\n" + "=" * 60 + "\n")
                f.write("Errors/Warnings:\n")
                f.write("=" * 60 + "\n")
                f.write(result.stderr)
        
        print(f"✓ Successfully processed: {Path(image_path).name}")
        print(f"  Output: {image_output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error processing {Path(image_path).name}: {e}")
        # Save error information
        error_txt = os.path.join(image_output_dir, "error.txt")
        with open(error_txt, 'w', encoding='utf-8') as f:
            f.write(f"Error processing: {Path(image_path).name}\n")
            f.write(f"Error: {str(e)}\n")
            if e.stdout:
                f.write(f"\nStdout:\n{e.stdout}\n")
            if e.stderr:
                f.write(f"\nStderr:\n{e.stderr}\n")
        return False
    except Exception as e:
        print(f"✗ Unexpected error processing {Path(image_path).name}: {e}")
        error_txt = os.path.join(image_output_dir, "error.txt")
        with open(error_txt, 'w', encoding='utf-8') as f:
            f.write(f"Unexpected error: {str(e)}\n")
        return False


def main():
    print("="*60)
    print("Batch OCR Processing - Pure OCR Mode")
    print("Optimized for Traditional Chinese Vertical Text")
    print("="*60)
    print(f"\nInput Directory: {INPUT_DIR}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print(f"\nOptimized Parameters:")
    print(f"  - det_db_thresh: {DET_DB_THRESH} (降低检测阈值)")
    print(f"  - det_db_box_thresh: {DET_DB_BOX_THRESH} (降低框过滤阈值)")
    print(f"  - det_db_unclip_ratio: {DET_DB_UNCLIP_RATIO} (扩大检测框)")
    print(f"  - det_limit_side_len: {DET_LIMIT_SIDE_LEN} (更高分辨率)")
    print()
    
    # Check if input directory exists
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Input directory does not exist: {INPUT_DIR}")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Get all image files
    image_files = get_image_files(INPUT_DIR)
    
    if not image_files:
        print(f"No image files found in: {INPUT_DIR}")
        print(f"Supported extensions: {', '.join(IMAGE_EXTENSIONS)}")
        sys.exit(1)
    
    print(f"Found {len(image_files)} image(s) to process:")
    for i, img in enumerate(image_files, 1):
        print(f"  {i}. {Path(img).name}")
    print()
    
    # Ask for confirmation
    response = input(f"Continue to process {len(image_files)} images? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled by user.")
        sys.exit(0)
    
    # Process each image
    success_count = 0
    failed_count = 0
    
    for i, image_path in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}]")
        if run_ocr(image_path, OUTPUT_DIR):
            success_count += 1
        else:
            failed_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("Processing Complete!")
    print(f"{'='*60}")
    print(f"Total: {len(image_files)} images")
    print(f"Success: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("\nEach image has its own subdirectory with:")
    print("  - <image_name>.jpg: Visualization with detected text boxes")
    print("  - system_results.txt: Detected text and coordinates")
    print("  - ocr_result.txt: Full OCR output log")
    print()


if __name__ == "__main__":
    # Check if we're in the correct conda environment
    current_env = os.environ.get('CONDA_DEFAULT_ENV', '')
    if current_env != CONDA_ENV:
        print(f"Warning: Not in the expected conda environment!")
        print(f"Expected: {CONDA_ENV}")
        print(f"Current: {current_env or 'None'}")
        print(f"\nPlease activate the environment first:")
        print(f"  conda activate {CONDA_ENV}")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    main()

