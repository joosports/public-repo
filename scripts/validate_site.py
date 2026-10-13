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
        self.languages: dict[str, dict[str, int]] = {}
        self.current_language: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())

        if tag == "main" and attributes.get("id") in ("profile-en", "profile-ja"):
            language = attributes.get("lang")
            if language:
                self.current_language = language
                self.languages.setdefault(language, {"pages": 0, "photos": 0})

        if tag == "section" and "joosports-page" in classes:
            self.page_count += 1
            if self.current_language:
                self.languages[self.current_language]["pages"] += 1
        if tag == "a" and "data-lightbox" in attributes:
            self.lightbox_count += 1
            if self.current_language:
                self.languages[self.current_language]["photos"] += 1

        for attribute in ("src", "href"):
            value = attributes.get(attribute)
            if value:
                self.references.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag == "main":
            self.current_language = None


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

    if set(parser.languages) != {"en", "ja"}:
        errors.append("Expected separate English and Japanese profile sections")
    for language, counts in parser.languages.items():
        if counts["pages"] != 4:
            errors.append(f"Expected 4 printable pages in {language}, found {counts['pages']}")
        if counts["photos"] != 11:
            errors.append(f"Expected 11 lightbox photos in {language}, found {counts['photos']}")
    if parser.page_count != 8 or parser.lightbox_count != 22:
        errors.append("Expected 8 page sections and 22 photo links across both languages")

    representative_sections = re.findall(r'<section class="section representative">(.*?)</section>', profile_source, re.DOTALL)
    if len(representative_sections) != 2:
        errors.append("Expected representative experience in both languages")
    for section in representative_sections:
        seasons = [section.find(season) for season in ("2026–27", "2025–26", "2023–24")]
        if any(index < 0 for index in seasons) or seasons != sorted(seasons):
            errors.append("Representative seasons are not sorted newest to oldest")

    club_sections = re.findall(r'<section class="section match-record">(.*?)</section>', profile_source, re.DOTALL)
    expected_teams = (["Kitchee SC U16", "Kitchee SC U16", "Kitchee SC U14"], ["傑志SC U-16", "傑志SC U-16", "傑志SC U-14"])
    if len(club_sections) != 2:
        errors.append("Expected club match records in both languages")
    for section, expected in zip(club_sections, expected_teams):
        teams = re.findall(r"<td>(Kitchee SC U\d+|傑志SC U-\d+)</td>", section)
        if teams != expected:
            errors.append("Club records do not list the older age team first within a season")

    training_sections = re.findall(r'<section class="section training">(.*?)</section>', profile_source, re.DOTALL)
    training_labels = (("Hong Kong Representative Team", "Kitchee Sports Club", "School Football"), ("香港年代別代表", "傑志SC", "学校サッカー"))
    if len(training_sections) != 2:
        errors.append("Expected training exposure in both languages")
    for section, labels in zip(training_sections, training_labels):
        order = [section.find(label) for label in labels]
        if any(index < 0 for index in order) or order != sorted(order):
            errors.append("Training exposure is not ordered representative team, club, then school")

    for required in ("ツェ・ロンティン", "センターバック／ボランチ", "継続的に先発出場"):
        if required not in profile_source:
            errors.append(f"Required professional Japanese wording is missing: {required}")

    for forbidden in ("守備的ミッドフィールダー", "レギュラー登録", "成長・育成プロフィール"):
        if forbidden in profile_source:
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
            if schema.get("url") != PROFILE_URL or schema.get("inLanguage") != ["en", "ja"]:
                errors.append("Structured data must use the main profile URL and both languages")
        except json.JSONDecodeError as error:
            errors.append(f"Structured data is invalid JSON: {error}")

    if errors:
        print("Site validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"Site validation passed: 4 pages and 11 lightbox photos per language (English/Japanese), "
        f"{len(image_files)} named images."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
