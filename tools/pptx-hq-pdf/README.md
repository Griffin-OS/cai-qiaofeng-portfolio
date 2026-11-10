# PPTX → 高清、可点击的单页 PDF

将 PowerPoint 演示文稿的指定页导出成 **可选中文字、尽量保持矢量图形与原始图片质量、保留超链接** 的 PDF。适用于单页简历、作品集、海报和其他 PPT 设计作品。

> 本目录只保存通用方法和脚本，**不包含任何个人简历、电话号码或私有源文件**。

## 方案总览

\`\`\`text
.pptx 原文件
   │
   ├── 1. 原生高质量 PDF 导出（首选 Windows PowerPoint）
   │       PowerPoint ExportAsFixedFormat → PDF, Intent=Print
   │       或 LibreOffice --headless（跨平台备选；有排版风险）
   │
   ├── 2. PyMuPDF 提取指定页（如第 2 页）
   │       不截图、不重新压缩整页、不重新排版正文
   │
   ├── 3. python-pptx 读取超链接
   │       读取文字 run 链接、图片/形状 click_action
   │       处理 group shape 坐标到页面坐标的转换
   │
   ├── 4. PyMuPDF 补上 PDF /Link 注释
   │       透明可点击区域，保留底层矢量/图片
   │
   └── 5. 导出检查
           页数 = 1、文字可选择、二维码可扫码、链接有效、
           图片与字体清晰、没有错行/遮挡/越界
\`\`\`

## 运行环境

- Python 3.10+
- \`pip install pymupdf python-pptx\`
- **Windows（推荐）**：安装 Microsoft PowerPoint，以及 \`pip install pywin32\`
- **Linux / macOS（备选）**：安装 LibreOffice，且 \`libreoffice\` 或 \`soffice\` 可在命令行调用

## 使用方法

\`\`\`bash
python export_pptx_page.py "简历Resume.pptx" --slide 2 --out "resume_en_page2.pdf"
\`\`\`

脚本默认只导出第 **2 页**。也可以通过 \`--slide 1\` 选择第1页。

## 为什么优先用 PowerPoint 导出？

PowerPoint 的 PDF **Print Intent** 通常对 Office 特有文本布局、嵌入字体和图形显示更准确。它会保留可矢量化的文字/图形，而不是把整张幻灯片转成位图。

LibreOffice 的 PDF 导出同样支持可检索文本，但当 PPTX 使用 **嵌入的特殊字体（如阿里巴巴普惠体、钉钉进步体）**、文本框自动适应、组合形状时，字体替换可能引起**加粗、换行、重叠、裁切**。这种情况要先在临时副本中修正字体与自动适应设置，然后重新导出与目视复核；不要因此修改原始 PPTX。

## 补回超链接的原理

PowerPoint 的图片、文本和形状链接可能存储在 PPTX 的关系与 drawing XML 中。脚本通过 \`python-pptx\` 读取这些链接及形状边界；按幻灯片尺寸换算到 PDF 坐标后，由 \`PyMuPDF\` 添加透明 URI Link 注释。不覆盖文字，不重绘页面。

**注意**：复杂旋转/剪裁的组合形状需人工检查链接点击范围；PDF 自带链接可能已经正确，无需重复覆盖。二维码图像仍然需要编码正确 URL，PDF 注释只能解决“鼠标点击”，不能修复二维码图案内容。

## 交付前必做检查

1. 用 \`pdfinfo\` 或 PDF 阅读器确认只有 1 页、尺寸正确。
2. 放大到 200%–400%，检查标题、正文行距、字重、段落边界，尤其是小字号正文与状态标签。
3. 尝试选中并复制几段文字（确认不是整页截图）。
4. 用手机扫描二维码，且鼠标点击二维码/“Learn More”等超链接都能打开正确网址。
5. 如与 PPT 原生界面不一致，**以 Windows PowerPoint 导出的原生高质量 PDF 为准**；不要把有错版的 LibreOffice PDF 当成高清最终版。

## 本次简历实例（2026-11）

原演示稿包含中英文两页，此次仅导出了第2页英文简历。由于运行环境没有 Windows PowerPoint，采用 **LibreOffice PDF + 临时字体/文本框兼容性调整 + PyMuPDF 单页提取与链接补全**。输出 PDF 的文字可选择，作品集链接可点击。为避免侵犯隐私，**PDF 文件和源 PPTX 未上传到此公开仓库**。

本脚本为可复用通用流程，具体简历中采用的兼容性微调（字体替换与微调标题字号）是针对版式的人工修复，不能保证每份 PPTX 都能自动完成。
