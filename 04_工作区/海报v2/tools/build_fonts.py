"""Subset the poster fonts to the characters actually used.

Full fonts go in fonts-src/ (git-ignored):
  Noto Serif SC / Noto Sans SC  https://github.com/notofonts/noto-cjk (SubsetOTF/SC)
  IBM Plex Mono                 https://github.com/google/fonts/tree/main/ofl/ibmplexmono
Run: python3 tools/build_fonts.py   (needs fonttools + brotli)
"""

import string
from pathlib import Path

from fontTools import subset

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "fonts-src"
OUT = ROOT / "src" / "assets" / "fonts"

FONTS = {
    "serif-400": "NotoSerifSC-Regular.otf",
    "serif-700": "NotoSerifSC-Bold.otf",
    "serif-900": "NotoSerifSC-Black.otf",
    "sans-400": "NotoSansSC-Regular.otf",
    "sans-500": "NotoSansSC-Medium.otf",
    "sans-700": "NotoSansSC-Bold.otf",
    "mono-400": "IBMPlexMono-Regular.ttf",
    "mono-500": "IBMPlexMono-Medium.ttf",
}


def used_text() -> str:
    text = string.printable + "，。、；：？！“”‘’（）《》【】—…·×㎡→–"
    for path in (ROOT / "src").glob("*.*"):
        if path.suffix in {".html", ".js", ".css"}:
            text += path.read_text(encoding="utf-8")
    return "".join(sorted(set(text)))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    text = used_text()
    for name, file in FONTS.items():
        options = subset.Options()
        options.flavor = "woff2"
        options.layout_features = ["*"]
        options.name_IDs = ["*"]
        font = subset.load_font(str(SRC / file), options)
        sub = subset.Subsetter(options)
        sub.populate(text=text)
        sub.subset(font)
        target = OUT / f"{name}.woff2"
        subset.save_font(font, str(target), options)
        print(f"{target.name:16} {target.stat().st_size / 1024:7.1f} KB")


if __name__ == "__main__":
    main()
