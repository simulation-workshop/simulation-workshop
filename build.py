#!/usr/bin/env python3
"""
mdsite - a small, mkdocs-style static site generator.

    python build.py build [-c site.yml] [--strict]
    python build.py serve [-c site.yml] [-p 8000]

You write Markdown files under docs/ and describe the navigation in site.yml.
The generator converts every page with a predefined theme (theme/) and gives you:

  * multi-page navigation (sidebar, breadcrumbs, prev/next, per-page TOC)
  * client-side search (works offline, even from file://)
  * light / dark mode
  * includes and embeds directives (see docs/guide/embedding.md)
  * internal .md links rewritten to the right .html URLs
  * a dev server that rebuilds and reloads the browser on every change

Requires: markdown, pyyaml, jinja2, pygments
"""
from __future__ import annotations

import argparse
import functools
import html
import http.server
import json
import posixpath
import re
import shlex
import shutil
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urlparse

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from markdown.treeprocessors import Treeprocessor
from markupsafe import Markup
from pygments import highlight as pyg_highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.styles import get_all_styles
from pygments.util import ClassNotFound

SCRIPT_DIR = Path(__file__).resolve().parent

DEFAULTS = {
    "site_name": "Documentation",
    "site_description": "",
    "site_url": "",
    "language": "en",
    "docs_dir": "docs",
    "site_dir": "site",
    "use_directory_urls": False,  # False -> guide/page.html (works from file://)
    "repo_url": "",
    "edit_uri": "",  # e.g. "edit/main/docs/"
    "copyright": "",
    "show_updated": False,
    "exclude_docs": [],  # extra glob patterns; ".*" and "_*" are always excluded
    "nav": None,  # None -> generated from the folder structure
    "extra_css": [],
    "extra_javascript": [],
    "markdown_extensions": [],
    "theme": {
        "dir": None,
        "primary": "#00796b",
        "primary_dark": "#3ddbc0",
        "default_mode": "auto",  # auto | light | dark
        "code_light": "xcode",
        "code_dark": "github-dark",
        "expand_all": False,
        "fonts": True,  # load Bricolage Grotesque + Geist from Google Fonts; false = system fonts only
        "logo": "",  # optional image inside docs/, shown next to the site name
    },
}

MD_SUFFIXES = (".md", ".markdown")
COLOR_RE = re.compile(r"^(#[0-9a-fA-F]{3,8}|[a-zA-Z]+|(rgb|hsl)a?\([\d\s.,%/]+\))$")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = v
    return out


INLINE_TAG_RE = re.compile(r"</?(?:span|code|a|em|strong|b|i|kbd|abbr|mark|sup|sub)(?:\s[^>]*)?>")


def strip_tags(s: str) -> str:
    s = INLINE_TAG_RE.sub("", s)  # inline markup must not split words or code tokens
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s).replace("¶", " ")
    return re.sub(r"\s+", " ", s).strip()


def contrast_text(color: str, light: str = "#ffffff", dark: str = "#06120f") -> str:
    """Pick readable text for a button filled with `color` (hex only; else white)."""
    m = re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", str(color).strip())
    if not m:
        return light
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    chan = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in chan]
    lum = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    return dark if lum > 0.179 else light


def prettify(name: str) -> str:
    return re.sub(r"[-_]+", " ", name).strip().title()


FRONT_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)


def split_front_matter(text: str) -> tuple[dict, str]:
    m = FRONT_RE.match(text)
    if not m:
        return {}, text
    try:
        meta = yaml.safe_load(m.group(1)) or {}
        if not isinstance(meta, dict):
            meta = {}
    except yaml.YAMLError:
        meta = {}
    return meta, text[m.end():]


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass(eq=False)
class Page:
    src: str  # path relative to docs_dir, posix
    meta: dict
    body: str
    mtime: float
    title: str = ""
    html: str = ""
    toc: list = field(default_factory=list)
    out: str = ""  # output file relative to site_dir
    out_dir: str = ""
    url: str = ""  # site-root-relative URL
    has_h1: bool = False
    uses_mermaid: bool = False
    breadcrumbs: list = field(default_factory=list)


@dataclass(eq=False)
class NavItem:
    title: str
    page: Page | None = None
    url: str | None = None  # external link
    children: list = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Markdown extension: includes, embeds, mermaid, link rewriting
