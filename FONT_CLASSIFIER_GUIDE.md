# 字体属性识别集成指南

## 📌 功能说明

本集成模块为 PaddleOCR 添加了字体属性识别功能，可以在 OCR 识别文本的同时，识别每个文本行的字体家族（如宋体、黑体、Arial 等）。

### 支持的字体类别（13种）

**中文字体：**
1. 黑体
2. 宋体
3. 仿宋
4. 楷体
5. 微软雅黑
6. 隶书
7. 幼圆

**英文字体：**
8. Times New Roman
9. Arial
10. Courier New
11. Georgia
12. Helvetica
13. Comic Sans MS

### 模型性能

- **准确率**: 89.44%
- **输入尺寸**: 192x48 (宽x高)
- **模型大小**: ~4MB
- **推理速度**: CPU 约 10-20ms/图像

---

## 🚀 快速开始

### 1. 在 ppstructure 中使用（推荐）

```bash
cd /Users/zoutao03/codeBase/ocr/PaddleOCR/ppstructure

python predict_system.py \
  --image_dir=/path/to/your/image.jpg \
  --det_model_dir=inference/new-version/PP-OCRv5_server_det_infer \
  --rec_model_dir=inference/new-version/PP-OCRv5_server_rec_infer \
  --table_model_dir=inference/new-version/SLANeXt_wired_infer \
  --rec_char_dict_path=../ppocr/utils/dict/ppocrv5_dict.txt \
  --layout_model_dir=inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer \
  --output=./output/ \
  --return_word_box=True \
  --enable_font_classifier=True \
  --font_model_path=../inference/font_classifier/font_family.pdparams \
  --font_dict_path=../inference/font_classifier/font_family_dict.txt
```

### 2. 单独使用 OCR 系统

```bash
cd /Users/zoutao03/codeBase/ocr/PaddleOCR

python tools/infer/predict_system.py \
  --image_dir=/path/to/your/image.jpg \
  --det_model_dir=inference/new-version/PP-OCRv5_server_det_infer \
  --rec_model_dir=inference/new-version/PP-OCRv5_server_rec_infer \
  --enable_font_classifier=True \
  --font_model_path=./inference/font_classifier/font_family.pdparams \
  --font_dict_path=./inference/font_classifier/font_family_dict.txt
```

---

## 📊 输出格式

启用字体分类后，每个文本行的结果会包含以下字段：

```json
{
  "text": "这是识别的文本",
  "confidence": 0.95,
  "text_region": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]],
  "font_family": "宋体",
  "font_confidence": 0.92
}
```

**字段说明：**
- `text`: 识别的文本内容
- `confidence`: 文本识别置信度
- `text_region`: 文本区域坐标
- `font_family`: 识别的字体名称（仅在启用字体分类时）
- `font_confidence`: 字体识别置信度（仅在启用字体分类时）

---

## 🔧 参数说明

### 必需参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `--enable_font_classifier` | bool | False | 是否启用字体分类 |
| `--font_model_path` | str | ./inference/font_classifier/font_family.pdparams | 字体分类模型路径 |
| `--font_dict_path` | str | ./inference/font_classifier/font_family_dict.txt | 字体类别字典路径 |

### 可选参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `--use_gpu` | bool | False | 是否使用GPU（字体分类器会自动跟随） |
| `--enable_mkldnn` | bool | False | 是否启用MKLDNN加速（CPU模式） |

---

## 📝 使用示例

### 示例1：处理单张图片

```bash
cd ppstructure

python predict_system.py \
  --image_dir=docs/img/0a4ad205277a55592971b5ebf7970cbb/image-3.jpg \
  --det_model_dir=inference/new-version/PP-OCRv5_server_det_infer \
  --rec_model_dir=inference/new-version/PP-OCRv5_server_rec_infer \
  --enable_font_classifier=True \
  --output=./output_with_font/
```

### 示例2：批量处理文件夹

```bash
python predict_system.py \
  --image_dir=docs/img/ \
  --enable_font_classifier=True \
  --output=./batch_output/
```

### 示例3：查看详细日志

```bash
python predict_system.py \
  --image_dir=test.jpg \
  --enable_font_classifier=True \
  --show_log=True
```

---

## 🛠️ 文件结构

集成后的文件结构：

