# PP-OCRv5 模型适配指南

## 问题概述

PP-OCRv5 新模型使用 PaddleX 格式（`.yml` + `.pdiparams`），与当前 PaddleOCR 推理代码不兼容。

**错误信息：**
```
ValueError: (InvalidArgument) Not find predictor_id 1 and pass_name memory_optimize_pass
```

---

## 解决方案

### 方案1：使用 PaddleX SDK（推荐，最简单）

#### 步骤1：安装 PaddleX

```bash
pip install paddlex
```

#### 步骤2：修改代码使用 PaddleX API

创建新文件 `predict_system_v5.py`:

```python
from paddlex import create_model
import cv2

# 加载检测模型
det_model = create_model("PP-OCRv5_server_det")
det_model.load("inference/new-version/PP-OCRv5_server_det_infer")

# 加载识别模型
rec_model = create_model("PP-OCRv5_server_rec")
rec_model.load("inference/new-version/PP-OCRv5_server_rec_infer")

# 读取图片
img = cv2.imread("test_image.jpg")

# 检测
det_result = det_model.predict(img)

# 识别
for box in det_result['boxes']:
    crop_img = crop_image(img, box)  # 需要实现裁剪函数
    rec_result = rec_model.predict(crop_img)
    print(rec_result)
```

**优点：**
- 简单，无需修改模型文件
- 官方支持，稳定可靠
- 一行代码加载模型

**缺点：**
- 需要学习新的API
- 可能需要重写部分业务代码

---

### 方案2：转换模型格式

#### 步骤1：安装转换工具

```bash
pip install paddle2paddle
```

#### 步骤2：转换模型

```python
import paddle
from paddle.static import load_inference_model

# 读取 PaddleX 格式模型
with open('inference/new-version/PP-OCRv5_server_det_infer/inference.yml', 'r') as f:
    config = yaml.load(f)

# 加载模型
predictor = create_predictor_from_yml(config, 
    model_dir='inference/new-version/PP-OCRv5_server_det_infer')

# 保存为传统格式
paddle.jit.save(predictor, 'inference/PP-OCRv5_server_det_converted')
```

**注意：** 这个方案需要深入理解 PaddleX 和 Paddle 的模型格式，实现较复杂。

---

### 方案3：升级 PaddlePaddle 和推理代码

#### 步骤1：升级依赖

```bash
# 升级 PaddlePaddle 到最新版本
pip install --upgrade paddlepaddle

# 或GPU版本
pip install --upgrade paddlepaddle-gpu
```

#### 步骤2：修改 `tools/infer/utility.py`

在 `create_predictor` 函数中添加对 `.yml` 格式的支持：

```python
def create_predictor(args, mode, logger):
    model_dir = get_model_dir(args, mode)
    
    # 检查是否为 PaddleX 格式
    yml_path = os.path.join(model_dir, "inference.yml")
    if os.path.exists(yml_path):
        # 使用 PaddleX 加载逻辑
        return create_paddlex_predictor(yml_path, model_dir)
    else:
        # 使用传统加载逻辑
        return create_paddle_predictor(model_dir, args, mode)

def create_paddlex_predictor(yml_path, model_dir):
    """加载 PaddleX 格式模型"""
    import yaml
    with open(yml_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # 根据config创建predictor
    # 这里需要实现具体的加载逻辑
    ...
```

**优点：**
- 一次修改，长期受益
- 同时支持新旧格式

**缺点：**
- 改动较大，需要深入理解代码
- 需要充分测试

---

## 快速验证方案

### 使用 Python 直接测试模型

创建测试脚本 `test_v5_model.py`:

```python
import paddle
from paddle import inference
import yaml
import numpy as np
import cv2

def load_yml_config(yml_path):
    with open(yml_path, 'r') as f:
        return yaml.safe_load(f)

def create_predictor_from_yml(model_dir):
    """尝试加载 PaddleX 格式模型"""
    yml_path = f"{model_dir}/inference.yml"
    config = load_yml_config(yml_path)
    
    # 创建推理配置
    infer_config = inference.Config(
        f"{model_dir}/inference.pdiparams",
        f"{model_dir}/inference.yml"
    )
    
    infer_config.disable_gpu()
    infer_config.enable_memory_optim()
    
    try:
        predictor = inference.create_predictor(infer_config)
        return predictor, config
    except Exception as e:
        print(f"加载失败: {e}")
        return None, None

# 测试检测模型
print("测试检测模型...")
det_predictor, det_config = create_predictor_from_yml(
    "inference/new-version/PP-OCRv5_server_det_infer"
)

if det_predictor:
    print("✓ 检测模型加载成功")
else:
    print("✗ 检测模型加载失败")

# 测试识别模型
print("测试识别模型...")
rec_predictor, rec_config = create_predictor_from_yml(
    "inference/new-version/PP-OCRv5_server_rec_infer"
)

if rec_predictor:
    print("✓ 识别模型加载成功")
else:
    print("✗ 识别模型加载失败")
```

