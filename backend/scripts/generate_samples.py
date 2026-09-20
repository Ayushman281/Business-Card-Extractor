"""Generate fictional evaluation images on an explicitly selected hosted server."""
import argparse
import json
from pathlib import Path
from hosted_guard import add_hosted_argument, require_hosted

from PIL import Image, ImageDraw, ImageFont


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_hosted_argument(parser)
    parser.add_argument("--output", type=Path, default=Path("/tmp/evaluation"))
    args = parser.parse_args()
    require_hosted(args.cloud_target)
    args.output.mkdir(parents=True, exist_ok=True)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_path, 34)
    title = ImageFont.truetype(font_path, 54)
    examples = [
        ("standard.png", ["Avery Morgan", "Account Director", "Fictional North Studio", "London, United Kingdom", "+44 20 7946 0000", "avery@example.com"],
         dict(first_name="Avery", last_name="Morgan", job_title="Account Director", company="Fictional North Studio", location="London, United Kingdom", phone="+44 20 7946 0000", email="avery@example.com")),
        ("missing-fields.png", ["Jamie Chen", "Product Designer", "Fictional Paperworks", "", "", "jamie@example.org"],
         dict(first_name="Jamie", last_name="Chen", job_title="Product Designer", company="Fictional Paperworks", location=None, phone=None, email="jamie@example.org")),
        ("rotated.png", ["Riya Shah", "Sales Manager", "Fictional Cedar Labs", "Mumbai, India", "+91 22 0000 0000", "riya@example.net"],
         dict(first_name="Riya", last_name="Shah", job_title="Sales Manager", company="Fictional Cedar Labs", location="Mumbai, India", phone="+91 22 0000 0000", email="riya@example.net")),
    ]
    truth = {}
    for index, (filename, lines, expected) in enumerate(examples):
        card = Image.new("RGB", (1200, 720), "#f6f3ed" if index != 1 else "#183d36")
        ink = "#163d36" if index != 1 else "#ffffff"
        draw = ImageDraw.Draw(card)
        draw.rectangle((60, 70, 70, 620), fill="#91ae73")
        for line_index, line in enumerate(lines):
            draw.text((110, 85 + line_index * 86), line, font=title if line_index == 0 else font, fill=ink)
        if filename == "rotated.png":
            card = card.rotate(90, expand=True)
        card.save(args.output / filename)
        truth[filename] = expected
    (args.output / "corrupt.jpg").write_bytes(b"This is deliberately not an image.")
    (args.output / "expected.json").write_text(json.dumps(truth, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
