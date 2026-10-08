from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
WIDTH = 1200
HEIGHT = 630
ORANGE = "#f37021"
INK = "#11171d"
MUTED = "#aab3bc"


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    candidates = {
        "regular": [
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ],
        "semibold": [
            Path("C:/Windows/Fonts/seguisb.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ],
        "bold": [
            Path("C:/Windows/Fonts/seguibl.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ],
        "japanese": [
            Path("C:/Windows/Fonts/YuGothB.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
        ],
    }
    for path in candidates[name]:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    raise FileNotFoundError(f"No suitable {name} font found")


def gradient_background() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), INK)
    pixels = image.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            mix = (x / WIDTH) * 0.7 + (y / HEIGHT) * 0.3
            pixels[x, y] = (
                int(13 + 16 * mix),
                int(19 + 14 * mix),
                int(25 + 14 * mix),
            )
    return image


def transparent_logo() -> Image.Image:
    letterhead = Image.open(ROOT / "assets" / "joosports-letterhead.png").convert("RGBA")
    logo = letterhead.crop((105, 82, 340, 252))
    pixels = logo.load()
    for y in range(logo.height):
        for x in range(logo.width):
            red, green, blue, _ = pixels[x, y]
            alpha = max(0, min(255, round((255 - min(red, green, blue)) * 1.3)))
            pixels[x, y] = (243, 112, 33, alpha)
    return logo


def player_portrait() -> Image.Image:
    source = Image.open(
        ROOT / "img" / "tse-long-tin" / "tse-long-tin-headshot.png"
    ).convert("RGB")
    portrait = source.resize((430, 430), Image.Resampling.LANCZOS)
    mask = Image.new("L", portrait.size, 0)
    ImageDraw.Draw(mask).ellipse((3, 3, 427, 427), fill=255)
    portrait.putalpha(mask)
    return portrait


def rounded_label(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    label_font: ImageFont.FreeTypeFont,
) -> int:
    box = draw.textbbox((0, 0), text, font=label_font)
    width = box[2] - box[0] + 34
    draw.rounded_rectangle((x, y, x + width, y + 42), radius=21, outline="#48515a", width=2)
    draw.text((x + 17, y + 9), text, fill="#f4f6f8", font=label_font)
    return width


def main() -> None:
    image = gradient_background().convert("RGBA")
    draw = ImageDraw.Draw(image)

    # Strong JOOSPORTS framing and understated pitch-inspired details.
    draw.rectangle((0, 0, WIDTH, 12), fill=ORANGE)
    draw.rectangle((0, HEIGHT - 14, WIDTH, HEIGHT), fill=ORANGE)
    draw.polygon(((1120, 0), (1200, 0), (1200, 230), (1162, 180)), fill=ORANGE)
    draw.arc((710, 48, 1210, 548), 105, 255, fill="#39434c", width=2)
    draw.line((709, 94, 709, 540), fill="#303942", width=2)

    logo = transparent_logo()
    logo.thumbnail((180, 130), Image.Resampling.LANCZOS)
    image.alpha_composite(logo, (70, 42))

    # Portrait shadow, ring, and image.
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse((720, 91, 1176, 547), fill=(0, 0, 0, 180))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    image.alpha_composite(shadow)
    draw = ImageDraw.Draw(image)
    draw.ellipse((717, 88, 1173, 544), fill="#f7f8f9")
    draw.ellipse((725, 96, 1165, 536), fill=ORANGE)
    image.alpha_composite(player_portrait(), (730, 101))

    eyebrow = font("semibold", 21)
    name_font = font("bold", 66)
    chinese_font = font("japanese", 38)
    position_font = font("semibold", 23)
    label_font = font("semibold", 16)
    footer_font = font("regular", 16)

    draw.text((72, 176), "FOOTBALL PLAYER PROFILE", fill=ORANGE, font=eyebrow)
    draw.text((68, 216), "TSE LONG TIN", fill="#ffffff", font=name_font)
    draw.text((72, 304), "謝朗天", fill="#d7dde2", font=chinese_font)
    draw.rectangle((72, 367, 126, 372), fill=ORANGE)
    draw.text(
        (72, 391),
        "CENTRE BACK  /  DEFENSIVE MIDFIELDER",
        fill="#e8ecef",
        font=position_font,
    )

    first_width = rounded_label(draw, 72, 449, "HONG KONG U15", label_font)
    rounded_label(draw, 72 + first_width + 12, 449, "KITCHEE U16", label_font)

    draw.line((72, 548, 668, 548), fill="#3b444d", width=2)
    draw.text(
        (72, 564),
        "JOOSPORTS  ·  INTERNATIONAL FOOTBALL DEVELOPMENT",
        fill=MUTED,
        font=footer_font,
    )

    output = ROOT / "assets" / "tse-long-tin-social-preview.png"
    image.convert("RGB").save(output, "PNG", optimize=True)
    print(f"Created {output.relative_to(ROOT)} ({WIDTH}×{HEIGHT})")


if __name__ == "__main__":
    main()
