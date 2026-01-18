import os
import re

WIKIS = [
    ".github/docs",
    "Install-ISOBUS-Environment-docs/docs",
    "ISOBUS-VT-Objects-docs/docs",
    "ISOBUS-other-docs/docs",
    "visual-programming-languages-docs/docs",
    "werkzeug-docs/docs"
]

# Bestimme Root-Verzeichnis (Parent von .github)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Wenn das Skript in .github liegt, ist Root eins höher.
# Aber wir wollen flexibel sein. Nehmen wir an, WIKIS sind relativ zu ROOT.
# Wir setzen ROOT auf CWD wenn wir annehmen, dass man es vom Root aufruft?
# Nein, besser wir machen die WIKIS relativ zum Skript.
# .github/docs ist im gleichen Ordner wie das Skript (fast, script in .github).
# Also script_dir = .../.github
# WIKIS[0] = script_dir/docs
# WIKIS[1] = script_dir/../Install...

ROOT_DIR = os.path.dirname(SCRIPT_DIR)

WIKIS = [
    os.path.join(ROOT_DIR, ".github", "docs"),
    os.path.join(ROOT_DIR, "Install-ISOBUS-Environment-docs", "docs"),
    os.path.join(ROOT_DIR, "ISOBUS-VT-Objects-docs", "docs"),
    os.path.join(ROOT_DIR, "ISOBUS-other-docs", "docs"),
    os.path.join(ROOT_DIR, "visual-programming-languages-docs", "docs"),
    os.path.join(ROOT_DIR, "werkzeug-docs", "docs")
]

MEDIEN_FILE = os.path.join(ROOT_DIR, ".github", "docs", "medien.md")

def collect_links():
    notebooks = [] 
    seen_links = set()

    print("Suche nach NotebookLM Links...")
    for wiki in WIKIS:
        if not os.path.exists(wiki): continue
        for root, _, files in os.walk(wiki):
            for file in files:
                if file.endswith(".md") and file != "medien.md":
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            content = f.read()
                            
                        # Suche nach Links
                        raw_links = re.findall(r'\((https://notebooklm\.google\.com[^)]+)\)', content)
                        
                        if raw_links:
                            file_title = file.replace(".md", "")
                            match_h1 = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                            if match_h1:
                                file_title = match_h1.group(1).strip()
                            
                            for link_item in raw_links:
                                if isinstance(link_item, tuple):
                                    link = link_item[0]
                                else:
                                    link = link_item
                                
                                link = str(link).strip("'" ).strip('"')

                                if link not in seen_links:
                                    notebooks.append({'title': file_title, 'link': link})
                                    seen_links.add(link)
                    except Exception as e:
                        print(f"Error reading {path}: {e}")
    return notebooks

def update_medien_md(notebooks):
    if not notebooks:
        print("Keine neuen NotebookLM Links gefunden.")
        return

    print(f"Gefunden: {len(notebooks)} eindeutige NotebookLM Links.")

    with open(MEDIEN_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    lines = ["## 📓 NotebookLM", ""]
    for nb in sorted(notebooks, key=lambda x: x['title']):
        lines.append(f"* [{nb['title']}]({nb['link']})")
    lines.append("")
    
    new_block = "\n".join(lines)

    if "## 📓 NotebookLM" in content:
        print("Aktualisiere existierende Sektion...")
        parts = re.split(r"(## 📓 NotebookLM)", content)
        if len(parts) >= 2:
            pre = parts[0]
            rest = content[len(pre) + len(parts[1]):] 
            next_header_match = re.search(r"\n## ", rest)
            if next_header_match:
                end_idx = next_header_match.start()
                post = rest[end_idx:]
            else:
                post = ""
            content = pre + new_block + post
        else:
            content += "\n" + new_block
    else:
        print("Erstelle neue Sektion am Ende...")
        if not content.endswith("\n"):
            content += "\n"
        content += "\n" + new_block

    with open(MEDIEN_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Fertig. {MEDIEN_FILE} aktualisiert.")

if __name__ == "__main__":
    nbs = collect_links()
    update_medien_md(nbs)