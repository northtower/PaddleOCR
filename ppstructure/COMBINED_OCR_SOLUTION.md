# 繁体字OCR完整识别与字符位置解决方案

## 问题分析

### 命令1的问题
使用 `ppstructure/predict_system.py` 时：
- ✅ **优势**：支持 `--return_word_box=True`，可以获取字符级位置信息
- ❌ **劣势**：使用默认的严格检测参数，导致部分文字无法识别
  - `det_db_thresh=0.3` (默认值，较高)
  - `det_db_box_thresh=0.6` (默认值，较高)
  - `det_db_unclip_ratio=1.5` (默认值，较小)
  - `det_limit_side_len=960` (默认值，较小)

**结果**：无法识别"第二齣 俠概"等文字

### 命令2的问题
使用 `tools/infer/predict_system.py` 时：
- ✅ **优势**：使用宽松的检测参数，识别更完整
  - `det_db_thresh=0.2` (降低阈值)
  - `det_db_box_thresh=0.45` (降低阈值)
  - `det_db_unclip_ratio=1.6` (增加扩展比例)
  - `det_limit_side_len=1920` (增加图像尺寸限制)
- ❌ **劣势**：不支持字符级位置输出，只能输出行级位置

**结果**：能识别"第二齣 俠概"，但无法获取单字位置

## 解决方案

### 核心思路
将命令2的宽松检测参数应用到命令1，既保留字符位置功能，又提高识别完整性。

### 关键参数说明

1. **det_db_thresh** (0.2)
   - 二值化阈值，降低可以检测更多文字区域
   - 默认0.3太高，会漏掉一些浅色或小字

2. **det_db_box_thresh** (0.45)
   - 文本框置信度阈值，降低可以保留更多候选框
   - 默认0.6太高，会过滤掉一些真实文字

3. **det_db_unclip_ratio** (1.6)
   - 文本框扩展比例，增大可以包含更完整的文字
   - 默认1.5太小，可能截断文字边缘

4. **det_limit_side_len** (1920)
   - 图像最大边长限制，增大可以保留更多细节
   - 默认960太小，高分辨率图像会被过度缩放

## 使用方法

### 方法1：使用批处理文件 (Windows)
```batch
cd ppstructure
run_combined_ocr.bat
```

### 方法2：使用PowerShell脚本
```powershell
cd ppstructure
.\run_combined_ocr.ps1
```

### 方法3：直接运行命令
```bash
python predict_system.py \
  --image_dir="你的图片路径" \
  --det_model_dir="inference/ch_PP-OCRv4_det_server_infer" \
  --rec_model_dir="inference/PP-OCRv5_server_rec_infer" \
  --rec_char_dict_path="../ppocr/utils/dict/ppocrv5_dict.txt" \
  --vis_font_path="../doc/fonts/chinese_cht.ttf" \
  --table_model_dir="inference/ch_ppstructure_mobile_v2.0_SLANet_infer" \
  --table_char_dict_path="../ppocr/utils/dict/table_structure_dict_ch.txt" \
  --layout_model_dir="inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer" \
  --layout_dict_path="../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt" \
  --output="./output/combined/" \
  --return_word_box=True \
  --use_gpu=True \
  --det_db_thresh=0.2 \
  --det_db_box_thresh=0.45 \
  --det_db_unclip_ratio=1.6 \
  --det_limit_side_len=1920 \
  --use_angle_cls=False
```

## 输出结果

### 输出文件位置
```
ppstructure/output/combined/
├── structure/
│   └── image-20/
│       ├── res_0.txt          # 文本结果（简化版）
│       ├── res_0.json         # 完整JSON结果（包含字符位置）
│       └── show_0.jpg         # 可视化结果图
```

### JSON结果格式
```json
{
  "type": "figure",
  "bbox": [84, 92, 569, 1030],
  "res": [
    {
      "text": "第二齣 俠概",
      "confidence": 0.95,
      "region": [[591, 179], [625, 179], [625, 355], [591, 355]],
      "runs": [
        {
          "text": "第二齣俠概",
          "chars": ["第", "二", "齣", "俠", "概"],
          "char_regions": [
            [[591, 179], [595, 179], [595, 355], [591, 355]],
            [[595, 179], [599, 179], [599, 355], [595, 355]],
            ...
          ]
        }
      ],
      "text_word": ["第", "二", "齣", "俠", "概"],
      "text_word_region": [...]
    }
  ]
}
```

### 关键字段说明
- **text**: 识别的完整文本
- **confidence**: 识别置信度
- **region**: 整行文本的四角坐标
- **text_word**: 单字列表
- **text_word_region**: 每个单字的四角坐标
- **runs**: 段落-Run结构，支持字体属性分组

## 参数调优建议

如果仍有文字漏识别，可以进一步调整：

1. **降低阈值**（更宽松，但可能增加误检）
   ```
   --det_db_thresh=0.15
   --det_db_box_thresh=0.4
   ```

2. **增加扩展比例**（包含更多边缘文字）
   ```
   --det_db_unclip_ratio=1.8
   ```

3. **增加图像尺寸**（保留更多细节，但消耗更多内存）
   ```
   --det_limit_side_len=2560
   ```

4. **启用形态学膨胀**（连接断裂的文字）
   ```
   --use_dilation=True
   ```

## 性能对比

| 指标 | 命令1(默认) | 命令2 | 组合方案 |
|------|------------|-------|---------|
| 文字识别完整性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 字符位置支持 | ✅ | ❌ | ✅ |
| 识别速度 | 快 | 快 | 快 |
| 误检率 | 低 | 中 | 中 |

## 技术原理

### 检测参数的作用机制

1. **det_db_thresh**: 控制DB算法的二值化阈值
   - 原理：将概率图转换为二值图时的阈值
   - 降低 → 保留更多低置信度区域 → 检测更多文字

2. **det_db_box_thresh**: 控制文本框的最终筛选
   - 原理：根据文本框的平均得分过滤
   - 降低 → 保留更多候选框 → 减少漏检

3. **det_db_unclip_ratio**: 控制文本框的扩展
   - 原理：使用Vatti clipping算法扩展多边形
   - 增大 → 文本框更大 → 包含完整文字

4. **det_limit_side_len**: 控制输入图像的尺寸
   - 原理：限制最大边长以控制内存和速度
   - 增大 → 保留更多细节 → 识别小字更准确

## 常见问题

### Q1: 为什么不直接修改默认参数？
A: 默认参数是针对通用场景优化的，修改可能影响其他用户。建议通过命令行参数覆盖。

### Q2: 参数调太宽松会有什么问题？
A: 可能会产生更多误检（如将图案、噪点识别为文字），需要根据实际情况平衡。

### Q3: 为什么命令2不支持字符位置？
A: `tools/infer/predict_system.py` 是纯OCR工具，设计简单高效，不包含字符位置计算逻辑。

### Q4: 能否批量处理多张图片？
A: 可以，将 `--image_dir` 指向文件夹路径即可：
```bash
--image_dir="C:\your\image\folder"
```

## 总结

通过将宽松的检测参数应用到支持字符位置的predict_system.py，我们成功结合了两个命令的优势：
- ✅ 识别完整（包括"第二齣 俠概"等之前漏掉的文字）
- ✅ 支持字符级位置信息
- ✅ 保持高性能
- ✅ 适用于繁体中文古籍OCR

这个方案特别适合需要精确字符位置的应用场景，如：
- 古籍数字化
- 文档版面分析
- 字符级标注
- 文字动画制作


