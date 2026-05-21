#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Batch OCR Processing Script
Processes all images in a directory using PaddleOCR with optimized font recognition
"""

import os
import glob
import subprocess
import sys
from pathlib import Path

# Configuration
INPUT_DIR = r"C:\codeBase\pdf\pdf-parser-clib\build\output\h1"
OUTPUT_DIR = r".\output"
CONDA_ENV = "paddleocr310"

# Model paths
DET_MODEL = r"ppstructure\inference\new-version\PP-OCRv5_server_det_infer"
REC_MODEL = r"ppstructure\inference\new-version\PP-OCRv5_server_rec_infer"
TABLE_MODEL = r"ppstructure\inference\new-version\SLANeXt_wired_infer"
LAYOUT_MODEL = r"ppstructure\inference\picodet_lcnet_x1_0_fgd_layout_cdla_infer"

# Dictionary paths
REC_DICT = r"ppocr\utils\dict\ppocrv5_dict.txt"
TABLE_DICT = r"ppocr\utils\dict\table_structure_dict_ch.txt"
LAYOUT_DICT = r"ppocr\utils\dict\layout_dict\layout_cdla_dict.txt"

# Font classifier paths
FONT_MODEL = r"inference\font_classifier\simple\model.pdparams"
FONT_DICT = r"inference\font_classifier\simple\labels.txt"
VIS_FONT = r"doc\fonts\chinese_cht.ttf"

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


def run_ocr(image_path):
    """Run OCR on a single image"""
    image_name = Path(image_path).name
    print(f"\n{'='*60}")
    print(f"Processing: {image_name}")
    print(f"{'='*60}")
    
    # Build the command
    cmd = [
        "python", r".\ppstructure\predict_system.py",
        f"--image_dir={image_path}",
        f"--det_model_dir={DET_MODEL}",
        f"--rec_model_dir={REC_MODEL}",
        f"--table_model_dir={TABLE_MODEL}",
        f"--rec_char_dict_path={REC_DICT}",
        f"--table_char_dict_path={TABLE_DICT}",
        f"--layout_model_dir={LAYOUT_MODEL}",
        f"--layout_dict_path={LAYOUT_DICT}",
        f"--vis_font_path={VIS_FONT}",
        f"--output={OUTPUT_DIR}",
        "--return_word_box=True",
        "--enable_font_classifier=True",
        "--use_simple_font=True",
        f"--font_simple_model_path={FONT_MODEL}",
        f"--font_simple_dict_path={FONT_DICT}",
        "--font_classifier_batch_size=128"
    ]
    
    try:
        # Run the command
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"✓ Successfully processed: {image_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error processing {image_name}: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error processing {image_name}: {e}")
        return False


def main():
    print("="*60)
    print("Batch OCR Processing - Optimized Font Recognition")
    print("="*60)
    print(f"\nInput Directory: {INPUT_DIR}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print(f"\nUsing: Simplified Font Model (4 classes)")
    print("Font classes:")
    print("  1. 中文宋体")
    print("  2. 中文黑体")
    print("  3. Times New Roman")
    print("  4. Arial")
    print()
    
    # Check if input directory exists
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Input directory does not exist: {INPUT_DIR}")
        sys.exit(1)
    
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
    
    # Process each image
    success_count = 0
    failed_count = 0
    
    for i, image_path in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}]")
        if run_ocr(image_path):
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
    print(f"\nOutput directory: {OUTPUT_DIR}\\structure\\")
    print("Each image will have its own subdirectory with:")
    print("  - res_0.txt: JSON results with Paragraph-Run-Text structure")
    print("  - show_0.jpg: Visualization")
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