```
PaddleOCR/
├── inference/
│   └── font_classifier/
│       ├── font_family.pdparams          # 字体分类模型
│       └── font_family_dict.txt          # 字体类别字典
├── ppocr/
│   └── utils/
│       └── font_classifier.py            # 字体分类器类
├── tools/
│   └── infer/
│       ├── predict_system.py             # 修改：集成字体分类
│       └── utility.py                    # 修改：添加参数支持
└── ppstructure/
    ├── predict_system.py                 # 修改：支持字体属性输出
    └── utility.py                        # 修改：添加参数支持
```

---

## 🔍 验证安装

运行以下脚本验证字体分类器是否正确安装：

```python
import os
import sys
sys.path.insert(0, '/Users/zoutao03/codeBase/ocr/PaddleOCR')

from ppocr.utils.font_classifier import FontAttributeClassifier

# 检查模型文件
model_path = '/Users/zoutao03/codeBase/ocr/PaddleOCR/inference/font_classifier/font_family.pdparams'
dict_path = '/Users/zoutao03/codeBase/ocr/PaddleOCR/inference/font_classifier/font_family_dict.txt'

print(f"模型文件存在: {os.path.exists(model_path)}")
print(f"字典文件存在: {os.path.exists(dict_path)}")

# 初始化分类器
try:
    classifier = FontAttributeClassifier(
        model_path=model_path,
        dict_path=dict_path,
        use_gpu=False
    )
    print(f"✓ 字体分类器初始化成功")
    print(f"✓ 支持 {classifier.num_classes} 种字体")
    print(f"✓ 字体列表: {', '.join(classifier.classes)}")
except Exception as e:
    print(f"✗ 字体分类器初始化失败: {e}")
```

---

## ⚠️ 注意事项

1. **依赖检查**: 确保已安装 `paddleclas`
   ```bash
   pip install paddleclas
   ```

2. **模型路径**: 默认模型路径为相对路径，如果从其他目录运行，需要指定绝对路径

3. **性能影响**: 启用字体分类会增加约 10-20% 的处理时间

4. **准确率**: 字体分类准确率受以下因素影响：
   - 文本长度（建议至少3-5个字符）
   - 图像质量（分辨率、清晰度）
   - 字体变体（粗体、斜体等可能影响识别）

5. **中英文混合**: 如果文本包含中英文混合，模型会根据主要字符判断字体

---

## 📈 性能优化建议

### CPU 模式
```bash
--enable_mkldnn=True  # 启用MKLDNN加速
```

### GPU 模式
```bash
--use_gpu=True
--gpu_mem=500
```

### 批处理优化
```bash
--rec_batch_num=10  # 增加批处理大小
```

---

## 🐛 故障排除

### 问题1: 导入错误 "No module named 'ppcls'"

**解决方案:**
```bash
pip install paddleclas
```

### 问题2: 模型文件不存在

**解决方案:**
```bash
# 检查模型文件
ls -lh inference/font_classifier/

# 如果不存在，重新复制
cp /Users/zoutao03/codeBase/ocr/PaddleClas/output/cls_family_pplcnet/best_model.pdparams \
   inference/font_classifier/font_family.pdparams
```

### 问题3: 字体识别结果不准确

**可能原因及解决方案:**
1. 文本过短 → 确保文本至少3-5个字符
2. 图像模糊 → 提高图像分辨率
3. 字体变体 → 字体分类模型主要识别标准字体

---

## 📚 API 文档

### FontAttributeClassifier 类

```python
from ppocr.utils.font_classifier import FontAttributeClassifier

classifier = FontAttributeClassifier(
    model_path='./inference/font_classifier/font_family.pdparams',
    dict_path='./inference/font_classifier/font_family_dict.txt',
    use_gpu=False,
    enable_mkldnn=False
)

# 预测单张图像
result = classifier.predict(img_crop)
# 返回: {'class_id': 0, 'class_name': '黑体', 'confidence': 0.95}

# 批量预测
results = classifier.predict_batch(img_crop_list)
# 返回: [{'class_id': 0, 'class_name': '黑体', 'confidence': 0.95}, ...]
```

---

## 🎯 下一步计划

未来可以扩展的功能：

1. **字体风格识别**: 粗体、斜体、下划线
2. **字号识别**: 识别文本的字号大小
3. **颜色识别**: 识别文本的颜色
4. **多模型集成**: 组合多个字体属性模型

---

## 📞 技术支持

如有问题，请参考：
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- PaddleClas: https://github.com/PaddlePaddle/PaddleClas

---

**版本信息:**
- PaddleOCR: 最新版
- 字体分类模型: v1.0
- 最后更新: 2025-12-09

