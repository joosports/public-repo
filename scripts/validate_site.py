from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "tse-long-tin-player-profile.html"
INDEX = ROOT / "index.html"
IMAGE_DIRECTORY = ROOT / "img" / "tse-long-tin"
IMAGE_NAME = re.compile(r"^tse-long-tin-[a-z0-9]+(?:-[a-z0-9]+)*\.(?:jpg|png)$")
PREVIEW = ROOT / "assets" / "tse-long-tin-social-preview.png"
PROFILE_URL = "https://joosports.github.io/public-repo/tse-long-tin-player-profile.html"
PREVIEW_URL = "https://joosports.github.io/public-repo/assets/tse-long-tin-social-preview.png"


class ProfileParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []
        self.page_count = 0
        self.lightbox_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())

        if tag == "section" and "joosports-page" in classes:
            self.page_count += 1
        if tag == "a" and "data-lightbox" in attributes:
            self.lightbox_count += 1

        for attribute in ("src", "href"):
            value = attributes.get(attribute)
            if value:
                self.references.append(value)


def local_path(reference: str) -> Path | None:
    parsed = urlsplit(reference)
    if parsed.scheme or parsed.netloc or reference.startswith(("#", "mailto:", "tel:")):
        return None
    return ROOT / unquote(parsed.path)


def png_dimensions(path: Path) -> tuple[int, int] | None:
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")


def main() -> int:
    errors: list[str] = []
    profile_source = PROFILE.read_text(encoding="utf-8")
    index_source = INDEX.read_text(encoding="utf-8")
    language_source = (ROOT / "assets" / "tse-long-tin-profile.js").read_text(encoding="utf-8")

    parser = ProfileParser()
    parser.feed(profile_source)

    for reference in parser.references:
        path = local_path(reference)
        if path is not None and not path.exists():
            errors.append(f"Missing local reference: {reference}")

    image_files = [path for path in IMAGE_DIRECTORY.iterdir() if path.is_file()]
    for image in image_files:
        if not IMAGE_NAME.fullmatch(image.name):
            errors.append(f"Image does not follow naming convention: {image.name}")

    if parser.page_count != 4:
        errors.append(f"Expected 4 printable pages, found {parser.page_count}")
    if parser.lightbox_count != 11:
        errors.append(f"Expected 11 lightbox photos, found {parser.lightbox_count}")

    representative_section = profile_source.partition("<h2>Representative Experience</h2>")[2].partition("<h2>Club Honours</h2>")[0]
    representative_seasons = [representative_section.find(season) for season in ("2026–27", "2025–26", "2023–24")]
    if any(index < 0 for index in representative_seasons) or representative_seasons != sorted(representative_seasons):
        errors.append("Representative seasons are not sorted newest to oldest")

    club_section = profile_source.partition("<h2>Documented Club Record</h2>")[2].partition("</section>")[0]
    club_teams = re.findall(r"<td>(Kitchee U\d+)</td>", club_section)
    if club_teams != ["Kitchee U16", "Kitchee U16", "Kitchee U14"]:
        errors.append("Club records do not list the older age team first within a season")

    training_section = profile_source.partition("<h2>Typical Training Exposure</h2>")[2].partition("</section>")[0]
    training_order = [training_section.find(label) for label in ("Hong Kong Team", "Club (Kitchee)", "Junior High School")]
    if any(index < 0 for index in training_order) or training_order != sorted(training_order):
        errors.append("Training exposure is not ordered Hong Kong, club, then junior high school")

    combined_source = profile_source + language_source
    for forbidden in ("(DBS)", "（DBS）", "JHS"):
        if forbidden in combined_source:
            errors.append(f"Deprecated wording remains: {forbidden}")

    for required in ("ツェ・ロンティン", "センターバック／ボランチ", "主力メンバー／先発出場"):
        if required not in language_source:
            errors.append(f"Required professional Japanese wording is missing: {required}")

    for forbidden in ("守備的ミッドフィールダー", "レギュラー登録", "成長・育成プロフィール"):
        if forbidden in language_source:
            errors.append(f"Literal Japanese wording remains: {forbidden}")

    required_metadata = (
        '<meta property="og:type" content="profile">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<link rel="canonical" href="{PROFILE_URL}">',
        f'<meta property="og:image" content="{PREVIEW_URL}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
    )
    for markup in required_metadata:
        if markup not in profile_source:
            errors.append(f"Profile metadata is missing: {markup}")
        if markup not in index_source:
            errors.append(f"Index metadata is missing: {markup}")

    if not PREVIEW.exists():
        errors.append("Social preview image is missing")
    elif png_dimensions(PREVIEW) != (1200, 630):
        errors.append(f"Social preview must be 1200×630, found {png_dimensions(PREVIEW)}")

    structured_data = re.search(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        profile_source,
        re.DOTALL,
    )
    if structured_data is None:
        errors.append("ProfilePage structured data is missing")
    else:
        try:
            schema = json.loads(structured_data.group(1))
            if schema.get("@type") != "ProfilePage" or schema.get("mainEntity", {}).get("@type") != "Person":
                errors.append("Structured data must describe a ProfilePage with a Person main entity")
        except json.JSONDecodeError as error:
            errors.append(f"Structured data is invalid JSON: {error}")

    if errors:
        print("Site validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"Site validation passed: {parser.page_count} pages, "
        f"{parser.lightbox_count} lightbox photos, {len(image_files)} named images."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
