# Command line

## `build`

```bash
python build.py build [-c site.yml] [--strict]
```

Converts every page and writes the site to `site_dir`. The old output is replaced only after the new build succeeds.

`--strict` makes the command exit with status 1 if there were warnings, such as a broken link, a missing include, or a nav entry that points at a missing file. Use it in CI.

## `serve`

```bash
python build.py serve [-c site.yml] [-p 8000] [--host 127.0.0.1]
```

Builds the site, serves it locally, and rebuilds when anything in `docs/`, `theme/` or `site.yml` changes. Open pages reload themselves.

## Warnings you may see

| Message                         | Fix                                                     |
| ------------------------------- | ------------------------------------------------------- |
| `link to unknown page`          | The `.md` file doesn't exist; check the path            |
| `include not found`             | Check the path, relative to the page or `docs/`         |
| `nav: page not found`           | The file named in `nav` isn't under `docs/`             |
| `link target not found`         | An image or file link points at a missing asset         |

See [configuration](../getting-started/configuration.md) for the settings that affect the build.
