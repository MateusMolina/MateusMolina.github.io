# pub.mmolina.me — Public links

A minimal static site that lists my public work, reading notes, and resources.  
Built with a tiny Python generator from a BibLaTeX-inspired YAML config.

## Adding a link

Open [`links.yaml`](links.yaml) and add an entry under `entries:`.  
Every entry can use these fields:

| Field         | Required | Description                                      |
|---------------|----------|--------------------------------------------------|
| `key`         | yes      | Unique identifier, snake_case, no spaces         |
| `type`        | yes      | `website` · `book` · `paper` · `note` · `project` · `other` |
| `title`       | yes      | Display title                                    |
| `url`         | yes      | Full URL                                         |
| `description` | no       | Short description shown under the title          |
| `authors`     | no       | Author string — mainly for papers                |
| `venue`       | no       | Conference / journal / publisher                 |
| `year`        | no       | Year of publication or access                    |
| `pinned`      | no       | `true` to float to the top of its section        |

## Building locally

```bash
pip install pyyaml
python build.py          # generates index.html
python build.py --watch  # rebuild on save (also needs: pip install watchdog)
```

## Deployment

Pushes to `main` trigger the [GitHub Actions workflow](.github/workflows/build.yml),
which runs `build.py` and pushes the updated `index.html` back to the repo
(served via GitHub Pages on `pub.mmolina.me`).
