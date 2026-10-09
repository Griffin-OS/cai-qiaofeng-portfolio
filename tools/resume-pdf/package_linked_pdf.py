"""Wrap a native 600dpi PowerPoint slide render in a PDF with live link regions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


DEFAULT_LINKS = Path(__file__).with_name("link_regions.json")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--png", required=True)
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--links", default=str(DEFAULT_LINKS))
    parser.add_argument("--dpi", default=600, type=float)
    args = parser.parse_args()

    png = Path(args.png).resolve()
    pdf = Path(args.pdf).resolve()
    links = json.loads(Path(args.links).read_text(encoding="utf-8"))
    if not png.is_file():
        raise FileNotFoundError(png)
    if args.dpi <= 0:
        raise ValueError("--dpi must be greater than zero")

    pdf.parent.mkdir(parents=True, exist_ok=True)
    image = ImageReader(str(png))
    pixel_w, pixel_h = image.getSize()
    page_w = pixel_w / args.dpi * 72
    page_h = pixel_h / args.dpi * 72
    document = canvas.Canvas(str(pdf), pagesize=(page_w, page_h), pageCompression=1)
    document.setTitle("蔡峤峰｜简历")
    document.setAuthor("蔡峤峰")
    document.drawImage(image, 0, 0, width=page_w, height=page_h, mask="auto")
    for link in links:
        x, top, width, height = link["x"], link["y_top"], link["width"], link["height"]
        document.linkURL(link["url"], (x, page_h - top - height, x + width, page_h - top), relative=0, thickness=0)
    document.showPage()
    document.save()
    print("Created PDF successfully")


if __name__ == "__main__":
    main()
