# PPTX to high-quality, clickable single-page PDF

Export a chosen PowerPoint slide as a **searchable, vector-first PDF** while retaining the original layout and web links. This workflow suits a one-page resume, portfolio, poster, or other PowerPoint-designed document.

> This folder contains only the reusable method and code. It does **not** contain a resume, phone number, or private source file.

## Design rule

Treat the supplied PPTX page as the visual source of truth. Do not “repair” a bad conversion by changing text-box coordinates, changing the body weight, or regrouping shapes. First export with Windows PowerPoint; only edit a PPTX when the same defect is visible in PowerPoint itself.

## Export paths

```text
PPTX source
  |
  +-- Preferred: Windows PowerPoint native single-slide PDF
  |     ExportAsFixedFormat, Print intent, requested slide range
  |     Preserves PowerPoint font/layout decisions and vector text
  |
  +-- Validate the native PDF
  |     1 page, selectable text, original links, high-resolution render
  |
  +-- Supplement missing URI links only when necessary
  |     Adds a transparent link annotation; never redraws or rasterizes page content
  |
  +-- Explicit fallback: LibreOffice
        Requires --allow-libreoffice-fallback
        Render and compare against the PowerPoint source before delivery
```

On Windows, the script asks PowerPoint to export the requested slide range directly. It does **not** export the whole deck and then rebuild the selected page. PowerPoint documents the required `ExportAsFixedFormat` range arguments and the `ppPrintSlideRange` value in its [PDF export reference](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.presentation.exportasfixedformat) and [range enumeration](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.ppprintrangetype).

## Requirements

- Python 3.10+
- `pip install pymupdf python-pptx`
- **Windows, recommended:** Microsoft PowerPoint and `pip install pywin32`
- **Only for fallback:** LibreOffice or soffice available on `PATH`

## Usage

Export the second slide with native PowerPoint:

```bash
python export_pptx_page.py "resume.pptx" --slide 2 --out "resume_en_page2.pdf"
```

A missing or failed PowerPoint installation stops the command by default. If you intentionally accept the LibreOffice fallback, opt in explicitly:

```bash
python export_pptx_page.py "resume.pptx" --slide 2 --out "resume_en_page2.pdf" --allow-libreoffice-fallback
```

Use `--skip-link-repair` only when the native output already contains every required web link and you do not want the script to add any missing PDF link annotations.

## Link handling

PowerPoint generally preserves links on text, shapes, and images. The script checks the output first. It reads PPTX hyperlinks from text runs, clickable shapes, and nested groups, then adds only link annotations absent from the PDF. It never paints over text, changes slide geometry, or converts the page to an image.

Complex rotated or cropped group objects can have an imprecise clickable rectangle. Test those links manually. A PDF annotation does not change the URL encoded into a QR code, so scan the QR code separately.

## Required visual checks

1. Confirm there is exactly one PDF page and that its size matches the source slide.
2. Render the PDF at 200% to 400% and compare it side by side with the PowerPoint source.
3. Check contact information left edges, small text, title spacing, labels, and QR-code captions.
4. Check state labels such as `In Progress` for both overlap and consistent spacing.
5. Select and copy several lines of text. The result must not be a full-page image.
6. Click each web link and scan any QR code.
7. When using the LibreOffice fallback, reject any font substitution, unexpected bold text, wrapping change, clipping, or label collision. Do not modify the source PPTX merely to hide the fallback defect.

## Why LibreOffice is opt-in

PPTX files can embed fonts and rely on PowerPoint-specific text fitting, groups, and drawing behavior. LibreOffice may substitute a font or calculate line widths differently, causing alignment changes, bold-looking text, line wrapping, label overlap, or clipping. The fallback can still be useful on Linux or macOS, but it needs visual approval against the original PowerPoint view.

## Validation reported by the script

After the output is written, the script reopens it and reports:

- one-page status;
- count of searchable text characters;
- total PDF links;
- number of missing links it added.

For final delivery, also inspect a high-resolution render. A structural check alone cannot prove the design matches the original visual layout.

## 2026-11 validation note

The current method was verified with a two-page resume that embeds Alibaba PuHuiTi, DingTalk JinBuTi, and Microsoft YaHei fonts. PowerPoint directly exported the selected English slide as a one-page PDF. The PDF retained selectable text and the original three portfolio hyperlinks; no coordinate or font-weight edits to the PPTX were required.
