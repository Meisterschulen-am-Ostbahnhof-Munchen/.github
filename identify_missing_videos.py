import os
import re

# Pfade
MEDIA_FILE = ".github/docs/medien.md"
WIKIS = [
    (".github/docs", "Wiki 0: Haupt-Wiki"),
    ("Install-ISOBUS-Environment-docs/docs", "Wiki 1: C-Programmierung"),
    ("ISOBUS-VT-Objects-docs/docs", "Wiki 2: Virtual Terminal"),
    ("ISOBUS-other-docs/docs", "Wiki 3: ISOBUS Technik"),
    ("visual-programming-languages-docs/docs", "Wiki 4: Visuelle Sprachen"),
    ("werkzeug-docs/docs", "Wiki 5: Werkzeuge")
]

IGNORE_TITLES = [
    "index", "home", "welcome", "contents", "indices and tables", 
    "genindex", "search", "nützliche links", "navigation", "startseite",
    "coming soon", "medien-bibliothek"
]

def get_covered_topics():
    if not os.path.exists(MEDIA_FILE):
        return []
    with open(MEDIA_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    # Extrahiere Titel aus [Titel](Link)
    titles = re.findall(r"[(.*?)]", content)
    return [t.lower() for t in titles]

def get_wiki_topics():
    wiki_topics = {} 
    
    for wiki_path, wiki_label in WIKIS:
        wiki_topics[wiki_label] = []
        if not os.path.exists(wiki_path):
            continue
            
        for root, _, files in os.walk(wiki_path):
            for file in files:
                if file.endswith(".md"):
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            for line in f:
                                if line.startswith("# "):
                                    title = line.lstrip("# ").strip()
                                    # MD-Links bereinigen
                                    if "[" in title and "]" in title:
                                        title = title.split("[")[1].split("]")[0]
                                    
                                    clean_title = title.lower()
                                    is_ignored = False
                                    for ignore in IGNORE_TITLES:
                                        if ignore in clean_title:
                                            is_ignored = True
                                            break
                                            
                                    if not is_ignored and len(clean_title) > 2:
                                        wiki_topics[wiki_label].append(title)
                                    break
                    except:
                        continue
    return wiki_topics

def main():
    covered = get_covered_topics()
    all_wiki_topics = get_wiki_topics()
    
    # Gesamten abgedeckten Text für Volltextsuche aufbereiten
    covered_blob = " ".join(covered).lower()
    covered_blob = re.sub(r'[^a-z0-9]', ' ', covered_blob)
    
    missing_by_wiki = {}
    
    for wiki, topics in all_wiki_topics.items():
        missing_by_wiki[wiki] = []
        for topic in topics:
            t_low = topic.lower()
            t_clean = re.sub(r'[^a-z0-9]', ' ', t_low).strip()
            
            if not t_clean: continue

            # Heuristik für Abdeckung
            is_covered = False
            if t_clean in covered_blob:
                is_covered = True
            
            # Falls kein Treffer, signifikante Wörter prüfen
            if not is_covered:
                words = [w for w in t_clean.split() if len(w) > 4]
                for w in words:
                    if w in covered_blob:
                        is_covered = True
                        break
            
            if not is_covered:
                missing_by_wiki[wiki].append(topic)

    # Markdown generieren
    new_section = "\n## ⏳ Geplante Themen (Coming Soon)\n\n"
    new_section += "Für die folgenden Wiki-Themen sind aktuell noch keine dedizierten Videos oder Podcasts verfügbar. Diese sind in Planung:\n\n"
    
    found_any = False
    for wiki, topics in missing_by_wiki.items():
        if topics:
            # Duplikate filtern und sortieren
            unique_topics = sorted(list(set(topics)))
            if unique_topics:
                found_any = True
                new_section += f"### {wiki}\n"
                for t in unique_topics:
                    new_section += f"* {t} (coming soon)\n"
                new_section += "\n"

    if not found_any:
        print("Alle Themen scheinen abgedeckt zu sein.")
        return

    # In medien.md schreiben
    with open(MEDIA_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Vorhandene Coming-Soon Sektion entfernen falls vorhanden
    if "## ⏳ Geplante Themen" in content:
        content = content.split("## ⏳ Geplante Themen")[0].strip()
    
    content = content.strip() + "\n\n" + new_section.strip() + "\n"

    with open(MEDIA_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    
    print("medien.md wurde erfolgreich aktualisiert.")

if __name__ == "__main__":
    main()