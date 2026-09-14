#!/usr/bin/env python3
"""Generate llms.txt from index.html content."""

import json
import os
import re
from html.parser import HTMLParser

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(SCRIPT_DIR, "index.html")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "llms.txt")


class SiteDataParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self._in_h1 = False
        self._in_h2 = False
        self._seen_h2_end = False
        self._p_after_h2 = 0
        self._in_p = False
        self._in_highlight = None
        self._in_jsonld = False
        self._buf = ""
        self._p_buf = ""
        self._h1_highlights = []
        self._h2_highlights = []
        self.name = ""
        self.title = ""
        self.employer = ""
        self.primary_tech = []
        self.additional_tech = []
        self.trainer = ""
        self.trainer_url = ""
        self.domain = ""
        self.jsonld = {}
        self._cert_href = ""
        self._contact_links = []
        self._in_contact = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)

        if tag == "link" and a.get("rel") == "canonical":
            url = a.get("href", "")
            self.domain = url.replace("https://", "").replace("http://", "").rstrip("/")

        if tag == "script" and a.get("type") == "application/ld+json":
            self._in_jsonld = True
            self._buf = ""

        if tag == "ul" and a.get("id") == "contact":
            self._in_contact = True

        if self._in_contact and tag == "a":
            href = a.get("href", "")
            title = a.get("title", "")
            if href and title:
                self._contact_links.append({"title": title, "href": href})

        if tag == "h1":
            self._in_h1 = True
        elif tag == "h2":
            self._in_h2 = True
        elif tag == "p":
            if self._seen_h2_end:
                self._p_after_h2 += 1
            self._in_p = True
            self._p_buf = ""

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
                self._cert_href = ""

        if self._in_highlight == "cert" and tag == "a":
            self._cert_href = a.get("href", "")

    def handle_endtag(self, tag):
        if tag == "h1":
            self._in_h1 = False
        elif tag == "h2":
            self._in_h2 = False
            self._seen_h2_end = True
        elif tag == "p":
            self._in_p = False
        elif tag == "ul":
            self._in_contact = False

        if tag == "script" and self._in_jsonld:
            self._in_jsonld = False
            try:
                self.jsonld = json.loads(self._buf)
            except json.JSONDecodeError:
                pass

        if tag == "span" and self._in_highlight:
            text = " ".join(self._buf.split())
            if self._in_highlight == "head":
                if self._in_h1:
                    self._h1_highlights.append(text)
                elif self._in_h2:
                    self._h2_highlights.append(text)
            elif self._in_highlight == "tech":
                if self._p_after_h2 == 1 and text:
                    self.primary_tech.append(text)
                elif self._p_after_h2 > 1 and text:
                    self.additional_tech.append(text)
            elif self._in_highlight == "cert":
                if "trainer" in text.lower():
                    self.trainer = text
                    self.trainer_url = self._cert_href
            self._in_highlight = None

    def handle_data(self, data):
        if self._in_jsonld:
            self._buf += data
        elif self._in_highlight:
            self._buf += data
        if self._in_p:
            self._p_buf += data

    def finalize(self):
        if len(self._h1_highlights) >= 2:
            self.name = self._h1_highlights[1]
        if self._h2_highlights:
            self.title = self._h2_highlights[0]
        if len(self._h2_highlights) >= 2:
            self.employer = self._h2_highlights[1]


def parse_html():
    with open(HTML_PATH) as f:
        html = f.read()
    parser = SiteDataParser()
    parser.feed(html)
    parser.finalize()
    return parser


def build_llms_txt(data):
    lines = []
    ld = data.jsonld

    lines.append(f"# {data.name}")
    lines.append("")

    summary = f"> {data.title} at {data.employer}."
    if data.trainer:
        summary = summary.rstrip(".") + f". {data.trainer}."
    lines.append(summary)
    lines.append("")

    desc = f"{data.name} is a {data.title} working at {data.employer}."
    if data.primary_tech:
        tech_list = ", ".join(data.primary_tech[:-1]) + f", and {data.primary_tech[-1]}" if len(data.primary_tech) > 1 else data.primary_tech[0]
        desc += f" Specialising in {tech_list}."
    lines.append(desc)
    lines.append("")

    creds = ld.get("hasCredential", [])
    if creds:
        lines.append("## Certifications")
        lines.append("")
        for c in creds:
            name = c.get("name", "")
            url = c.get("url", "")
            if url:
                lines.append(f"- [{name}]({url})")
            else:
                lines.append(f"- {name}")
        if data.trainer:
            if data.trainer_url:
                lines.append(f"- [{data.trainer}]({data.trainer_url})")
            else:
                lines.append(f"- {data.trainer}")
        lines.append("")

    if data.primary_tech or data.additional_tech:
        lines.append("## Technologies")
        lines.append("")
        if data.primary_tech:
            lines.append(f"Primary: {', '.join(data.primary_tech)}")
        if data.additional_tech:
            lines.append(f"Additional: {', '.join(data.additional_tech)}")
        lines.append("")

    same_as = ld.get("sameAs", [])
    contact_links = data._contact_links
    if same_as or contact_links:
        lines.append("## Links")
        lines.append("")
        url = ld.get("url", f"https://{data.domain}")
        lines.append(f"- Website: {url}")
        for link in contact_links:
            title = link["title"]
            href = link["href"]
            if href.startswith("mailto:") or href.startswith("tel:"):
                continue
            lines.append(f"- {title}: {href}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main():
    data = parse_html()
    print(f"Name:     {data.name}")
    print(f"Title:    {data.title}")
    print(f"Employer: {data.employer}")
    print(f"Tech:     {', '.join(data.primary_tech)}")
    print(f"Domain:   {data.domain}")

    content = build_llms_txt(data)
    with open(OUTPUT_PATH, "w") as f:
        f.write(content)

    print(f"\nGenerated {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
