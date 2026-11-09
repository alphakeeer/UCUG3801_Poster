"""Crop and tone the field photos used on the poster.

Sources live in 02_现场/照片/. Outputs go to src/assets/.
Run: python3 tools/prepare_photos.py  (needs Pillow)
"""

from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PHOTOS = ROOT.parents[1] / "02_现场" / "照片"
OUT = ROOT / "src" / "assets"


def tone(img: Image.Image, contrast: float, brightness: float) -> Image.Image:
    """Warm monochrome: grey scale, then map black→ink and white→paper."""
    grey = ImageOps.grayscale(img)
    grey = ImageEnhance.Contrast(grey).enhance(contrast)
    grey = ImageEnhance.Brightness(grey).enhance(brightness)
    return ImageOps.colorize(grey, black="#0f1012", white="#f3eee4", mid="#7d7972")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # Hero: eaves framing the skyscraper (F04). Keep the full frame.
    hero = Image.open(PHOTOS / "F04_檐下框景超高层.jpg")
    hero = tone(hero, contrast=1.18, brightness=1.04)
    hero.save(OUT / "hero.jpg", quality=88, optimize=True, progressive=True)

    # Sculpture group "安居乐业" (F01). Crop away the passer-by on the left,
    # keeping only the statues and the inscription.
    sculpture = Image.open(PHOTOS / "F01_安居乐业雕塑墙.jpg")
    sculpture = sculpture.crop((690, 560, 1790, 1140))
    sculpture = tone(sculpture, contrast=1.12, brightness=1.02)
    sculpture.save(OUT / "sculpture.jpg", quality=88, optimize=True, progressive=True)

    print("photos ->", OUT)


if __name__ == "__main__":
    main()
