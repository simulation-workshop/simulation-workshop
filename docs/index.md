---
title: Acme Docs
template: home.html
description: Documentation for the Acme platform.
hero:
  title: Write Markdown. Get a documentation site.
  text: Describe your pages in one file, drop your Markdown into a folder, and publish a fast, searchable site that works on any host.
  actions:
    - text: Get started
      link: getting-started/installation.md
      style: primary
    - text: See embeds in action
      link: guide/embedding.md
      style: secondary
  code_title: site.yml
  code_lang: yaml
  code: |
    site_name: Acme Docs

    nav:
      - Home: index.md
      - Getting Started:
          - Installation: getting-started/installation.md
          - Configuration: getting-started/configuration.md
      - Guide:
          - Writing content: guide/writing-content.md
          - Embeds & includes: guide/embedding.md
      - Reference:
          - Command line: reference/cli.md
features:
  - title: Your layout lives in one file
    text: List pages in site.yml and they become the sidebar, the section tabs, and the previous and next links. Leave the list out and the folder structure is used instead.
    link: getting-started/configuration.md
    wide: true
  - title: Search that works offline
    text: Press Ctrl+K or Cmd+K to search every page and heading. No server needed.
    link: reference/cli.md
  - title: Embeds and snippets
    text: Add YouTube, PDFs and live demos with one line, and reuse Markdown partials.
    link: guide/embedding.md
  - title: Light and dark, built in
    text: The theme follows the reader's system setting and remembers their choice, with an accent color you set in one line.
    link: getting-started/configuration.md
    wide: true
---

## Quick start

```bash
pip install markdown pyyaml jinja2 pygments
python build.py serve
```

Open `http://127.0.0.1:8000`. Edit any file in `docs/` and the page reloads. When you're ready to publish, run `python build.py build` and upload the `site/` folder.
