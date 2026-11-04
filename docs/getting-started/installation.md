# Installation

You need Python 3.9 or newer.

```bash
pip install markdown pyyaml jinja2 pygments
```

Then, from the project folder:

```bash
python build.py build      # writes the site to ./site
python build.py serve      # live preview at http://127.0.0.1:8000
```

## Project layout

```text
mdsite/
├── build.py          # the generator
├── site.yml          # site settings and navigation
├── docs/             # your Markdown files, images and other assets
│   ├── index.md
│   └── _snippets/    # partials: never published on their own
└── theme/            # templates, CSS and JS (the predefined style)
```

## Verify the build

{% include "_snippets/shared-note.md" %}

Next: [configure the site](configuration.md).
