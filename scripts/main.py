"""
Prompt Saver — single-file diagnostic version.
All logic inlined, no lib_prompt_saver dependency.
"""
import json, os, re, threading
from datetime import datetime

import gradio as gr
import modules.scripts as scripts
from modules import script_callbacks, shared

# ── Config ──────────────────────────────────────────────────────────────

_pending_override = None

EXTENSION_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVER_JSON = os.path.join(EXTENSION_DIR, "prompt-saver.json")
DEFAULT_EXPORT_DIR = os.path.join(EXTENSION_DIR, "exported_prompts")
PLACEHOLDER = "--- Select a saved prompt ---"
_prompt_lock = threading.Lock()

def load():
    with _prompt_lock:
        if not os.path.isfile(SAVER_JSON): return []
        try:
            data = json.load(open(SAVER_JSON, encoding="utf-8"))
            prompts = data.get("prompts", [])
            for p in prompts:
                if "favorite" not in p: p["favorite"] = False
                if "tags" not in p: p["tags"] = []
            return prompts
        except: return []

def save(prompts):
    with _prompt_lock:
        json.dump({"prompts": prompts}, open(SAVER_JSON, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

def find(name):
    for p in load():
        if p["name"] == name: return p
    return None

def unique_name(base, existing):
    n, i = base, 1
    while n in existing:
        n = f"{base} ({i})"
        i += 1
    return n

def filter_names(query="", fav_only=False):
    prompts = load()
    if fav_only: prompts = [p for p in prompts if p.get("favorite")]
    if query.strip():
        q = query.strip().lower()
        prompts = [p for p in prompts if q in p["name"].lower() or q in p["text"].lower()]
    choices = [(f"★ {p['name']}", p["name"]) if p.get("favorite") else (p["name"], p["name"]) for p in prompts]
    choices.insert(0, (PLACEHOLDER, PLACEHOLDER))
    return choices

# ── Textbox references ─────────────────────────────────────────────────

txt2img_prompt = None
img2img_prompt = None

def _on_after_component(component, **_kwargs):
    eid = getattr(component, "elem_id", None)
    if eid == "txt2img_prompt":
        global txt2img_prompt; txt2img_prompt = component
    elif eid == "img2img_prompt":
        global img2img_prompt; img2img_prompt = component

script_callbacks.on_after_component(_on_after_component)

# ── Settings ───────────────────────────────────────────────────────────

def on_ui_settings():
    shared.opts.add_option("prompt_saver_export_path", shared.OptionInfo(DEFAULT_EXPORT_DIR, "Default export folder for saved prompts", section=("prompt_saver", "Prompt Saver")))
    shared.opts.add_option("prompt_saver_export_format", shared.OptionInfo("One prompt per line", "Default export format", gr.Dropdown, lambda: {"choices": ["One prompt per line", "Script format (--pos)"]}, section=("prompt_saver", "Prompt Saver")))

script_callbacks.on_ui_settings(on_ui_settings)

# ── Script ─────────────────────────────────────────────────────────────

class Script(scripts.Script):
    sorting_priority = 15.1
    def title(self): return "Prompt Saver"
    def show(self, is_img2img): return scripts.AlwaysVisible

    def process(self, p, *args):
        global _pending_override
        if _pending_override is not None:
            p.all_prompts = [_pending_override] * len(p.all_prompts)
            _pending_override = None

    def ui(self, is_img2img):
        tab_name = "img2img" if is_img2img else "txt2img"
        prompt_box = img2img_prompt if is_img2img else txt2img_prompt
        EID = "ps"

        with gr.Accordion("Prompt Saver", open=False):

            with gr.Row():
                search_box = gr.Textbox(label="Search prompts", placeholder="Type to filter...", elem_id=f"{EID}_search", scale=3)
                fav_only = gr.Checkbox(label="★ Favorites only", value=False, elem_id=f"{EID}_fav_only", scale=1)

            saved_dropdown = gr.Dropdown(choices=filter_names(), value=PLACEHOLDER, label="Saved prompts", elem_id=f"{EID}_saved")

            with gr.Row():
                append_btn = gr.Button("Append to prompt", elem_id=f"{EID}_append")
                replace_btn = gr.Button("Replace prompt", elem_id=f"{EID}_replace")
                save_current_btn = gr.Button("← Save current", elem_id=f"{EID}_save_current")

            prompt_editor = gr.Textbox(label="Prompt text (view / edit)", lines=4, placeholder="Select a saved prompt above...", elem_id=f"{EID}_editor")

            with gr.Row():
                tags_box = gr.Textbox(label="Tags (comma‑separated)", placeholder="portrait, anime", elem_id=f"{EID}_tags", scale=3)
                fav_btn = gr.Button("☆ Toggle favorite", elem_id=f"{EID}_fav_btn", scale=1)

            new_name = gr.Textbox(label="Save as new — name", placeholder="My prompt name", elem_id=f"{EID}_new_name")

            with gr.Row():
                save_new_btn = gr.Button("Save as new", elem_id=f"{EID}_save_new")
                save_changes_btn = gr.Button("Save changes", elem_id=f"{EID}_save_changes")
                delete_btn = gr.Button("Delete", elem_id=f"{EID}_delete", variant="stop")

            with gr.Row():
                extra_info = gr.Textbox(label="Extra info to prepend...", placeholder="masterpiece, <lora:my_lora:1.0>", elem_id=f"{EID}_extra", scale=2)
                generate_btn = gr.Button("Generate with saved prompt", elem_id=f"{EID}_generate", variant="primary", scale=1)

            with gr.Accordion("Export prompts", open=False):
                export_fmt = gr.Dropdown(choices=["One prompt per line", "Script format (--pos)"], value=shared.opts.data.get("prompt_saver_export_format", "One prompt per line"), label="Export format", elem_id=f"{EID}_export_fmt")
                export_path = gr.Textbox(label="Save folder", placeholder=shared.opts.data.get("prompt_saver_export_path", DEFAULT_EXPORT_DIR), elem_id=f"{EID}_export_path")
                export_btn = gr.Button("Export to .txt", elem_id=f"{EID}_export_btn", variant="primary")
                export_file = gr.File(label="Download", interactive=False, elem_id=f"{EID}_export_file")

            with gr.Accordion("Import prompts", open=False):
                import_file = gr.File(label="Upload a .txt file", file_types=[".txt"], elem_id=f"{EID}_import_file")
                import_fmt = gr.Dropdown(choices=["Auto-detect", "One prompt per line", "Script format (--pos)"], value="Auto-detect", label="Import format", elem_id=f"{EID}_import_fmt")
                import_btn = gr.Button("Import prompts", elem_id=f"{EID}_import_btn", variant="primary")
                import_status = gr.HTML(value="", elem_id=f"{EID}_import_status")

        # ═══ Event wiring ═══════════════════════════════════════════════

        def _search(q, f): return gr.update(choices=filter_names(q, f), value=PLACEHOLDER)
        search_box.change(fn=_search, inputs=[search_box, fav_only], outputs=[saved_dropdown])
        fav_only.change(fn=_search, inputs=[search_box, fav_only], outputs=[saved_dropdown])

        def _select(name):
            if not name or name == PLACEHOLDER: return "", "", "☆ Toggle favorite", ""
            p = find(name)
            if not p: return "", "", "☆ Toggle favorite", ""
            tags = ", ".join(p.get("tags", []))
            star = "★" if p.get("favorite") else "☆"
            return p["text"], tags, f"{star} Toggle favorite", p["name"]
        saved_dropdown.change(fn=_select, inputs=[saved_dropdown], outputs=[prompt_editor, tags_box, fav_btn, new_name])

        if prompt_box is not None:
            def _append(name, cur):
                if not name or name == PLACEHOLDER: return ""
                p = find(name)
                return f"{cur}, {p['text']}" if cur and p else (p["text"] if p else "")
            append_btn.click(fn=_append, inputs=[saved_dropdown, prompt_box], outputs=[prompt_box])

            def _replace(name, _cur):
                if not name or name == PLACEHOLDER: return ""
                p = find(name)
                return p["text"] if p else ""
            replace_btn.click(fn=_replace, inputs=[saved_dropdown, prompt_box], outputs=[prompt_box])

            def _save_cur(name, cur, tags_str):
                if not cur: return gr.update(), ""
                if not name:
                    existing = {p["name"] for p in load()}
                    name = unique_name("Prompt", existing)
                tags = [t.strip() for t in tags_str.split(",") if t.strip()]
                prompts = load()
                names = {p["name"] for p in prompts}
                safe = unique_name(name, names)
                prompts.append({"name": safe, "text": cur, "favorite": False, "tags": tags})
                save(prompts)
                return gr.update(choices=filter_names(), value=PLACEHOLDER), ""
            save_current_btn.click(fn=_save_cur, inputs=[new_name, prompt_box, tags_box], outputs=[saved_dropdown, new_name])

            def _gen(name, extra, _cur):
                global _pending_override
                if not name or name == PLACEHOLDER: return
                p = find(name)
                if not p: return
                _pending_override = f"{extra}, {p['text']}" if extra else p["text"]
            generate_btn.click(fn=_gen, inputs=[saved_dropdown, extra_info, prompt_box], outputs=[]).then(
                fn=None, _js=f"() => {{const btn = document.querySelector('#{tab_name}_generate'); if(btn) btn.click(); return [];}}", inputs=[], outputs=[])

        def _fav(name):
            if not name or name == PLACEHOLDER: return gr.update()
            prompts = load()
            for p in prompts:
                if p["name"] == name:
                    p["favorite"] = not p.get("favorite", False)
                    save(prompts)
                    star = "★" if p["favorite"] else "☆"
                    return f"{star} Toggle favorite"
            return gr.update()
        fav_btn.click(fn=_fav, inputs=[saved_dropdown], outputs=[fav_btn])

        def _tags_save(name, tags_str):
            if not name or name == PLACEHOLDER: return
            tags = [t.strip() for t in tags_str.split(",") if t.strip()]
            prompts = load()
            for p in prompts:
                if p["name"] == name: p["tags"] = tags; break
            save(prompts)
        tags_box.change(fn=_tags_save, inputs=[saved_dropdown, tags_box], outputs=[])

        def _save_new(name, text, tags_str):
            if not name or not text: return gr.update(choices=filter_names(), value=PLACEHOLDER), "", "", "☆ Toggle favorite"
            tags = [t.strip() for t in tags_str.split(",") if t.strip()]
            prompts = load()
            safe = unique_name(name, {p["name"] for p in prompts})
            prompts.append({"name": safe, "text": text, "favorite": False, "tags": tags})
            save(prompts)
            return gr.update(choices=filter_names(), value=PLACEHOLDER), "", tags_str, "☆ Toggle favorite"
        save_new_btn.click(fn=_save_new, inputs=[new_name, prompt_editor, tags_box], outputs=[saved_dropdown, new_name, tags_box, fav_btn])

        def _save_chg(name, new_name_val, text, tags_str):
            if not name or not text or name == PLACEHOLDER:
                return gr.update(choices=filter_names(), value=PLACEHOLDER), ""
            tags = [t.strip() for t in tags_str.split(",") if t.strip()]
            prompts = load()
            final_name = name
            for p in prompts:
                if p["name"] == name:
                    p["text"], p["tags"] = text, tags
                    if new_name_val and new_name_val != name:
                        existing_names = {pp["name"] for pp in prompts if pp["name"] != name}
                        final_name = unique_name(new_name_val, existing_names)
                        p["name"] = final_name
                    break
            save(prompts)
            return gr.update(choices=filter_names(), value=final_name), final_name
        save_changes_btn.click(fn=_save_chg, inputs=[saved_dropdown, new_name, prompt_editor, tags_box], outputs=[saved_dropdown, new_name])

        def _del(name):
            if not name or name == PLACEHOLDER: return gr.update(choices=filter_names(), value=PLACEHOLDER), "", "", "☆ Toggle favorite"
            prompts = [p for p in load() if p["name"] != name]
            save(prompts)
            return gr.update(choices=filter_names(), value=PLACEHOLDER), "", "", "☆ Toggle favorite"
        delete_btn.click(fn=_del, inputs=[saved_dropdown], outputs=[saved_dropdown, prompt_editor, tags_box, fav_btn])

        def _exp(fmt, folder):
            prompts = load()
            if not prompts: return None
            out_dir = (folder or "").strip() or shared.opts.data.get("prompt_saver_export_path", DEFAULT_EXPORT_DIR)
            os.makedirs(out_dir, exist_ok=True)
            lines = []
            for p in prompts:
                t = p["text"].replace("\r\n", " ").replace("\n", " ")
                t = re.sub(r"\s+", " ", t).strip()
                lines.append(f'--pos "{t}"' if fmt == "Script format (--pos)" else t)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(out_dir, f"exported_prompts_{ts}.txt")
            open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
            return path
        export_btn.click(fn=_exp, inputs=[export_fmt, export_path], outputs=[export_file])

        def _imp(file, fmt):
            if file is None: return '<span style="color:red">No file uploaded.</span>'
            raw = None
            try:
                raw = open(file.name, encoding="utf-8-sig").read()
                data = json.loads(raw)
                if isinstance(data, dict) and "prompts" in data:
                    valid = [e for e in data["prompts"] if isinstance(e, dict) and "name" in e and "text" in e]
                    if not valid: return '<span style="color:orange">No valid entries in JSON.</span>'
                    existing = load()
                    names = {p["name"] for p in existing}
                    for e in valid:
                        n = unique_name(e["name"], names)
                        existing.append({"name": n, "text": e["text"], "favorite": e.get("favorite", False), "tags": e.get("tags", [])})
                        names.add(n)
                    save(existing)
                    return f'<span style="color:green">Imported {len(valid)} prompt(s) from JSON.</span>'
            except json.JSONDecodeError: pass
            except OSError as e: return f'<span style="color:red">Error: {e}</span>'

            if raw is None: raw = open(file.name, encoding="utf-8-sig").read()
            imported = []
            for line in raw.split("\n"):
                t = line.strip()
                if not t or t.startswith("#"): continue
                if fmt in ("Auto-detect", "Script format (--pos)"):
                    if t.startswith("--pos") or t.startswith("--POS"):
                        rest = re.sub(r"^--pos\s*", "", t, flags=re.IGNORECASE).strip()
                        if rest.startswith('"') and rest.endswith('"'): rest = rest[1:-1]
                        elif rest.startswith("'") and rest.endswith("'"): rest = rest[1:-1]
                        imported.append(rest.strip()); continue
                    elif fmt == "Auto-detect" and (t.startswith("--neg") or t.startswith("--NEG")): continue
                    elif fmt == "Script format (--pos)": continue
                imported.append(t)
            if not imported: return '<span style="color:orange">No prompts found.</span>'
            existing = load()
            names = {p["name"] for p in existing}
            for i, t in enumerate(imported):
                n = unique_name(f"Imported {i+1}", names)
                existing.append({"name": n, "text": t, "favorite": False, "tags": []})
                names.add(n)
            save(existing)
            return f'<span style="color:green">Imported {len(imported)} prompt(s) from text.</span>'
        import_btn.click(fn=_imp, inputs=[import_file, import_fmt], outputs=[import_status])

        return []
