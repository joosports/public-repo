from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "tse-long-tin-player-profile.html"
IMAGE_DIRECTORY = ROOT / "img" / "tse-long-tin"
IMAGE_NAME = re.compile(r"^tse-long-tin-[a-z0-9]+(?:-[a-z0-9]+)*\.(?:jpg|png)$")


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


def main() -> int:
    errors: list[str] = []

    parser = ProfileParser()
    parser.feed(PROFILE.read_text(encoding="utf-8"))

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
