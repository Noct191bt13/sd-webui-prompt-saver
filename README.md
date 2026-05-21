# Prompt Saver

Save, manage, and re-use prompts in Stable Diffusion WebUI Forge.

## Features

- **Save prompts** — save any prompt with a custom name for later use
- **Browse & edit** — select saved prompts from a dropdown, view and edit the text
- **Search** — filter the prompt list by name or text content, toggle to show only favorites
- **Append** — append a saved prompt to whatever's currently in the main prompt box
- **Replace** — replace the main prompt with a saved one
- **Save current** — capture the current main prompt text and save it as a new entry
- **Rename** — select a prompt, edit its name in the name field, then click "Save changes"
- **Tags** — add comma-separated tags to prompts for organization (auto-saved on change)
- **Favorites** — mark prompts as favorites, filter by favorites only
- **Extra info** — add tags, LoRAs, quality boosters that get prepended when generating
- **Generate** — compose the full prompt (extra info + saved prompt) and click Generate
- **Export** — export all saved prompts to a timestamped `.txt` file
- **Import** — import prompts from a `.txt` file (plain text, `--pos` format, or JSON)
- **XYZ Grid** — use saved prompts as an axis in the XYZ Grid script (appends to the main prompt)

## UI

The extension adds an accordion **Prompt Saver** under txt2img and img2img:

```
🔍 [Search prompts...                  ]  [★] Favorites only
[▼ Saved prompts (filtered choices)                ]

[Append to prompt] [Replace prompt] [← Save current]

[Prompt text editor...]

Tags: [portrait, anime, high-res        ]  [★ Toggle fav]

[Save as new — name (auto‑filled on select)]
[Save as new] [Save changes] [Delete]

[Extra info to prepend...]           [Generate]

╔═══ Export prompts ════════════════╗
╚═══════════════════════════════════╝
╔═══ Import prompts ════════════════╗
╚═══════════════════════════════════╝
```

When you select a prompt from the dropdown:
- The text editor shows the prompt text
- The **tags** field shows its comma-separated tags (changes auto-save)
- The **name** field shows the prompt's name (edit it and click "Save changes" to rename)
- The **favorite** button shows ★ or ☆

## Data Storage

Saved prompts are stored in a **JSON file** inside the extension folder:

```
extensions/sd-webui-prompt-saver/prompt-saver.json
```

The file format:

```json
{
  "prompts": [
    {"name": "Portrait base", "text": "1girl, solo, looking at viewer", "favorite": true, "tags": ["portrait", "anime"]},
    {"name": "Action shot",   "text": "dynamic pose, action", "favorite": false, "tags": []}
  ]
}
```

Edit this file directly to bulk-manage prompts — changes are picked up after a page refresh.

## Settings (Settings → Prompt Saver)

Persistent settings available in the **Settings** tab:

| Setting | Key | Description |
|---------|-----|-------------|
| Default export folder | `prompt_saver_export_path` | Where exported `.txt` files are saved by default |
| Default export format | `prompt_saver_export_format` | "One prompt per line" or "Script format (--pos)" |

## Export

Writes all saved prompts to a timestamped `.txt` file.

- **Format**: "One prompt per line" (plain) or "Script format (--pos)" (lines wrapped in `--pos "..."`)
- **Folder**: leave blank for the default (set in Settings), or type a custom path
- Multi-line prompts are collapsed to a single line in the export (original line breaks are preserved in the JSON storage)

## Import

Upload a `.txt` or `.json` file and import prompts. Supports:

| Format | Description |
|--------|-------------|
| **JSON** | Native extension format (`{"prompts": [{"name":..., "text":...}, ...]}`) — names are preserved |
| **Auto-detect** (text) | Handles both plain lines and `--pos` format |
| **One prompt per line** | Each non-empty line is a prompt |
| **Script format (--pos)** | Only lines starting with `--pos` are imported |

- Lines starting with `#` are treated as comments and skipped
- `--neg` lines are skipped in auto-detect mode
- Imported prompts are named "Imported 1", "Imported 2", etc. (text) or their original name (JSON)
- Duplicate names are automatically renamed (e.g. "Portrait (1)")

## XYZ Grid

In the XYZ Grid script, a new axis `[Prompt Saver] Saved prompt` is available. It lists all your saved prompts as choices and **appends** the selected prompt's text to whatever's in the main prompt box.

Example: if your main prompt is `masterpiece, best quality` and the saved prompt is `1girl, portrait`, the generated prompt becomes `masterpiece, best quality, 1girl, portrait`.

## Installation

1. Place the `sd-webui-prompt-saver` folder in the `extensions/` directory
2. Restart or reload the webui
3. Open the **Prompt Saver** accordion under txt2img or img2img
