# Writing content

Standard Markdown plus the "extra" features: tables, footnotes, definition lists, abbreviations and attribute lists.

## Admonitions

!!! note
    A plain note. The title defaults to the type name.

!!! info "Custom title"
    Admonitions can hold **formatting**, `code`, and lists:

    - first
    - second

!!! success
    Something went well.

!!! warning
    Be careful here.

!!! danger "Do not do this"
    Destructive action ahead.

??? example "Collapsible example"
    Use `???` instead of `!!!` only if you add the `pymdownx.details` extension.

## Code

Fenced code is highlighted at build time and gets a copy button:

```python
def greet(name: str) -> str:
    """Return a friendly greeting."""
    return f"Hello, {name}!"

print(greet("docs"))
```

Inline code looks like `this`. Keyboard keys: <kbd>Ctrl</kbd> + <kbd>K</kbd>.

## Tables

| Column     | Type    | Notes                    |
| ---------- | ------- | ------------------------ |
| `id`       | integer | Primary key              |
| `title`    | string  | Required                 |
| `archived` | boolean | Defaults to `false`      |

## Lists and definitions

1. Ordered item
2. Another item
    - nested bullet
    - another one

Term
:   Definition of the term, written with a leading colon.

The HTML spec is maintained by the W3C and WHATWG.

*[HTML]: HyperText Markup Language
*[W3C]: World Wide Web Consortium

## Footnotes

Footnotes are collected at the bottom of the page.[^1]

[^1]: Like this one.

## Card grids

Wrap a list in a `grid cards` block to lay it out as cards:

```html
<div class="grid cards" markdown="1">

- **Fast builds**

    Hundreds of pages in a second.

- **Plain files**

    Nothing to install on the server.

</div>
```

<div class="grid cards" markdown="1">

- **Fast builds**

    Hundreds of pages in a second.

- **Plain files**

    Nothing to install on the server.

- **Yours to change**

    Edit the theme's CSS and templates.

</div>

## Images and links

Images can be sized with attribute lists:

![Sample logo](../assets/logo.svg){ width=96 }

Links to other pages use the file name, so they keep working if you rename the output: [back to the start](../index.md), [installation](../getting-started/installation.md#project-layout).
