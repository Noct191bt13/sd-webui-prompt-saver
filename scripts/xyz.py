"""
XYZ Grid integration for Prompt Saver.

Self-contained — reads prompt-saver.json directly,
no dependency on main.py or lib_prompt_saver.
"""

import json
import os

from modules import scripts


def _load_prompts():
    """Load prompts from the extension's JSON file."""
    ext_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(ext_dir, "prompt-saver.json")
    if not os.path.isfile(path):
        return []
    try:
        return json.load(open(path, encoding="utf-8")).get("prompts", [])
    except (json.JSONDecodeError, OSError):
        return []


def patch_xyz_grid():
    """Register Prompt Saver axis options."""
    xyz_grid = None
    for data in scripts.scripts_data:
        if data.script_class.__module__ in ("xyz_grid.py", "scripts.xyz_grid") and hasattr(data, "module"):
            xyz_grid = data.module
            break

    if xyz_grid is None:
        print("[Prompt Saver] xyz_grid not found")
        return

    label = "[Prompt Saver] "
    if any(x.label == label for x in xyz_grid.axis_options):
        return

    def apply_saved_prompt(p, name, _xs):
        for saved in _load_prompts():
            if saved["name"] == name:
                base = p.prompt.strip().rstrip(",").strip()
                full = f"{base}, {saved['text']}" if base else saved["text"]
                p.prompt = full
                p.all_prompts = [full] * max(p.batch_size, 1)
                return

    def list_choices():
        prompts = _load_prompts()
        return [p["name"] for p in prompts] or ["(no prompts saved)"]

    xyz_grid.axis_options.extend([
        xyz_grid.AxisOption(label, str, apply_saved_prompt, choices=list_choices),
    ])


try:
    patch_xyz_grid()
except Exception as e:
    print(f"[Prompt Saver] xyz_grid patch failed: {e}")
