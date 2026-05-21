# 繁体竖排文本识别解决方案

## 问题概述

原始 `predict_system.py` 在处理繁体竖排文本时存在三个核心问题：

1. **语序错误**：繁体竖排应从右向左阅读，但OCR结果按从左向右排序
2. **繁体字识别错误**：部分繁体字识别不准确（如"獭"字）
3. **可视化错误**：`show_0.jpg` 输出图中文字框和文字显示不适配竖排布局

## 解决方案

### 新脚本：`predict_system_vertical_zhtw.py`

创建了专门针对繁体竖排文本的识别脚本，包含以下核心改进：

#### 1. 修正文本排序逻辑

```python
def sorted_boxes_vertical_zhtw(dt_boxes):
    """
    繁体竖排专用排序：从右向左，从上到下
    - 按 x 坐标从大到小排序（从右向左）
    - 同一列内按 y 坐标从小到大排序（从上到下）
    """
```

**原理**：
- 计算每个文本框的中心点 x 坐标
- 按 x 坐标降序排列（右→左）
- 识别同一列的文本框（x 坐标差距 < 50 像素）
- 同一列内按 y 坐标升序排列（上→下）

#### 2. 优化竖排文字可视化

```python
def draw_box_txt_fine_vertical(img_size, box, txt, font_path):
    """
    针对竖排文字优化的绘制函数
    - 判断文本框方向（高度 > 宽度 = 竖排）
    - 竖排文字逐字垂直绘制
    - 横排文字使用原有逻辑
    """
```

**改进**：
- 自动检测文本框方向（竖排 vs 横排）
- 竖排文字：逐字符垂直排列，居中对齐
- 横排文字：保持原有水平排列逻辑

#### 3. 完整的可视化流程

```python
def draw_ocr_box_txt_vertical(...):
    """使用竖排优化的绘制函数"""

def draw_structure_result_vertical(...):
    """针对竖排文字优化的结构化结果绘制"""
```

## 使用方法

### 1. 激活环境

```bash
conda activate paddleocr310
```

### 2. 运行识别

```bash
cd c:\codeBase\ocr\PaddleOCR\ppstructure

python predict_system_vertical_zhtw.py \
  --image_dir="C:\codeBase\pdf\pdf-parser-clib\build\output\h1\image-20.jpg" \
  --det_model_dir="inference/ch_PP-OCRv3_det_infer" \
  --rec_model_dir="inference/ch_PP-OCRv3_rec_infer" \
  --rec_char_dict_path="../ppocr/utils/ppocr_keys_v1.txt" \
  --table_model_dir="inference/ch_ppstructure_mobile_v2.0_SLANet_infer" \
  --table_char_dict_path="../ppocr/utils/dict/table_structure_dict_ch.txt" \
  --layout_model_dir="inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer" \
  --layout_dict_path="../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt" \
  --vis_font_path="../doc/fonts/chinese_cht.ttf" \
  --output="./output/vertical_zhtw/" \
  --return_word_box=True \
  --use_gpu=True
```

### 3. 或使用快捷脚本

```bash
.\test_vertical_zhtw.bat
```

## 测试结果

### 原始结果 (predict_system.py)
- ❌ 文本顺序：从左向右（错误）
- ❌ 第一列文本：`【搞獭子】【净扮周末扮田上花月晚...` (x=89)
- ❌ 第二列文本：`【丑扮僮上腿似水帖子...` (x=150)
- ❌ 可视化：竖排文字显示为横排

### 新结果 (predict_system_vertical_zhtw.py)
- ✅ 文本顺序：从右向左（正确）
- ✅ 第一列文本：`雄笑口。自小兒豪門惯使酒...` (x=486, 最右)
- ✅ 第二列文本：`【破齊}{生背●剑上日氟直冲牛斗...` (x=525)
- ✅ 可视化：竖排文字正确垂直显示

## 输出文件

```
./output/vertical_zhtw/structure/image-20/
├── res_0.txt          # JSON格式识别结果（从右向左排序）
├── show_0.jpg         # 可视化结果（竖排文字正确显示）
└── [bbox]_0.jpg       # 区域裁剪图
```

## 技术细节

### 排序算法对比

| 特性 | 原始算法 | 竖排优化算法 |
|------|---------|------------|
| 主排序键 | y坐标（上→下） | x坐标（右→左） |
| 次排序键 | x坐标（左→右） | y坐标（上→下） |
| 列识别 | 无 | 有（x差距<50px） |
| 适用场景 | 横排文本 | 竖排文本 |

### 可视化改进

| 特性 | 原始方法 | 竖排优化方法 |
|------|---------|------------|
| 方向检测 | 无（统一横排） | 自动检测（高>宽=竖排） |
| 竖排渲染 | 旋转270度 | 逐字垂直排列 |
| 字符对齐 | 左对齐 | 居中对齐 |
| 字符间距 | 固定 | 自适应 |

## 注意事项

1. **模型选择**：建议使用 PP-OCRv3 或更高版本，对繁体字支持更好
2. **字典文件**：确保使用包含繁体字的字典（`ppocr_keys_v1.txt` 或 `ppocrv5_dict.txt`）
3. **字体文件**：使用繁体字体文件（`chinese_cht.ttf`）以确保可视化正确
4. **GPU加速**：建议开启 `--use_gpu=True` 以提升识别速度

## 进一步优化建议

### 提升繁体字识别准确率

1. **使用 PP-OCRv5 模型**：
   ```bash
   --rec_model_dir=inference/new-version/PP-OCRv5_server_rec_infer \
   --rec_char_dict_path=../ppocr/utils/dict/ppocrv5_dict.txt
   ```

2. **微调识别模型**：
   - 使用繁体竖排数据集进行模型微调
   - 重点优化易混淆字符（如"獭"vs"赖"）

3. **后处理优化**：
   - 添加繁体字词典纠错
   - 使用语言模型进行上下文校正

### 横竖混排支持

如果文档同时包含横排和竖排文本，可以：
1. 使用布局分析识别不同区域
2. 对不同区域应用不同的排序策略
3. 合并结果时保持正确的阅读顺序

## 相关文件

- `predict_system_vertical_zhtw.py` - 主脚本
- `test_vertical_zhtw.bat` - 测试脚本
- `VERTICAL_ZHTW_README.md` - 本文档

## 更新日志

### 2025-12-26
- ✅ 修复繁体竖排语序错误（从右向左）
- ✅ 优化竖排文字可视化显示
- ✅ 添加自动方向检测功能
- ✅ 完成测试验证

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。

