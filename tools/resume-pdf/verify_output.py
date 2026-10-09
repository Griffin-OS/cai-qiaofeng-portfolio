"""Quick structural verification for a generated resume PDF."""
from __future__ import annotations

import sys
from pathlib import Path

from pypdf import PdfReader


pdf = Path(sys.argv[1]).resolve()
reader = PdfReader(pdf)
page = reader.pages[0]
annotations = page.get("/Annots", [])
uris = [item.get_object().get("/A", {}).get("/URI") for item in annotations]
print(f"pages={len(reader.pages)}")
print(f"page_size={float(page.mediabox.width):.0f}x{float(page.mediabox.height):.0f}pt")
print(f"clickable_links={len(uris)}")
for uri in uris:
    print(uri)
