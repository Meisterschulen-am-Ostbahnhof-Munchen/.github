import os
import re

# Liste der Dokumentations-Verzeichnisse
directories = [
    ".github/docs",
    "Install-ISOBUS-Environment-docs/docs",
    "ISOBUS-VT-Objects-docs/docs",
    "ISOBUS-other-docs/docs",
    "visual-programming-languages-docs/docs",
    "werkzeug-docs/docs"
]

def process_file(file_path):
    content = None
    encodings = ['utf-8', 'latin-1', 'cp1252']
    
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue
            
    if content is None:
        print(f"Fehler: Konnte Kodierung von {file_path} nicht bestimmen.")
        return

    # Prüfen, ob bereits ein Index-Eintrag vorhanden ist
    if "```{index}" in content or ":::{index}" in content:
        return

    lines = content.splitlines()
    new_lines = []
    h1_found = False

    for line in lines:
        new_lines.append(line)
        # Suche nach der ersten H1 Überschrift (# Titel)
        if not h1_found and line.startswith("# "):
            title = line.lstrip("# ").strip()
            if title:
                # Index-Direktive einfügen
                new_lines.append("")
                new_lines.append("```{index} single: " + title)
                new_lines.append("```")
                h1_found = True

    if h1_found:
        try:
            # Immer als UTF-8 speichern für Konsistenz
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(new_lines) + "\n")
            print(f"Index hinzugefügt: {file_path} ({title})")
        except Exception as e:
            print(f"Fehler beim Schreiben von {file_path}: {e}")

def main():
    for d in directories:
        if not os.path.exists(d):
            print(f"Verzeichnis nicht gefunden: {d}")
            continue
        print(f"Verarbeite Verzeichnis: {d}...")
        for root, dirs, files in os.walk(d):
            for file in files:
                if file.endswith(".md"):
                    process_file(os.path.join(root, file))

if __name__ == "__main__":
    main()