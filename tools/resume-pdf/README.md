# 高清简历 PDF 生成器

这是当前简历的保真流程：PowerPoint 只负责按原页面渲染一张 600dpi PNG，PDF 则由独立脚本封装并添加可点击链接。它不使用 PowerPoint 的 PDF 导出器，因此不会触发其低清或深色特效兼容问题，同时保留原有字体、字距、排版、阴影和发光。

原生渲染脚本会按源幻灯片的尺寸输出，可复用于单页简历；当前的 `link_regions.json` 是这份简历的链接坐标。运行环境需要 Windows 和已安装的桌面版 PowerPoint。

## 使用

先安装 Python 依赖：

```powershell
pip install -r requirements.txt
```

渲染 600dpi 原生页面：

```powershell
powershell -ExecutionPolicy Bypass -File .\render_pptx_600dpi.ps1 -SourcePath "简历Resume.pptx" -OutputPath "resume-600dpi.png"
```

再封装带链接的 PDF：

```powershell
python package_linked_pdf.py --png "resume-600dpi.png" --pdf "蔡峤峰_高清简历.pdf" --dpi 600
python verify_output.py "蔡峤峰_高清简历.pdf"
```

`link_regions.json` 保存二维码和两段引导文字的 PDF 链接区域；版式变动后只需更新其中的坐标和目标地址。

