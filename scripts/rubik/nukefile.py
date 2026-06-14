#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "nuclear>=2.10.0",
# ]
# ///
from nuclear import nuke

class Config:
    dry: bool = False

config, sh = nuke.init(Config)

def guide():
    sh<<'python scripts/rubik/gen_rubik_guide.py --guide --output docs/rubik-for-dummies/assets'
