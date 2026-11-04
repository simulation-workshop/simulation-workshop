---
description: How to describe your site's layout and appearance in site.yml.
---

# Configuration

All settings live in `site.yml`.

## Navigation

The `nav` key is the layout of your site. Entries are `Title: path.md`, and a title that maps to a list becomes a collapsible section:

```yaml
nav:
  - Home: index.md
  - Getting Started:
      - Installation: getting-started/installation.md
      - Configuration: getting-started/configuration.md
  - Source code: https://github.com      # external links work too
```

Paths are relative to `docs/`. If you leave `nav` out, it is generated from the folder structure, with `index.md` first in each folder.

## Appearance

```yaml
theme:
  primary: "#00796b"      # accent color, light mode
  primary_dark: "#3ddbc0" # accent color, dark mode
  default_mode: auto      # auto | light | dark
  code_light: xcode
  code_dark: github-dark
  fonts: true             # false = system fonts only, no Google Fonts request
  logo: assets/logo.svg   # optional, shown next to the site name
```

Any [Pygments style](https://pygments.org/styles/) name works for the code themes. Text on buttons switches between white and near-black automatically so it stays readable on whatever accent you choose.

## Landing page

Give a page `template: home.html` and describe its hero and highlights in the front matter. The Markdown below the front matter is shown after the highlights.

```yaml
---
title: Acme Docs
template: home.html
hero:
  title: Write Markdown. Get a documentation site.
  text: One supporting sentence.
  actions:
    - {text: Get started, link: getting-started/installation.md, style: primary}
    - {text: Learn more, link: guide/embedding.md, style: secondary}
  code_title: site.yml      # optional code window beside the headline
  code_lang: yaml
  code: |
    nav:
      - Home: index.md
  # image: assets/screenshot.png   # use instead of code
features:
  - title: First highlight
    text: A sentence or two.
    link: guide/embedding.md
    wide: true              # spans two columns; pair wide cards with normal ones
---
```

The first level of `nav` also becomes a row of section tabs in the top bar.

## Page options

A page can start with YAML front matter:

```yaml
---
title: Custom title        # otherwise the first # heading is used
description: Shown in <meta> tags
hide_title: true           # skip the auto-generated h1 when the page has none
search: false              # leave this page out of the search index
---
```

## Settings reference

| Key                  | Default | Purpose                                              |
| -------------------- | ------- | ---------------------------------------------------- |
| `use_directory_urls` | `false` | `true` builds `page/index.html` for clean URLs       |
| `exclude_docs`       | `[]`    | Extra glob patterns to skip (`.*` and `_*` always are) |
| `extra_css`          | `[]`    | Stylesheets to add, relative to `docs/`              |
| `extra_javascript`   | `[]`    | Scripts to add, relative to `docs/`                  |
| `markdown_extensions`| `[]`    | Extra Python-Markdown extensions                     |

!!! warning "Directory URLs and local files"
    With `use_directory_urls: true`, links end in `/`, which browsers can't open from disk. Host the site on a web server (or use `build.py serve`) in that mode.

Continue with [writing content](../guide/writing-content.md).