# --------------------------------------------------------------------------- #
FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*([\w+-]*)")
CLOSE_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*$")
INCLUDE_RE = re.compile(r"^(\s*)(?:\{%\s*include\s+(.+?)\s*%\}|--8<--\s+(.+?))\s*$")
EMBED_RE = re.compile(r"^(\s*)\{%\s*embed\s+(.+?)\s*%\}\s*$")

YT_RE = re.compile(r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|embed/|shorts/|live/)|youtu\.be/)([\w-]{11})")
VIMEO_RE = re.compile(r"vimeo\.com/(?:video/)?(\d+)")
CODEPEN_RE = re.compile(r"codepen\.io/([\w-]+)/(?:pen|full|embed)/([\w-]+)")
VIDEO_EXT = {".mp4", ".webm", ".ogv", ".mov", ".m4v"}
AUDIO_EXT = {".mp3", ".wav", ".ogg", ".m4a", ".flac"}
LANG_MAP = {".py": "python", ".js": "javascript", ".ts": "typescript", ".sh": "bash",
            ".yml": "yaml", ".yaml": "yaml", ".md": "markdown", ".rs": "rust",
            ".rb": "ruby", ".kt": "kotlin", ".htm": "html"}
TEXT_INCLUDE = {".md", ".markdown", ".txt"}
RATIO_RE = re.compile(r"^\d+(\.\d+)?\s*/\s*\d+(\.\d+)?$")
SIZE_RE = re.compile(r"^\d+(\.\d+)?(px|vh|rem|em|%)?$")


def esc(s: str) -> str:
    return html.escape(s, quote=True)