运行测试：
```bash
python test_v5_model.py
```

---

## 推荐实施计划

### 阶段1：快速验证（1-2天）

1. 安装 PaddleX SDK
2. 运行测试脚本验证模型可用性
3. 编写简单的示例代码

### 阶段2：API 封装（3-5天）

1. 封装 PaddleX 调用接口
2. 保持与现有代码的兼容性
3. 编写单元测试

### 阶段3：集成测试（1周）

1. 在现有系统中集成新模型
2. 批量测试准确率和性能
3. 对比新旧模型效果

### 阶段4：性能优化（1周）

1. GPU 推理优化
2. 批处理优化
3. 内存优化

### 阶段5：生产部署（2-4周）

1. 灰度发布（10%流量）
2. 监控关键指标
3. 逐步扩大到100%

**总时间：6-8周**

---

## 常见问题

### Q1: 为什么新模型使用不同格式？

A: PP-OCRv5 是 PaddleX 生态的一部分，使用统一的模型格式以便于管理和部署。`.yml` 格式包含了更多的元信息和配置，便于自动化工具解析。

### Q2: 旧模型还能继续使用吗？

A: 可以。PP-OCRv3 仍然稳定可靠，在大多数场景下表现优秀。如果当前性能满足需求，可以继续使用。

### Q3: 适配新模型的投入产出比如何？

A: 
- **投入：** 1-2个月开发+测试时间
- **收益：** 识别准确率提升3-5%，长期技术升级
- **建议：** 如果当前准确率<90%，值得投入；如果>95%，可以推迟

### Q4: 有没有官方的迁移指南？

A: PaddleX 官方文档中有模型迁移指南，建议查阅：
- https://github.com/PaddlePaddle/PaddleX
- https://paddlex-doc.readthedocs.io/

---

## 联系支持

如果在适配过程中遇到问题：

1. **查看官方文档：** https://github.com/PaddlePaddle/PaddleOCR
2. **提交 Issue：** https://github.com/PaddlePaddle/PaddleOCR/issues
3. **加入社区群：** 扫描官方文档中的二维码

---

## 附录：完整示例代码

### 使用 PaddleX 的完整 OCR 示例

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PP-OCRv5 完整示例
使用 PaddleX SDK
"""

try:
    from paddlex import create_pipeline
    HAS_PADDLEX = True
except ImportError:
    HAS_PADDLEX = False
    print("警告: PaddleX 未安装，请运行: pip install paddlex")

import cv2
import json

def ocr_with_paddlex(image_path):
    """使用 PaddleX 进行 OCR 识别"""
    
    if not HAS_PADDLEX:
        return None
    
    # 创建 OCR pipeline
    ocr_pipeline = create_pipeline(
        task="OCR",
        det_model="PP-OCRv5_server_det",
        rec_model="PP-OCRv5_server_rec",
        det_model_dir="inference/new-version/PP-OCRv5_server_det_infer",
        rec_model_dir="inference/new-version/PP-OCRv5_server_rec_infer",
    )
    
    # 预测
    result = ocr_pipeline.predict(image_path)
    
    return result

def main():
    image_path = "test_image.jpg"
    
    print("开始 OCR 识别...")
    result = ocr_with_paddlex(image_path)
    
    if result:
        print(f"识别完成！共识别 {len(result['texts'])} 行文本")
        
        # 保存结果
        with open("ocr_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 打印部分结果
        for i, text in enumerate(result['texts'][:5]):
            print(f"{i+1}. {text['text']} (置信度: {text['confidence']:.2f})")
    else:
        print("识别失败")

if __name__ == "__main__":
    main()
```

---

**文档版本：** v1.0  
**最后更新：** 2025年12月5日  
**作者：** PaddleOCR Team  

