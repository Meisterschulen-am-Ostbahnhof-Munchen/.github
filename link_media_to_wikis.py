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

def parse_medien_md():
    media_db = {'videos': [], 'podcasts': []}
    if not os.path.exists(MEDIA_FILE):
        return media_db

    with open(MEDIA_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Sektionen trennen
    pod_part = content.split("## 🎧 Podcasts")[1].split("## 📺 YouTube Videos")[0]
    yt_part = content.split("## 📺 YouTube Videos")[1].split("## 📂 Thematische Übersicht")[0]

    # Extrahiere Titel aus [Titel](Link)
    def extract(text):
        return re.findall(r"\* \[(.*?)\]\((.*?)\)", text)

    for title, link in extract(pod_part):
        media_db['podcasts'].append({'title': title, 'link': link})
    
    # Deduplizierung: Liste für Fuzzy-Check (Aggressive Normalisierung)
    pod_titles_agg = [normalize_aggressive(p['title']) for p in media_db['podcasts']]

    for title, link in extract(yt_part):
        # Check ob Video ein Podcast-Mirror ist
        t_agg = normalize_aggressive(title)
        
        is_duplicate = False
        for p_agg in pod_titles_agg:
            # Wenn Titel sehr ähnlich sind (Substring Match), und lang genug
            if len(t_agg) > 20 and (t_agg in p_agg or p_agg in t_agg):
                is_duplicate = True
                break
        
        if is_duplicate:
            continue
            
        media_db['videos'].append({'title': title, 'link': link})

    return media_db

def normalize(text):
    t = text.lower()
    t = t.replace("ü", "ue").replace("ö", "oe").replace("ä", "ae").replace("ß", "ss")
    return re.sub(r'[^a-z0-9]', ' ', t)

def normalize_aggressive(text):
    t = text.lower()
    t = t.replace("ü", "ue").replace("ö", "oe").replace("ä", "ae").replace("ß", "ss")
    return re.sub(r'[^a-z0-9]', '', t)

def find_matches(file_title, filename, media_list):
    matches = []
    fname_clean = filename.lower().replace(".md", "")
    title_norm = normalize(file_title)
    title_agg = normalize_aggressive(file_title)
    fname_agg = normalize_aggressive(fname_clean)
    
    # Suche nach Übungs-Mustern (z.B. 010b2)
    exercise_match = re.search(r"uebung_(\w+)", fname_clean) or re.search(r"uebung\s*(\w+)", title_norm)
    obj_id_match = re.search(r"id-(\d+)", fname_clean) or re.search(r"id\s*(\d+)", title_norm)

    for item in media_list:
        m_title = item['title'].lower()
        m_title_norm = normalize(item['title'])
        m_title_agg = normalize_aggressive(item['title'])
        
        score = 0
        # 1. Prio: Übungsnummer Match
        if exercise_match:
            num = exercise_match.group(1).lower()
            clean_title = m_title.replace("ü", "ue")
            if num in clean_title:
                score += 100
            elif num.lstrip("0") in clean_title and len(num.lstrip("0")) > 1:
                 score += 100
        
        # 2. Prio: ISOBUS ID Match
        if obj_id_match:
            oid = obj_id_match.group(1)
            # Match "ID X" oder "ID-X"
            if f"id {oid}" in m_title or f"id-{oid}" in m_title:
                score += 90

        # 3. Prio: Titel-Überschneidung (Standard)
        if fname_clean in m_title or m_title in fname_clean:
            score += 50
        
        # 3b. Prio: Aggressiver Titel Match (z.B. "Soft Key" in "Softkeys")
        # Prüfe ob signifikante Teile des Dateinamens im Titel vorkommen
        # Wir nehmen den Dateinamen ohne "id", "iso", zahlen etc.
        # Einfacher: Ist der aggressive String im aggressiven Titel enthalten?
        # Z.B. file: "id05keysoftkey..." -> video: "iso...softkeys..."
        # Das matcht so nicht direkt.
        
        # Besser: Token Match mit aggressiver Normalisierung
        # File tokens: "key", "soft", "key"
        # Video tokens: "softkeys"
        # "softkey" in "softkeys" -> JA!
        
        # Zerlege Filename in Wörter (Standard)
        f_words = title_norm.split()
        m_words_agg = m_title_agg # Ganzer Titel als Wurst
        
        match_count = 0
        for w in f_words:
            if len(w) > 3: # Ignoriere "id", "iso", "the" etc wenn möglich (aber ISO ist wichtig)
                # Suche das Wort (aggressiv) im aggressiven Titel
                if w in m_words_agg:
                    score += 15
                    match_count += 1
        
        # Bonus für "Softkey" Spezialfall (zusammengesetzte Wörter)
        if "softkey" in title_agg and "softkey" in m_title_agg:
             score += 40

        if score > 0:
            matches.append((score, item))

    # Sortieren nach Score, dann die besten 5
    matches.sort(key=lambda x: x[0], reverse=True)
    # Nur Matches mit Score >= 50 behalten (verhindert Spam durch schwache Wort-Matches)
    matches = [m for m in matches if m[0] >= 50]

    unique_links = []
    result = []
    for score, item in matches:
        if item['link'] not in unique_links:
            result.append(item)
            unique_links.append(item['link'])
        if len(result) >= 5:
            break
    return result

def remove_section(content, header):
    lines = content.splitlines()
    new_lines = []
    skip = False
    for line in lines:
        if header in line:
            skip = True
            continue
        if skip:
            # Stop skipping at next header or separator (but be careful not to catch list items)
            s = line.strip()
            if s.startswith("## ") or s.startswith("----") or s.startswith("```{") or s.startswith(":::{"):
                skip = False
            else:
                continue
        new_lines.append(line)
    return "\n".join(new_lines)

def clean_file(content):
    c = remove_section(content, "## 📺 Video")
    c = remove_section(c, "## 🎧 Podcast")
    c = remove_section(c, "## Video")
    c = remove_section(c, "## Podcast")
    # Remove Spotify Iframes
    c = re.sub(r'<iframe.*?src=".*?spotify.*?".*?></iframe>', '', c, flags=re.DOTALL | re.IGNORECASE)
    # Remove empty lines excess
    c = re.sub(r'\n{3,}', '\n\n', c)
    return c

def update_file(path, videos, podcasts):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Zuerst aufräumen
    content = clean_file(content)

    if not videos and not podcasts:
        # Wenn wir nichts hinzuzufügen haben, schreiben wir die bereinigte Version zurück (um Müll zu entfernen)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return

    lines = content.splitlines()
    
    # Helper to insert
    def insert_section(lines, title, items):
        # Einfügeposition finden: Nach YAML header, nach Imports, vor Textstart?
        # Strategie: Nach der ersten Überschrift (Titel) und Index-Block.
        # Einfachste Heuristik: Zeile 5? Nein.
        # Suche nach Index Block Ende ```
        insert_idx = -1
        
        # Versuche eine gute Position zu finden (z.B. nach dem ersten Bild oder nach ToC)
        # Wenn '----' (Separator) da ist, davor?
        
        # Fallback: Nach dem ersten Header (Titel) und evtl. Index
        has_title = False
        for i, line in enumerate(lines):
            if line.startswith("# "):
                has_title = True
            if has_title and line.strip() == "```": # Ende vom Index Block
                insert_idx = i + 1
            if has_title and i > 5 and line.strip() == "": # Erste leere Zeile nach Header Bereich
                if insert_idx == -1: insert_idx = i
                
        # Wenn wir '----' finden, ist das meist ein guter Platz davor
        for i, line in enumerate(lines):
            if line.strip() == "----":
                insert_idx = i
                break
        
        if insert_idx == -1: insert_idx = len(lines)
        
        lines.insert(insert_idx, "")
        lines.insert(insert_idx, title)
        for item in reversed(items):
             lines.insert(insert_idx + 2, f"* [{item['title']}]({item['link']})")
        lines.insert(insert_idx + 2 + len(items), "")

    if videos:
        insert_section(lines, "## 📺 Video", videos)
        
    if podcasts:
        # Neu berechnen, da lines sich geändert haben
        insert_section(lines, "## 🎧 Podcast", podcasts)

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Updated: {path} (+{len(videos)} V, +{len(podcasts)} P)")

def main():
    db = parse_medien_md()
    print(f"Datenbank geladen: {len(db['videos'])} Videos, {len(db['podcasts'])} Podcasts.")

    for wiki in WIKIS:
        if not os.path.exists(wiki): continue
        for root, _, files in os.walk(wiki):
            for file in files:
                if file.endswith(".md") and file != "medien.md" and file != "index.md":
                    path = os.path.join(root, file)
                    file_title = ""
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            for line in f:
                                if line.startswith("# "):
                                    file_title = line.lstrip("# ").strip()
                                    break
                        
                        v_matches = find_matches(file_title, file, db['videos'])
                        p_matches = find_matches(file_title, file, db['podcasts'])
                        
                        update_file(path, v_matches, p_matches)
                    except:
                        continue

if __name__ == "__main__":
    main()