class DirectivePreprocessor(Preprocessor):
    """Handles directives that sit on a line of their own:

        {% include "path" [lines="3-10"] [lang="python"] %}   (also: --8<-- "path")
        {% embed "url" [title=".."] [ratio="16/9"] [height="480"] [caption=".."] %}
        ```mermaid ... ```

    Anything inside a fenced code block is left alone, so you can document the syntax.
    """

    def __init__(self, md, site: "Site", page: Page):
        super().__init__(md)
        self.site = site
        self.page = page

    def run(self, lines):
        base = (self.site.docs_dir / self.page.src).parent
        return self.process(lines, 0, base)

    def stash(self, markup: str, indent: str = "") -> list[str]:
        return ["", indent + self.md.htmlStash.store(markup), ""]

    def process(self, lines, depth, base_dir):
        out: list[str] = []
        fence = None
        i = 0
        while i < len(lines):
            line = lines[i]
            if fence:
                out.append(line)
                m = CLOSE_RE.match(line)
                if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1]:
                    fence = None
                i += 1
                continue

            m = FENCE_RE.match(line)
            if m:
                marks, lang = m.group(2), m.group(3).lower()
                if lang == "mermaid":
                    j, body = i + 1, []
                    while j < len(lines) and not CLOSE_RE.match(lines[j]):
                        body.append(lines[j])
                        j += 1
                    self.page.uses_mermaid = True
                    out += self.stash(f'<pre class="mermaid">{esc(chr(10).join(body))}</pre>', m.group(1))
                    i = j + 1
                    continue
                fence = (marks[0], len(marks))
                out.append(line)
                i += 1
                continue

            m = INCLUDE_RE.match(line)
            if m:
                out += self.include(m.group(2) or m.group(3), m.group(1), depth, base_dir)
                i += 1
                continue

            m = EMBED_RE.match(line)
            if m:
                out += self.stash(self.embed(m.group(2)), m.group(1))
                i += 1
                continue

            out.append(line)
            i += 1
        return out

    # ----- include ---------------------------------------------------------
    def include(self, argstr, indent, depth, base_dir):
        try:
            tokens = shlex.split(argstr)
        except ValueError as exc:
            self.site.warn(f"{self.page.src}: bad include arguments ({exc})")
            return self.stash('<p class="mdsite-error">Bad include directive</p>', indent)
        if not tokens:
            return []
        ref, opts = tokens[0], dict(t.split("=", 1) for t in tokens[1:] if "=" in t)
        path = self.site.find_file(ref, base_dir)
        if path is None:
            self.site.warn(f"{self.page.src}: include not found: {ref}")
            return self.stash(f'<p class="mdsite-error">Include not found: <code>{esc(ref)}</code></p>', indent)
        if depth >= 5:
            self.site.warn(f"{self.page.src}: includes nested too deeply at {ref}")
            return []

        text = path.read_text(encoding="utf-8")
        suffix = path.suffix.lower()
        if suffix in TEXT_INCLUDE:
            _, text = split_front_matter(text)
            lines = text.splitlines()
            lines = self.select_lines(lines, opts.get("lines"))
            lines = self.process(lines, depth + 1, path.parent)
        else:
            lines = self.select_lines(text.splitlines(), opts.get("lines"))
            lang = opts.get("lang") or LANG_MAP.get(suffix, suffix.lstrip("."))
            ticks = "`" * max(3, max((len(x) for x in re.findall(r"`+", text)), default=0) + 1)
            lines = [f"{ticks}{lang}", *lines, ticks]
        return [(indent + l) if l.strip() else l for l in lines]

    @staticmethod
    def select_lines(lines, spec):
        if not spec:
            return lines
        m = re.fullmatch(r"(\d*)(-?)(\d*)", spec.strip())
        if not m or not (m.group(1) or m.group(3)):
            return lines
        start = int(m.group(1) or 1)
        end = int(m.group(3)) if m.group(3) else (len(lines) if m.group(2) else start)
        return lines[max(start - 1, 0):end]

    # ----- embed -----------------------------------------------------------
    def embed(self, argstr) -> str:
        err = lambda msg: f'<p class="mdsite-error">{esc(msg)}</p>'
        try:
            tokens = shlex.split(argstr)
        except ValueError as exc:
            self.site.warn(f"{self.page.src}: bad embed arguments ({exc})")
            return err("Bad embed directive")
        if not tokens:
            return err("Empty embed directive")
        url, opts = tokens[0], dict(t.split("=", 1) for t in tokens[1:] if "=" in t)
        title, caption = opts.get("title", "Embedded content"), opts.get("caption", "")
        ratio, height = opts.get("ratio"), opts.get("height")
        kind, src, default = "iframe", url, {"ratio": "16/9"}

        if m := YT_RE.search(url):
            src = f"https://www.youtube-nocookie.com/embed/{m.group(1)}"
        elif m := VIMEO_RE.search(url):
            src = f"https://player.vimeo.com/video/{m.group(1)}"
        elif m := CODEPEN_RE.search(url):
            src = f"https://codepen.io/{m.group(1)}/embed/{m.group(2)}?default-tab=result"
        else:
            parsed = urlparse(url)
            ext = posixpath.splitext(parsed.path)[1].lower()
            if parsed.scheme in ("http", "https"):
                src = url
            elif parsed.scheme or parsed.netloc:
                self.site.warn(f"{self.page.src}: embed URL scheme not allowed: {url}")
                return err(f"Embed URL not allowed: {url}")
            else:
                src = self.site.local_href(self.page, parsed.path, what="embed")
                if parsed.query:
                    src += "?" + parsed.query
                if parsed.fragment:
                    src += "#" + parsed.fragment
            if ext in VIDEO_EXT:
                kind = "video"
            elif ext in AUDIO_EXT:
                kind = "audio"
            elif ext == ".pdf":
                default = {"height": "640px"}
            elif ext in (".html", ".htm"):
                default = {"height": "480px"}

        if ratio and not RATIO_RE.match(ratio):
            ratio = None
        if height and SIZE_RE.match(height):
            height = height if not height.isdigit() else f"{height}px"
        else:
            height = None
        if height:
            style = f"height:{height}"
        elif ratio:
            style = f"aspect-ratio:{ratio}"
        elif "height" in default:
            style = f"height:{default['height']}"
        else:
            style = f"aspect-ratio:{default['ratio']}"

        if kind == "audio":
            media = f'<audio controls preload="metadata" src="{esc(src)}"></audio>'
        elif kind == "video":
            media = (f'<div class="embed-frame" style="{style}">'
                     f'<video controls preload="metadata" src="{esc(src)}"></video></div>')
        else:
            media = (f'<div class="embed-frame" style="{style}"><iframe src="{esc(src)}" title="{esc(title)}" '
                     f'loading="lazy" allowfullscreen referrerpolicy="strict-origin-when-cross-origin" '
                     f'allow="encrypted-media; picture-in-picture; fullscreen"></iframe></div>')
        cap = f"<figcaption>{esc(caption)}</figcaption>" if caption else ""
        return f'<figure class="embed">{media}{cap}</figure>'


