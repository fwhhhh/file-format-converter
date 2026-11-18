"""Generate the application icon (requires Pillow)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


def build_icon() -> Image.Image:
    size = 256
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle([8, 8, size - 8, size - 8], radius=52, fill=(37, 99, 235, 255))
    white = (255, 255, 255, 255)
    draw.line([(66, 100), (182, 100)], fill=white, width=16)
    draw.polygon([(202, 100), (172, 80), (172, 120)], fill=white)
    draw.line([(190, 156), (74, 156)], fill=white, width=16)
    draw.polygon([(54, 156), (84, 136), (84, 176)], fill=white)
    return image


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    assets = root / "assets"
    assets.mkdir(exist_ok=True)
    image = build_icon()
    image.save(assets / "app.png")
    image.save(
        assets / "app.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"Wrote {assets / 'app.ico'} and {assets / 'app.png'}")


if __name__ == "__main__":
    main()
