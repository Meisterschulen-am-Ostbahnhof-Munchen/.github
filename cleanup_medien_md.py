import os
import re

MEDIA_FILE = ".github/docs/medien.md"

def normalize_aggressive(text):
    t = text.lower()
    t = t.replace("ü", "ue").replace("ö", "oe").replace("ä", "ae").replace("ß", "ss")
    return re.sub(r'[^a-z0-9]', '', t)

def cleanup():
    if not os.path.exists(MEDIA_FILE):
        # Falls wir im .github Ordner sind, gehe eins hoch oder passe Pfad an
        if os.path.exists("docs/medien.md"):
             MEDIA_FILE_PATH = "docs/medien.md"
        elif os.path.exists("../.github/docs/medien.md"): # Fallback from root logic? No.
             MEDIA_FILE_PATH = "../.github/docs/medien.md"
        else:
             print(f"File not found: {MEDIA_FILE}")
             return
    else:
        MEDIA_FILE_PATH = MEDIA_FILE

    print(f"Processing {MEDIA_FILE_PATH}...")

    with open(MEDIA_FILE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    output_lines = []
    podcasts_titles = []
    removed_count = 0
    
    current_section = "HEAD"
    
    # Pre-Scan Podcasts to have full list before filtering YouTube
    # Weil "Podcasts" VOR "YouTube" kommt in der Datei, können wir on-the-fly sammeln.
    
    for line in lines:
        stripped = line.strip()
        
        # Sektions-Erkennung
        if stripped.startswith("## 🎧 Podcasts"):
            current_section = "PODCASTS"
            output_lines.append(line)
            continue
        elif stripped.startswith("## 📺 YouTube Videos"):
            current_section = "YOUTUBE"
            output_lines.append(line)
            continue
        elif stripped.startswith("## 📂 Thematische Übersicht"):
            current_section = "REST"
            output_lines.append(line)
            continue
        elif stripped.startswith("## ") and current_section == "YOUTUBE":
             # Ein anderer Header beendet YouTube Sektion (falls Thematische Übersicht umbenannt wurde)
             current_section = "REST"
             output_lines.append(line)
             continue

        if current_section == "PODCASTS":
            # Sammle Titel aus Link-Zeilen
            match = re.search(r"\* \[(.*?)\]\((.*?)\)", line)
            if match:
                title = match.group(1)
                podcasts_titles.append(normalize_aggressive(title))
            output_lines.append(line)
            
        elif current_section == "YOUTUBE":
            # Filtern
            match = re.search(r"\* \[(.*?)\]\((.*?)\)", line)
            if match:
                title = match.group(1)
                t_agg = normalize_aggressive(title)
                
                is_duplicate = False
                for p_agg in podcasts_titles:
                    # Fuzzy Match
                    if len(t_agg) > 15 and (t_agg in p_agg or p_agg in t_agg):
                        is_duplicate = True
                        removed_count += 1
                        # print(f"Removing Duplicate Video: {title}")
                        break
                
                if is_duplicate:
                    continue # Zeile überspringen
            
            output_lines.append(line)
            
        else:
            output_lines.append(line)

    with open(MEDIA_FILE_PATH, "w", encoding="utf-8") as f:
        f.writelines(output_lines)
    print(f"Cleanup complete. Removed {removed_count} duplicate YouTube videos.")

if __name__ == "__main__":
    cleanup()