class LinkTreeprocessor(Treeprocessor):
    """Rewrites relative links/images so .md links point at the generated pages."""

    ATTRS = {"a": "href", "img": "src", "source": "src", "video": "src", "audio": "src"}

    def __init__(self, md, site: "Site", page: Page):
        super().__init__(md)
        self.site, self.page = site, page

    def run(self, root):
        for el in root.iter():
            attr = self.ATTRS.get(el.tag)
            if not attr or not el.get(attr):
                continue
            new = self.site.resolve_link(self.page, el.get(attr))
            if new:
                el.set(attr, new)


class SiteExtension(Extension):
    def __init__(self, site: "Site", page: Page):
        super().__init__()
        self.site, self.page = site, page

    def extendMarkdown(self, md):
        md.preprocessors.register(DirectivePreprocessor(md, self.site, self.page), "mdsite_directives", 28)
        md.treeprocessors.register(LinkTreeprocessor(md, self.site, self.page), "mdsite_links", 4)


# --------------------------------------------------------------------------- #
# The site
# --------------------------------------------------------------------------- #
class Site:
    def __init__(self, config_path: Path, dev: bool = False):
        self.config_path = config_path.resolve()
        self.root = self.config_path.parent
        self.dev = dev
        self.warnings = 0
        raw = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
        self.cfg = merge(DEFAULTS, raw)
        self.cfg["site_url"] = str(self.cfg["site_url"]).rstrip("/")
        self.docs_dir = (self.root / self.cfg["docs_dir"]).resolve()
        self.site_dir = (self.root / self.cfg["site_dir"]).resolve()

        theme = self.cfg["theme"]
        if theme.get("dir"):
            self.theme_dir = (self.root / theme["dir"]).resolve()
        elif (self.root / "theme").is_dir():
            self.theme_dir = (self.root / "theme").resolve()
        else:
            self.theme_dir = SCRIPT_DIR / "theme"
        for key, fallback in (("primary", DEFAULTS["theme"]["primary"]),
                              ("primary_dark", DEFAULTS["theme"]["primary_dark"])):
            if not COLOR_RE.match(str(theme[key])):
                self.warn(f"theme.{key}: '{theme[key]}' is not a valid color, using {fallback}")
                theme[key] = fallback

        if not self.docs_dir.is_dir():
            raise SystemExit(f"error: docs_dir not found: {self.docs_dir}")
        if (self.site_dir in (self.root, self.docs_dir) or self.site_dir in self.root.parents
                or self.site_dir in self.docs_dir.parents or self.docs_dir in self.site_dir.parents):
            raise SystemExit(f"error: site_dir ({self.site_dir}) must be a separate folder, "
                             "not the project, docs folder, or inside docs")

    # ----- logging ---------------------------------------------------------
    def warn(self, msg: str):
        self.warnings += 1
        print(f"WARNING  {msg}", file=sys.stderr)

    # ----- collecting ------------------------------------------------------
    def excluded(self, rel: str) -> bool:
        patterns = [".*", "_*", *self.cfg["exclude_docs"]]
        parts = rel.split("/")
        return any(fnmatch(p, pat) for pat in patterns for p in parts) or \
            any(fnmatch(rel, pat) for pat in self.cfg["exclude_docs"])

    def out_for(self, src: str) -> str:
        p = PurePosixPath(src)
        if p.stem == "index":
            return (p.parent / "index.html").as_posix()
        base = p.with_suffix("").as_posix()
        return f"{base}/index.html" if self.cfg["use_directory_urls"] else f"{base}.html"

    def collect(self):
        self.pages: list[Page] = []
        self.pages_by_src: dict[str, Page] = {}
        self.assets: list[str] = []
        for path in sorted(self.docs_dir.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(self.docs_dir).as_posix()
            if self.excluded(rel):
                continue
            if path.suffix.lower() in MD_SUFFIXES:
                meta, body = split_front_matter(path.read_text(encoding="utf-8"))
                page = Page(src=rel, meta=meta, body=body, mtime=path.stat().st_mtime)
                page.out = self.out_for(rel)
                page.out_dir = posixpath.dirname(page.out)
                page.url = (page.out_dir + "/" if page.out_dir else "") if (
                    self.cfg["use_directory_urls"] and page.out.endswith("/index.html")) else page.out
                self.pages.append(page)
                self.pages_by_src[rel] = page
            else:
                self.assets.append(rel)
        if not self.pages:
            raise SystemExit(f"error: no markdown files found in {self.docs_dir}")

    # ----- URLs ------------------------------------------------------------
    def page_href(self, frm: Page, to: Page) -> str:
        if self.cfg["use_directory_urls"]:
            rel = posixpath.relpath(to.out_dir or ".", frm.out_dir or ".")
            return "./" if rel == "." else rel + "/"
        return posixpath.relpath(to.out, frm.out_dir or ".")

    def root_path(self, page: Page) -> str:
        rel = posixpath.relpath(".", page.out_dir or ".")
        return "" if rel == "." else rel + "/"

    def asset_href(self, page: Page, target: str) -> str:
        return quote(posixpath.relpath(target, page.out_dir or "."), safe="/")

    def find_file(self, ref: str, base_dir: Path) -> Path | None:
        for cand in (base_dir / ref, self.docs_dir / ref):
            cand = cand.resolve()
            if cand.is_file() and cand.is_relative_to(self.root):
                return cand
        return None

    def local_href(self, page: Page, path: str, what: str = "link") -> str:
        path = unquote(path)
        if path.startswith("/"):
            target = posixpath.normpath(path.lstrip("/"))
        else:
            target = posixpath.normpath(posixpath.join(posixpath.dirname(page.src), path))
        if target.startswith("..") or not (self.docs_dir / target).exists():
            self.warn(f"{page.src}: {what} target not found: {path}")
        return self.asset_href(page, target)

    def resolve_link(self, page: Page, url: str) -> str | None:
        p = urlparse(url)
        if p.scheme or p.netloc or not p.path:
            return None  # external, mailto:, or #fragment only
        path = unquote(p.path)
        if path.startswith("/"):
            target = posixpath.normpath(path.lstrip("/"))
        else:
            target = posixpath.normpath(posixpath.join(posixpath.dirname(page.src), path))
        if target.startswith(".."):
            self.warn(f"{page.src}: link leaves the docs folder: {url}")
            return None
        if target.lower().endswith(MD_SUFFIXES):
            dest = self.pages_by_src.get(target)
            if dest is None:
                self.warn(f"{page.src}: link to unknown page: {url}")
                return None
            href = self.page_href(page, dest)
        else:
            if (self.docs_dir / target).is_dir():
                return None
            if not (self.docs_dir / target).exists():
                self.warn(f"{page.src}: link target not found: {url}")
                return None
            href = self.asset_href(page, target)
        if p.query:
            href += "?" + p.query
        if p.fragment:
            href += "#" + p.fragment
        return href

    # ----- converting ------------------------------------------------------
    def convert(self, page: Page):
        extensions: list = ["extra", "admonition", "sane_lists", "toc", "codehilite", SiteExtension(self, page)]
        configs = {
            "toc": {"permalink": True, "permalink_title": "Permanent link", "toc_depth": "1-4"},
            "codehilite": {"css_class": "highlight", "guess_lang": False},
        }
        for ext in self.cfg["markdown_extensions"]:
            if isinstance(ext, str):
                extensions.append(ext)
            elif isinstance(ext, dict):
                for name, conf in ext.items():
                    extensions.append(name)
                    if conf:
                        configs[name] = conf
        md = markdown.Markdown(extensions=extensions, extension_configs=configs)
        page.html = md.convert(page.body)
        tokens = getattr(md, "toc_tokens", [])
        page.has_h1 = any(t["level"] == 1 for t in tokens)

        def flatten(items, depth=0):
            out = []
            for t in items:
                if t["level"] == 1:
                    out += flatten(t["children"], depth)
                elif t["level"] <= 3:
                    out.append({"name": html.unescape(t["name"]), "id": t["id"], "children": flatten(t["children"], depth + 1)})
            return out

        page.toc = flatten(tokens)
        h1 = next((html.unescape(t["name"]) for t in tokens if t["level"] == 1), None)
        if page.meta.get("title"):
            page.title = str(page.meta["title"])
        elif h1:
            page.title = h1
        elif PurePosixPath(page.src).stem == "index":
            parent = PurePosixPath(page.src).parent.name
            page.title = prettify(parent) if parent else "Home"
        else:
            page.title = prettify(PurePosixPath(page.src).stem)

    # ----- navigation ------------------------------------------------------
    def build_nav(self):
        nav = self.cfg.get("nav")
        self.nav = self.parse_nav(nav) if nav else self.auto_nav()
        self.nav_pages: list[Page] = []

        def walk(items, trail):
            for it in items:
                if it.page:
                    it.page.breadcrumbs = list(trail)
                    self.nav_pages.append(it.page)
                walk(it.children, trail + [it.title])

        walk(self.nav, [])
        self.home = self.pages_by_src.get("index.md") or (self.nav_pages[0] if self.nav_pages else self.pages[0])

    def _leaf(self, title, ref):
        ref = str(ref)
        if re.match(r"^[a-z][a-z0-9+.-]*://", ref, re.I):
            return NavItem(title=title or ref, url=ref)
        target = posixpath.normpath(ref)
        page = self.pages_by_src.get(target)
        if page is None:
            self.warn(f"nav: page not found: {ref}")
            return None
        return NavItem(title=title or page.title, page=page)

    def parse_nav(self, entries):
        items = []
        for entry in entries:
            if isinstance(entry, str):
                item = self._leaf(None, entry)
                if item:
                    items.append(item)
            elif isinstance(entry, dict):
                for title, val in entry.items():
                    if isinstance(val, list):
                        items.append(NavItem(title=str(title), children=self.parse_nav(val)))
                    else:
                        item = self._leaf(str(title), val)
                        if item:
                            items.append(item)
        return items

    def auto_nav(self):
        def build(folder: str):
            prefix = folder + "/" if folder else ""
            files, dirs = [], set()
            for p in self.pages:
                if not p.src.startswith(prefix):
                    continue
                rest = p.src[len(prefix):]
                if "/" in rest:
                    dirs.add(rest.split("/", 1)[0])
                else:
                    files.append(p)
            files.sort(key=lambda p: (PurePosixPath(p.src).stem != "index", p.src))
            items = [NavItem(title=p.title, page=p) for p in files]
            for d in sorted(dirs):
                items.append(NavItem(title=prettify(d), children=build(prefix + d)))
            return items

        return build("")

    def nav_for(self, page: Page) -> list[dict]:
        def conv(item: NavItem) -> dict:
            if item.children:
                kids = [conv(c) for c in item.children]
                return {"title": item.title, "children": kids, "href": None, "active": False,
                        "external": False, "open": any(k["active"] or k["open"] for k in kids)}
            if item.page:
                return {"title": item.title, "children": [], "href": self.page_href(page, item.page),
                        "active": item.page is page, "external": False, "open": False}
            return {"title": item.title, "children": [], "href": item.url,
                    "active": False, "external": True, "open": False}

        return [conv(i) for i in self.nav]

    # ----- top tabs and landing page -----------------------------------------
    def first_page(self, item: NavItem) -> Page | None:
        if item.page:
            return item.page
        for child in item.children:
            found = self.first_page(child)
            if found:
                return found
        return None

    def contains(self, item: NavItem, page: Page) -> bool:
        return item.page is page or any(self.contains(c, page) for c in item.children)

    def top_nav_for(self, page: Page) -> list[dict]:
        tabs = []
        for item in self.nav:
            if item.page is self.home and not item.children:
                continue  # the brand already links home
            if item.url:
                tabs.append({"title": item.title, "href": item.url, "active": False, "external": True})
                continue
            target = self.first_page(item)
            if target:
                tabs.append({"title": item.title, "href": self.page_href(page, target),
                             "active": self.contains(item, page), "external": False})
        return tabs

    def home_context(self, page: Page) -> dict:
        """Hero and feature data from the front matter of a page using home.html."""
        meta = page.meta
        hero = meta.get("hero") if isinstance(meta.get("hero"), dict) else None
        if hero:
            hero = dict(hero)
            actions = []
            for a in hero.get("actions") or []:
                if isinstance(a, dict) and a.get("text"):
                    link = str(a.get("link", ""))
                    actions.append({"text": str(a["text"]), "style": str(a.get("style", "primary")),
                                    "href": (self.resolve_link(page, link) or link) if link else "#"})
            hero["actions"] = actions
            if hero.get("code"):
                try:
                    lexer = get_lexer_by_name(str(hero.get("code_lang", "text")))
                except ClassNotFound:
                    lexer = get_lexer_by_name("text")
                hero["code_html"] = Markup(pyg_highlight(
                    str(hero["code"]).rstrip("\n"), lexer, HtmlFormatter(cssclass="highlight")))
            elif hero.get("image"):
                hero["image_href"] = self.local_href(page, str(hero["image"]), what="hero image")
        features = []
        for f in meta.get("features") if isinstance(meta.get("features"), list) else []:
            if isinstance(f, dict) and f.get("title"):
                link = str(f.get("link", ""))
                features.append({"title": str(f["title"]), "text": str(f.get("text", "")),
                                 "wide": bool(f.get("wide")),
                                 "href": (self.resolve_link(page, link) or link) if link else None})
        return {"hero": hero, "features": features}

    # ----- search index ----------------------------------------------------
    HEAD_RE = re.compile(r"<h([1-4])\s+id=\"([^\"]*)\"[^>]*>(.*?)</h\1>", re.S)

    def search_entries(self, page: Page) -> list[dict]:
        if page.meta.get("search") is False:
            return []
        parts, pos = [], 0
        cur_title, cur_id = page.title, ""
        for m in self.HEAD_RE.finditer(page.html):
            parts.append((cur_title, cur_id, page.html[pos:m.start()]))
            cur_title = strip_tags(m.group(3))
            cur_id = "" if m.group(1) == "1" else m.group(2)
            pos = m.end()
        parts.append((cur_title, cur_id, page.html[pos:]))
        entries = []
        for title, id_, chunk in parts:
            text = strip_tags(chunk)[:5000]
            if not text and not id_:
                continue
            entries.append({"t": title, "p": page.title, "u": page.url + (f"#{id_}" if id_ else ""), "x": text})
        return entries

    # ----- theme assets ----------------------------------------------------
    def pygments_css(self) -> str:
        styles = set(get_all_styles())
        theme = self.cfg["theme"]

        def pick(name, fallback):
            if name in styles:
                return name
            self.warn(f"unknown pygments style '{name}', using '{fallback}'")
            return fallback

        light = HtmlFormatter(style=pick(theme["code_light"], "default")).get_style_defs(".highlight")
        dark = HtmlFormatter(style=pick(theme["code_dark"], "monokai")).get_style_defs('[data-theme="dark"] .highlight')
        return f"/* generated from pygments */\n{light}\n{dark}\n"

    def asset_url(self, root: str, ref: str) -> str:
        return ref if re.match(r"^([a-z][a-z0-9+.-]*:)?//", ref, re.I) else root + quote(ref.lstrip("/"), safe="/")

    # ----- build -----------------------------------------------------------
    def build(self):
        t0 = time.time()
        self.collect()
        for page in self.pages:
            self.convert(page)
        self.build_nav()

        tmp = self.site_dir.with_name(self.site_dir.name + ".__build")
        if tmp.exists():
            shutil.rmtree(tmp)
        (tmp / "_static").mkdir(parents=True)

        # static files
        static_src = self.theme_dir / "static"
        if static_src.is_dir():
            shutil.copytree(static_src, tmp / "_static", dirs_exist_ok=True)
        (tmp / "_static" / "pygments.css").write_text(self.pygments_css(), encoding="utf-8")
        index = [e for p in self.pages for e in self.search_entries(p)]
        (tmp / "_static" / "search_index.js").write_text(
            "window.__SEARCH_INDEX__=" + json.dumps(index, ensure_ascii=False, separators=(",", ":")) + ";",
            encoding="utf-8")
        if self.dev:
            (tmp / "_static" / "build-id.txt").write_text(str(time.time_ns()), encoding="utf-8")

        # docs assets (images, pdfs, demo html, ...)
        for rel in self.assets:
            dest = tmp / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.docs_dir / rel, dest)

        # pages
        env = Environment(loader=FileSystemLoader(str(self.theme_dir / "templates")),
                          autoescape=select_autoescape(["html", "xml"]), trim_blocks=True, lstrip_blocks=True)
        order = {id(p): i for i, p in enumerate(self.nav_pages)}
        for page in self.pages:
            root = self.root_path(page)
            prev = nxt = None
            if id(page) in order:
                i = order[id(page)]
                if i > 0:
                    prev = {"title": self.nav_pages[i - 1].title, "href": self.page_href(page, self.nav_pages[i - 1])}
                if i < len(self.nav_pages) - 1:
                    nxt = {"title": self.nav_pages[i + 1].title, "href": self.page_href(page, self.nav_pages[i + 1])}
            edit_url = None
            if self.cfg["repo_url"] and self.cfg["edit_uri"]:
                edit_url = f"{self.cfg['repo_url'].rstrip('/')}/{self.cfg['edit_uri'].strip('/')}/{page.src}"
            ctx = {
                "site": self.cfg, "theme": self.cfg["theme"], "page": page,
                "content": Markup(page.html), "nav": self.nav_for(page), "toc": page.toc,
                "root": root, "home_href": self.page_href(page, self.home), "prev": prev, "next": nxt,
                "edit_url": edit_url, "dev": self.dev,
                "top_nav": self.top_nav_for(page),
                "logo": root + quote(self.cfg["theme"]["logo"].lstrip("/"), safe="/") if self.cfg["theme"].get("logo") else None,
                "on_primary": contrast_text(self.cfg["theme"]["primary"]),
                "on_primary_dark": contrast_text(self.cfg["theme"]["primary_dark"]),
                **self.home_context(page),
                "updated": datetime.fromtimestamp(page.mtime).strftime("%d %b %Y") if self.cfg["show_updated"] else None,
                "canonical": f"{self.cfg['site_url']}/{page.url}" if self.cfg["site_url"] else None,
                "extra_css": [self.asset_url(root, c) for c in self.cfg["extra_css"]],
                "extra_js": [self.asset_url(root, j) for j in self.cfg["extra_javascript"]],
            }
            html_out = env.get_template(page.meta.get("template", "base.html")).render(**ctx)
            dest = tmp / page.out
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(html_out, encoding="utf-8")

        if self.site_dir.exists():
            shutil.rmtree(self.site_dir)
        tmp.rename(self.site_dir)
        print(f"Built {len(self.pages)} pages, {len(self.assets)} assets, {len(index)} search entries "
              f"-> {self.site_dir} in {time.time() - t0:.2f}s ({self.warnings} warnings)")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def signature(site: Site):
    latest = count = 0
    for base in (site.config_path, site.docs_dir, site.theme_dir):
        files = [base] if base.is_file() else base.rglob("*")
        for p in files:
            try:
                latest = max(latest, p.stat().st_mtime_ns)
                count += 1
            except OSError:
                pass
    return latest, count


