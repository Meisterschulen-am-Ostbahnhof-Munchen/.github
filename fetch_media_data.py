import feedparser
import yt_dlp
import os

# Konfiguration
podcasts = {
    "Eclipse 4diac (DE)": "https://anchor.fm/s/107cb3bb4/podcast/rss",
    "Eclipse 4diac (EN)": "https://anchor.fm/s/107d0665c/podcast/rss",
    "IEC 61499 Grundkurs (DE)": "https://anchor.fm/s/107ca346c/podcast/rss",
    "IEC 61499 Prime Course (EN)": "https://anchor.fm/s/107cec338/podcast/rss",
    "ISOBUS VT Objects": "https://anchor.fm/s/107caef88/podcast/rss",
    "logiBUS": "https://anchor.fm/s/107cb03d8/podcast/rss",
    "MS-MUC LAMA": "https://anchor.fm/s/107cb4c1c/podcast/rss"
}

youtube_channel_url = "https://www.youtube.com/@ms-muc-lama/videos"

# Themen-Kategorien (Keywords)
THEMES = {
    "ISOBUS": ["isobus", "vt", "virtual terminal", "pool", "aux"],
    "4diac / IEC 61499": ["4diac", "61499", "forte", "function block"],
    "Landtechnik / LAMA": ["lama", "traktor", "landmaschine", "pflug", "saemaschine"],
    "Elektronik / Werkzeug": ["loeten", "oszilloskop", "netzteil", "crimpen", "multimeter"],
    "Programmierung": ["python", " c ", "programmieren", "coder", "architekt"],
}

def get_podcast_data():
    all_episodes = {}
    podcast_titles = set()
    for name, url in podcasts.items():
        print(f"Lade Podcast: {name}...")
        feed = feedparser.parse(url)
        episodes = []
        for entry in feed.entries:
            episodes.append({"title": entry.title, "link": entry.link, "source": name})
            podcast_titles.add(entry.title.lower())
        all_episodes[name] = episodes
    return all_episodes, podcast_titles

def get_youtube_data(exclude_titles):
    print("Lade YouTube Videos (dies kann einen Moment dauern)...")
    ydl_opts = {
        'quiet': True,
        'extract_flat': 'in_playlist',
        'force_generic_extractor': True
    }
    videos = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(youtube_channel_url, download=False)
        if 'entries' in result:
            for entry in result['entries']:
                # Filtere Shorts (YT markiert sie oft nicht im flat extract, aber wir prüfen Titel/ID)
                # Reguläre Videos haben meist keine "shorts" im Pfad bei der URL
                title = entry.get('title')
                url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                
                # Ausschlusskriterien:
                # 1. Keine Shorts (einfache Heuristik: 'shorts' in URL)
                if '/shorts/' in url:
                    continue
                # 2. Keine Podcasts (Dubletten-Check via Titel)
                if title.lower() in exclude_titles:
                    continue
                
                videos.append({"title": title, "link": url, "source": "YouTube"})
    return videos

def categorize(items):
    categorized = {theme: [] for theme in THEMES}
    categorized["Sonstiges"] = []
    
    for item in items:
        found = False
        title_lower = item["title"].lower()
        for theme, keywords in THEMES.items():
            if any(kw in title_lower for kw in keywords):
                categorized[theme].append(item)
                found = True
                break
        if not found:
            categorized["Sonstiges"].append(item)
    return categorized

def generate_markdown():
    pod_data, podcast_titles = get_podcast_data()
    yt_data = get_youtube_data(podcast_titles)
    
    md = "# 🎙️ Medien-Bibliothek\n\n"
    md += "Hier finden Sie eine Übersicht aller Videos und Podcasts der Meisterschulen am Ostbahnhof München.\n\n"
    md += "```{index} single: Medien-Bibliothek\n```\n"
    md += "```{index} single: Podcasts\n```\n"
    md += "```{index} single: YouTube-Videos\n```\n\n"

    # 1. Podcasts Sektion
    md += "## 🎧 Podcasts\n\n"
    for name, episodes in pod_data.items():
        md += f"### {name}\n"
        # Alphabetisch sortieren
        sorted_eps = sorted(episodes, key=lambda x: x["title"].lower())
        for ep in sorted_eps:
            md += f"* [{ep['title']}]({ep['link']})\n"
        md += "\n"

    # 2. YouTube Sektion
    md += "## 📺 YouTube Videos\n\n"
    md += "*(Ohne Shorts und ohne Podcast-Dubletten)*\n\n"
    sorted_yt = sorted(yt_data, key=lambda x: x["title"].lower())
    for vid in sorted_yt:
        md += f"* [{vid['title']}]({vid['link']})\n"
    md += "\n"

    # 3. Thematische Liste
    md += "## 📂 Thematische Übersicht\n\n"
    all_media = []
    for eps in pod_data.values(): all_media.extend(eps)
    all_media.extend(yt_data)
    
    themed = categorize(all_media)
    for theme, items in themed.items():
        if items:
            md += f"### {theme}\n"
            for item in sorted(items, key=lambda x: x["title"].lower()):
                md += f"* **[{item['source']}]** [{item['title']}]({item['link']})\n"
            md += "\n"

    # Datei schreiben
    file_path = ".github/docs/medien.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Datei erstellt: {file_path}")

    # Index.md verlinken
    index_path = ".github/docs/index.md"
    with open(index_path, "r", encoding="utf-8") as f:
        index_content = f.read()
    
    if "medien.md" not in index_content:
        # Füge Link unter Nützliche Links hinzu
        updated_index = index_content.replace(
            "* [🔍 Super-Suche (alle Wikis)](https://meisterschulen-am-ostbahnhof-munchen-docs.readthedocs.io/de/latest/)",
            "* [🔍 Super-Suche (alle Wikis)](https://meisterschulen-am-ostbahnhof-munchen-docs.readthedocs.io/de/latest/)\n* [🎙️ Medien-Bibliothek (Videos & Podcasts)](medien.md)"
        )
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(updated_index)
        print("Link in index.md hinzugefügt.")

if __name__ == "__main__":
    generate_markdown()
