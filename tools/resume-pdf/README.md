# 高清简历 PDF 生成器

这是当前简历版式的自定义渲染流程，不调用 PowerPoint 的 PDF 导出器。

它会从 PPTX 中读取原始 PNG 与版式清单，在 600dpi 画布上合成文字、阴影、发光和图片，再把无损页面写入 PDF，同时保留二维码及 “Learn More” 的可点击链接。

## 使用

先安装依赖：

```powershell
pip install -r requirements.txt
```

然后执行：

```powershell
python build_highres_resume.py --source "简历Resume.pptx" --pdf "蔡峤峰_高清简历.pdf"
```

默认会同时生成一个同名 PNG 中间稿，用于检查清晰度；需要指定位置时可加 `--png`。默认输出为 600dpi，也可用 `--dpi 300` 先快速预览。

## 版式说明

`templates/cai_qiaofeng_resume_manifest.json` 是当前简历版式的源级绘制清单。它适用于这份单页简历的同一结构；如果以后大改 PPT 的形状、分组或链接位置，应同步更新清单后再生成。