def cmd_build(args) -> int:
    site = Site(Path(args.config))
    site.build()
    return 1 if (args.strict and site.warnings) else 0


def cmd_serve(args) -> int:
    cfg = Path(args.config)
    site = Site(cfg, dev=True)
    site.build()
    stop = threading.Event()

    def watch():
        nonlocal site
        last = signature(site)
        while not stop.wait(1.0):
            try:
                cur = signature(site)
                if cur != last:
                    last = cur
                    print("Change detected, rebuilding...")
                    site = Site(cfg, dev=True)
                    site.build()
            except (Exception, SystemExit) as exc:  # keep serving, show the error
                print(f"Build failed: {exc}", file=sys.stderr)

    threading.Thread(target=watch, daemon=True).start()

    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

    handler = functools.partial(Handler, directory=str(site.site_dir))
    with http.server.ThreadingHTTPServer((args.host, args.port), handler) as httpd:
        print(f"Serving on http://{args.host}:{args.port}/  (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
        finally:
            stop.set()
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Markdown -> multi-page HTML site generator")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build the site once")
    b.add_argument("-c", "--config", default="site.yml")
    b.add_argument("--strict", action="store_true", help="exit with an error if there are warnings")
    s = sub.add_parser("serve", help="build, serve, and rebuild on change")
    s.add_argument("-c", "--config", default="site.yml")
    s.add_argument("-p", "--port", type=int, default=8000)
    s.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args(argv)
    if not Path(args.config).is_file():
        print(f"error: config file not found: {args.config}", file=sys.stderr)
        return 2
    return {"build": cmd_build, "serve": cmd_serve}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
