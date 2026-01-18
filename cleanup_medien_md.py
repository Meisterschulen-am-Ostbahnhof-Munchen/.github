import os
import re

MEDIA_FILE = ".github/docs/medien.md"

def normalize_aggressive(text):
    t = text.lower()
    t = t.replace("ü", "ue").replace("ö", "oe").replace("ä", "ae").replace("ß", "ss")
    return re.sub(r'[^a-z0-9]', '', t)

def cleanup():
    if not os.path.exists(MEDIA_FILE):
        if os.path.exists("docs/medien.md"):
             MEDIA_FILE_PATH = "docs/medien.md"
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
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith("## 🎧 Podcasts"):
            current_section = "PODCASTS"
            output_lines.append(line)
            continue
        elif stripped.startswith("## 📺 YouTube Videos"):
            current_section = "YOUTUBE"
            output_lines.append(line)
            continue
        elif stripped.startswith("## 📂 Thematische Übersicht"):
            current_section = "THEMATIC"
            output_lines.append(line)
            continue
        elif stripped.startswith("## ") and not stripped.startswith("###") and current_section in ["YOUTUBE", "THEMATIC"]:
             current_section = "REST"
             output_lines.append(line)
             continue

        if current_section == "PODCASTS":
            match = re.search(r"\* \[(.*?)\]\((.*?)\)", line)
            if match:
                title = match.group(1)
                norm = normalize_aggressive(title)
                if len(norm) > 3: # Ignore very short (e.g. empty due to non-latin chars) titles
                    podcasts_titles.append(norm)
            output_lines.append(line)
            
        elif current_section == "YOUTUBE":
            match = re.search(r"\* \[(.*?)\]\((.*?)\)", line)
            if match:
                title = match.group(1)
                t_agg = normalize_aggressive(title)
                
                is_duplicate = False
                for p_agg in podcasts_titles:
                    # Require minimum length for both sides to avoid false positives
                    if len(t_agg) > 15 and len(p_agg) > 5 and (t_agg in p_agg or p_agg in t_agg):
                        is_duplicate = True
                        removed_count += 1
                        break
                
                if is_duplicate:
                    continue 
            
            output_lines.append(line)

        elif current_section == "THEMATIC":
            if "youtube.com" in line or "youtu.be" in line:
                 # Remove known prefixes to avoid polluting the title extraction
                 clean_line = line.replace("**[YouTube]**", "").replace("**[ YouTube ]**", "")
                 links = re.findall(r"\[(.*?)\]\((https?://.*?)\)", clean_line)
                 if links:
                     title, url = links[-1]
                     if "youtube" in url or "youtu.be" in url:
                         t_agg = normalize_aggressive(title)
                         
                         is_duplicate = False
                         for p_agg in podcasts_titles:
                             if len(t_agg) > 15 and len(p_agg) > 5 and (t_agg in p_agg or p_agg in t_agg):
                                 is_duplicate = True
                                 removed_count += 1
                                 break
                         
                         if is_duplicate:
                             continue
            output_lines.append(line)
            
        else:
            output_lines.append(line)

    with open(MEDIA_FILE_PATH, "w", encoding="utf-8") as f:
        f.writelines(output_lines)
    print(f"Cleanup complete. Removed {removed_count} duplicate YouTube videos.")

if __name__ == "__main__":
    cleanup()
