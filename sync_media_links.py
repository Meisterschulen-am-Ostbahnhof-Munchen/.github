import os
import re

MEDIA_FILE = ".github/docs/medien.md"
WIKIS = [
    ".github/docs",
    "Install-ISOBUS-Environment-docs/docs",
    "ISOBUS-VT-Objects-docs/docs",
    "ISOBUS-other-docs/docs",
    "visual-programming-languages-docs/docs",
    "werkzeug-docs/docs"
]

def parse_medien_db():
    db = {'videos': [], 'podcasts': []}
    if not os.path.exists(MEDIA_FILE): return db
    with open(MEDIA_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Sichereres Splitting der Sektionen
    try:
        parts = content.split("## 📂 Thematische Übersicht")[0].split("## 📺 YouTube Videos")
        pod_content = parts[0]
        yt_content = parts[1] if len(parts) > 1 else ""
        db['podcasts'] = re.findall(r"\* \[(.*?)\]\((.*?)\)", pod_content)
        db['videos'] = re.findall(r"\* \[(.*?)\]\((.*?)\)", yt_content)
    except:
        print("Fehler beim Parsen der medien.md")
    return db

def normalize_ex_id(text):
    if not text: return None
    # Extrahiert Nummersteil und entfernt führende Nullen (z.B. 010b2 -> 10b2)
    match = re.search(r"uebung[ _](0*)(\w+)", text.lower())
    return match.group(2) if match else None

def get_isobus_id(text):
    match = re.search(r"id[- ](\d+)", text.lower())
    return match.group(1) if match else None

def sync_file(path, db):
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.rstrip() for line in f.readlines()]
    
    filename = os.path.basename(path)
    h1_title = ""
    for l in lines:
        if l.startswith("# "):
            h1_title = l.lstrip("# ").strip()
            break

    # Bestimme die Ziel-IDs für diese Datei
    target_ex = normalize_ex_id(filename) or normalize_ex_id(h1_title)
    target_id = get_isobus_id(filename) or get_isobus_id(h1_title)
    
    # 1. Sammle passende Medien
    def get_matches(media_list, ex_id, iso_id, current_title):
        matches = []
        for title, link in media_list:
            score = 0
            m_ex = normalize_ex_id(title)
            m_iso = get_isobus_id(title)
            
            if ex_id and m_ex == ex_id: score += 100
            elif ex_id and m_ex: score -= 50
            
            if iso_id and m_iso == iso_id: score += 90
            elif iso_id and m_iso: score -= 40
            
            # Text-Matching auf signifikante Wörter
            t_clean = re.sub(r'[^a-z0-9]', ' ', current_title.lower())
            m_clean = re.sub(r'[^a-z0-9]', ' ', title.lower())
            if t_clean in m_clean or m_clean in t_clean:
                score += 30
            
            if score > 20:
                matches.append((score, title, link))
        
        matches.sort(key=lambda x: x[0], reverse=True)
        # Unique links
        seen = set()
        unique = []
        for s, t, l in matches:
            if l not in seen:
                unique.append((s, t, l))
                seen.add(l)
        return unique[:5]

    matched_v = get_matches(db['videos'], target_ex, target_id, h1_title)
    matched_p = get_matches(db['podcasts'], target_ex, target_id, h1_title)

    # 2. Bereinige die Datei vorsichtig
    final_lines = []
    skip = False
    for line in lines:
        l_strip = line.strip()
        # Start einer Mediensektion
        if l_strip.startswith("## 📺 Video") or l_strip.startswith("## Video") or \
           l_strip.startswith("## 🎧 Podcast") or l_strip.startswith("## Podcast") or \
           l_strip.startswith("<iframe src=\"https://creators.spotify.com"):
            skip = True
            continue
        
        if skip:
            # Ende der Mediensektion: Jeder neue Header oder Trenner
            if l_strip.startswith("## ") or l_strip.startswith("---") or l_strip.startswith("----"):
                skip = False
                # Den Trenner selbst behalten wir NICHT, wenn er direkt nach einer Sektion kommt 
                # (wir fügen eigene Trenner ein)
                if l_strip.startswith("---"):
                    continue
            else:
                continue
        
        if not skip:
            final_lines.append(line)

    # 3. Neue Sektionen einfügen (nach dem ersten H1-Block/Einleitung)
    insert_pos = 0
    for i, line in enumerate(final_lines):
        if i > 0 and (line.startswith("## ") or line.startswith("---")):
            insert_pos = i
            break
    if insert_pos == 0: insert_pos = min(5, len(final_lines))

    # Block zusammenbauen
    new_media_block = []
    if matched_v or matched_p:
        new_media_block.append("")
        new_media_block.append("---- ")
        
        if matched_v:
            new_media_block.append("")
            new_media_block.append("## 📺 Video")
            for s, t, l in matched_v:
                new_media_block.append(f"* [{t}]({l})")
        
        if matched_p:
            new_media_block.append("")
            new_media_block.append("## 🎧 Podcast")
            for s, t, l in matched_p:
                new_media_block.append(f"* [{t}]({l})")
        new_media_block.append("")

    # Einfügen
    for line in reversed(new_media_block):
        final_lines.insert(insert_pos, line)

    # 4. Speichern nur bei Änderungen
    new_content = "\n".join(final_lines).strip()
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content + "\n")
    
    if matched_v or matched_p:
        print(f"Synced: {path} ({len(matched_v)}V, {len(matched_p)}P)")

def main():
    db = parse_medien_db()
    for wiki in WIKIS:
        if not os.path.exists(wiki): continue
        for root, _, files in os.walk(wiki):
            for file in files:
                if file.endswith(".md") and file not in ["index.md", "medien.md"]:
                    try:
                        sync_file(os.path.join(root, file), db)
                    except Exception as e:
                        print(f"Fehler in {file}: {e}")

if __name__ == "__main__":
    main()