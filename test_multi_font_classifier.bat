@echo off
chcp 65001 >nul
echo ========================================
echo Multi-Attribute Font Classifier Test
echo ========================================
echo.

echo [1/4] Checking model files...
if not exist "inference\font_classifier\family\model.pdparams" (
    echo   X family model not found
    exit /b 1
)
if not exist "inference\font_classifier\size\model.pdparams" (
    echo   X size model not found
    exit /b 1
)
if not exist "inference\font_classifier\style\model.pdparams" (
    echo   X style model not found
    exit /b 1
)
if not exist "inference\font_classifier\color\model.pdparams" (
    echo   X color model not found
    exit /b 1
)
echo   √ All model files found
echo.

echo [2/4] Checking label files...
if not exist "inference\font_classifier\family\labels.txt" (
    echo   X family labels not found
    exit /b 1
)
if not exist "inference\font_classifier\size\labels.txt" (
    echo   X size labels not found
    exit /b 1
)
if not exist "inference\font_classifier\style\labels.txt" (
    echo   X style labels not found
    exit /b 1
)
if not exist "inference\font_classifier\color\labels.txt" (
    echo   X color labels not found
    exit /b 1
)
echo   √ All label files found
echo.

echo [3/4] Checking test image...
if not exist "ppstructure\docs\img\0a4ad205277a55592971b5ebf7970cbb\image-3.jpg" (
    echo   X Test image not found
    exit /b 1
)
echo   √ Test image found
echo.

echo [4/4] Running ppstructure test with font classifiers...
echo.

call conda activate paddleocr310

python ppstructure\predict_system.py ^
  --image_dir="ppstructure\docs\img\0a4ad205277a55592971b5ebf7970cbb\image-3.jpg" ^
  --det_model_dir=ppstructure\inference\new-version\PP-OCRv5_server_det_infer ^
  --rec_model_dir=ppstructure\inference\new-version\PP-OCRv5_server_rec_infer ^
  --table_model_dir=ppstructure\inference\new-version\SLANeXt_wired_infer ^
  --rec_char_dict_path=ppocr\utils\dict\ppocrv5_dict.txt ^
  --table_char_dict_path=ppocr\utils\dict\table_structure_dict_ch.txt ^
  --layout_model_dir=ppstructure\inference\picodet_lcnet_x1_0_fgd_layout_cdla_infer ^
  --layout_dict_path=ppocr\utils\dict\layout_dict\layout_cdla_dict.txt ^
  --vis_font_path=doc\fonts\chinese_cht.ttf ^
  --output=./output_test_font/ ^
  --return_word_box=True ^
  --enable_font_classifier=True ^
  --font_family_model_path=inference\font_classifier\family\model.pdparams ^
  --font_family_dict_path=inference\font_classifier\family\labels.txt ^
  --font_size_model_path=inference\font_classifier\size\model.pdparams ^
  --font_size_dict_path=inference\font_classifier\size\labels.txt ^
  --font_style_model_path=inference\font_classifier\style\model.pdparams ^
  --font_style_dict_path=inference\font_classifier\style\labels.txt ^
  --font_color_model_path=inference\font_classifier\color\model.pdparams ^
  --font_color_dict_path=inference\font_classifier\color\labels.txt

if errorlevel 1 (
    echo.
    echo X Test failed
    exit /b 1
)

echo.
echo ========================================
echo Test completed successfully!
echo ========================================
echo.
echo Output directory: output_test_font\structure
echo Check the res_*.txt files for OCR results with font attributes
echo.
