#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "nuclear>=2.10.0",
# ]
# ///
from nuclear import nuke
from pathlib import Path

class Config:
    dry: bool = False
    gray: bool = False

config, sh = nuke.init(Config)

def guide():
    gray_flag = '--gray' if config.gray else ''
    sh<<f'python scripts/rubik/gen_rubik_guide.py --guide {gray_flag} --output docs/rubik-for-dummies/assets'

def pdf():
    guide()
    root = Path('docs/rubik-for-dummies').resolve()
    html = root / 'guide.html'
    pdf_path = root / 'rubik_guide.pdf'
    sh << f'google-chrome --headless --disable-gpu --no-pdf-header-footer --print-to-pdf="{pdf_path}" "file://{html}"'
