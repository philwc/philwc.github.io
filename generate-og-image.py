#!/usr/bin/env python3
"""Generate og-image.png from index.html content."""

import os
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from xml.sax.saxutils import escape as xml_escape

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(SCRIPT_DIR, "index.html")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "og-image.png")

BG = "#272822"
NAME_COLOR = "#F92672"
TEXT_COLOR = "#F8F8F2"
TECH_COLOR = "#AE81FF"
CERT_COLOR = "#A6E22E"
DOMAIN_COLOR = "#75715E"
DECO_LEFT = "#5c2238"
DECO_RIGHT = "#3e3e37"


class OGDataParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self._in_h1 = False
        self._in_h2 = False
        self._seen_h2_end = False
        self._p_after_h2 = 0
        self._in_highlight = None
        self._buf = ""
        self._h1_highlights = []
        self._h2_highlights = []
        self.name = ""
        self.title = ""
        self.tech = []
        self.trainer = ""
        self.domain = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "link" and a.get("rel") == "canonical":
            url = a.get("href", "")
            self.domain = (
                url.replace("https://", "").replace("http://", "").rstrip("/")
            )
        if tag == "h1":
            self._in_h1 = True
        elif tag == "h2":
            self._in_h2 = True
        elif tag == "p" and self._seen_h2_end:
            self._p_after_h2 += 1
        cls = a.get("class", "")
        if tag == "span":
            if "head-highlight" in cls:
                self._in_highlight = "head"
                self._buf = ""
            elif "tech-highlight" in cls:
                self._in_highlight = "tech"
                self._buf = ""
            elif "cert-highlight" in cls:
                self._in_highlight = "cert"
                self._buf = ""

    def handle_endtag(self, tag):
        if tag == "h1":
            self._in_h1 = False
        elif tag == "h2":
            self._in_h2 = False
            self._seen_h2_end = True
        if tag == "span" and self._in_highlight:
            text = " ".join(self._buf.split())
            if self._in_highlight == "head":
                if self._in_h1:
                    self._h1_highlights.append(text)
                elif self._in_h2:
                    self._h2_highlights.append(text)
            elif self._in_highlight == "tech":
                if self._p_after_h2 == 1 and text:
                    self.tech.append(text)
            elif self._in_highlight == "cert":
                if "trainer" in text.lower():
                    self.trainer = text
            self._in_highlight = None

    def handle_data(self, data):
        if self._in_highlight:
            self._buf += data

    def finalize(self):
        if len(self._h1_highlights) >= 2:
            self.name = self._h1_highlights[1]
        if self._h2_highlights:
            self.title = self._h2_highlights[0]


def parse_html():
    with open(HTML_PATH) as f:
        html = f.read()
    parser = OGDataParser()
    parser.feed(html)
    parser.finalize()
    return parser


def build_svg(data):
    name = xml_escape(data.name)
    title = xml_escape(data.title)
    tech_line = xml_escape(" · ".join(data.tech))
    trainer = xml_escape(data.trainer)
    domain = xml_escape(data.domain)

    return f"""\
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="{BG}"/>

  <g stroke="{DECO_LEFT}" stroke-width="8" stroke-linecap="round"
     stroke-linejoin="round" fill="none">
    <polyline points="35,230 -35,350 35,470"/>
    <line x1="65" y1="470" x2="105" y2="230"/>
    <polyline points="140,230 210,350 140,470"/>
  </g>

  <g stroke="{DECO_RIGHT}" stroke-width="8" stroke-linecap="round"
     stroke-linejoin="round" fill="none">
    <polyline points="1070,180 1015,275 1070,370"/>
    <line x1="1095" y1="370" x2="1130" y2="180"/>
    <polyline points="1160,180 1215,275 1160,370"/>
  </g>

  <text x="600" y="195" text-anchor="middle"
        font-family="sans-serif" font-weight="bold"
        font-size="64" fill="{NAME_COLOR}">{name}</text>

  <text x="600" y="275" text-anchor="middle"
        font-family="sans-serif"
        font-size="34" fill="{TEXT_COLOR}">{title}</text>

  <line x1="500" y1="315" x2="700" y2="315"
        stroke="{TECH_COLOR}" stroke-width="2"/>

  <text x="600" y="375" text-anchor="middle"
        font-family="sans-serif"
        font-size="22" fill="{TECH_COLOR}">{tech_line}</text>

  <text x="600" y="440" text-anchor="middle"
        font-family="sans-serif"
        font-size="22" fill="{CERT_COLOR}">{trainer}</text>

  <text x="600" y="565" text-anchor="middle"
        font-family="sans-serif"
        font-size="20" fill="{DOMAIN_COLOR}">{domain}</text>
</svg>"""


def main():
    data = parse_html()
    print(f"Name:    {data.name}")
    print(f"Title:   {data.title}")
    print(f"Tech:    {', '.join(data.tech)}")
    print(f"Trainer: {data.trainer}")
    print(f"Domain:  {data.domain}")

    svg = build_svg(data)

    rsvg = shutil.which("rsvg-convert") or "/opt/homebrew/bin/rsvg-convert"
    if not os.path.isfile(rsvg):
        print("Error: rsvg-convert not found. Install librsvg:", file=sys.stderr)
        print("  brew install librsvg", file=sys.stderr)
        sys.exit(1)

    with tempfile.NamedTemporaryFile(suffix=".svg", mode="w", delete=False) as f:
        f.write(svg)
        svg_path = f.name

    try:
        subprocess.run([rsvg, svg_path, "-o", OUTPUT_PATH], check=True)
        print(f"\nGenerated {OUTPUT_PATH}")
    finally:
        os.unlink(svg_path)


if __name__ == "__main__":
    main()
