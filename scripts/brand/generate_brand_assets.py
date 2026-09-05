"""Generate the web-ready AI BOS brand assets from the approved source logo.

Usage:
    python scripts/brand/generate_brand_assets.py [path/to/logo.png]

The source artwork has a translucent navy background. The extraction below only
changes background transparency; it does not redraw or recolour the artwork.
"""

from pathlib import Path
import shutil
import sys

from PIL import Image, ImageChops, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads" / "logo.png"
OUTPUT = ROOT / "ai-bos-frontend" / "public" / "brand"
SOURCE_ARCHIVE = ROOT / "brand" / "source"


def foreground_alpha(image: Image.Image) -> Image.Image:
    """Remove the dark navy field with a soft, anti-aliased luminance mask."""
    rgb = image.convert("RGB")
    red, green, blue = rgb.split()
    brightest = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    # Pixels <= 52 are background; pixels >= 92 retain full opacity.
    alpha = brightest.point(lambda value: max(0, min(255, round((value - 52) * 255 / 40))))
    return alpha.filter(ImageFilter.GaussianBlur(0.45))


def extract(box: tuple[int, int, int, int], clear_boxes: tuple[tuple[int, int, int, int], ...] = ()) -> Image.Image:
    image = Image.open(SOURCE).convert("RGBA").crop(box)
    alpha = foreground_alpha(image)
    for left, top, right, bottom in clear_boxes:
        alpha.paste(0, (left - box[0], top - box[1], right - box[0], bottom - box[1]))
    image.putalpha(alpha)
    bounds = alpha.getbbox()
    if bounds is None:
        raise RuntimeError("No foreground was detected in the requested logo crop")
    padded = (
        max(0, bounds[0] - 8),
        max(0, bounds[1] - 8),
        min(image.width, bounds[2] + 8),
        min(image.height, bounds[3] + 8),
    )
    return image.crop(padded)


def contain(image: Image.Image, size: tuple[int, int], padding: int) -> Image.Image:
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    available = (size[0] - padding * 2, size[1] - padding * 2)
    fitted = image.copy()
    fitted.thumbnail(available, Image.Resampling.LANCZOS)
    canvas.alpha_composite(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
    return canvas


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Logo source not found: {SOURCE}")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    SOURCE_ARCHIVE.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, SOURCE_ARCHIVE / "ai-bos-logo-source.png")

    icon = extract((330, 145, 790, 550))
    # Preserve the complete symbol while hiding the two text rows.
    wordmark = extract((330, 145, 1790, 550), ((780, 365, 1790, 550),))
    # Keep BUSINESS OPERATING SYSTEM, remove only the lower marketing strapline.
    full = extract((330, 145, 1790, 550), ((780, 435, 1790, 550),))
    hero = extract((330, 145, 1790, 550))

    variants = {"icon": icon, "wordmark": wordmark, "full": full, "hero": hero}
    for name, image in variants.items():
        image.save(OUTPUT / f"ai-bos-{name}.png", optimize=True)
        image.save(OUTPUT / f"ai-bos-{name}.webp", "WEBP", lossless=True, method=6)

    for size in (16, 32, 192, 512):
        favicon = contain(icon, (size, size), max(1, round(size * 0.08)))
        favicon.save(OUTPUT / f"favicon-{size}x{size}.png", optimize=True)
    contain(icon, (64, 64), 5).save(
        OUTPUT.parent / "favicon.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64)],
    )

    original = Image.open(SOURCE).convert("RGBA")
    backdrop = Image.new("RGB", (1200, 630), "#060b1c")
    fitted = original.copy()
    fitted.thumbnail((1120, 520), Image.Resampling.LANCZOS)
    backdrop.paste(fitted, ((1200 - fitted.width) // 2, (630 - fitted.height) // 2), fitted)
    backdrop.save(OUTPUT / "ai-bos-og.png", optimize=True)

    for name, image in variants.items():
        print(f"{name:8} {image.width}x{image.height}")


if __name__ == "__main__":
    main()
