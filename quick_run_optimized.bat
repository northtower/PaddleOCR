@echo off
chcp 65001 >nul
echo ========================================
echo Quick Run - Optimized Font Recognition
echo ========================================
echo.
echo Using: Simplified Font Model (4 classes)
echo Performance: ~1.7s per image (47x faster!)
echo.

call conda activate paddleocr310

python .\ppstructure\predict_system.py ^
  --image_dir="C:\codeBase\src\rag\docs\qwen\images\general\p1_Page1.jpg" ^
  --det_model_dir=ppstructure\inference\new-version\PP-OCRv5_server_det_infer ^
  --rec_model_dir=ppstructure\inference\new-version\PP-OCRv5_server_rec_infer ^
  --table_model_dir=ppstructure\inference\new-version\SLANeXt_wired_infer ^
  --rec_char_dict_path=ppocr\utils\dict\ppocrv5_dict.txt ^
  --table_char_dict_path=ppocr\utils\dict\table_structure_dict_ch.txt ^
  --layout_model_dir=ppstructure\inference\picodet_lcnet_x1_0_fgd_layout_cdla_infer ^
  --layout_dict_path=ppocr\utils\dict\layout_dict\layout_cdla_dict.txt ^
  --vis_font_path=doc\fonts\chinese_cht.ttf ^
  --output=./output/ ^
  --return_word_box=True ^
  --enable_font_classifier=True ^
  --use_simple_font=True ^
  --font_simple_model_path=inference\font_classifier\simple\model.pdparams ^
  --font_simple_dict_path=inference\font_classifier\simple\labels.txt ^
  --font_classifier_batch_size=128

echo.
echo ========================================
echo Completed!
echo ========================================
echo.
echo Output: output\structure\image-3\
echo   - res_0.txt: JSON results with Paragraph-Run-Text structure
echo   - show_0.jpg: Visualization
echo.
echo Font classes (4):
echo   1. 中文宋体
echo   2. 中文黑体
echo   3. Times New Roman
echo   4. Arial
echo.




