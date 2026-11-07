#!/usr/bin/env python3
"""
review_agent.py
Automated PR Code Review Agent using the Google Antigravity SDK (google-antigravity).
Analyzes Git PR diffs for security vulnerabilities, logic bugs, and best practices.
"""

import asyncio
import os
import subprocess
import sys

try:
    from google.antigravity import Agent, LocalAgentConfig
except ImportError:
    print(
        "Fehler: Das Paket 'google-antigravity' ist nicht installiert. "
        "Bitte installiere es mit 'pip install google-antigravity'.",
        file=sys.stderr,
    )
    sys.exit(1)


def get_git_diff() -> str:
    """Ermittelt den Git-Diff zwischen dem Zielbranch (GITHUB_BASE_REF) und HEAD."""
    base_ref = os.getenv("GITHUB_BASE_REF", "main")

    # Sicherstellen, dass die Remote-Refs vorhanden sind
    try:
        subprocess.run(
            ["git", "fetch", "origin", base_ref],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass

    diff_cmd = ["git", "diff", f"origin/{base_ref}...HEAD"]
    try:
        diff_text = subprocess.check_output(
            diff_cmd,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return diff_text
    except subprocess.CalledProcessError as e:
        # Fallback auf HEAD~1 falls origin/<base_ref> nicht auflösbar ist
        try:
            return subprocess.check_output(
                ["git", "diff", "HEAD~1...HEAD"],
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except Exception:
            return f"Fehler beim Ermitteln des Git Diffs: {e.output}"


async def run_review(diff: str) -> str:
    """Führt das Code-Review mit dem Antigravity Agenten durch."""
    max_chars = 80000
    truncated = False
    if len(diff) > max_chars:
        diff = diff[:max_chars]
        truncated = True

    system_instructions = (
        "Du bist ein Senior Code Reviewer und Security Engineer für die "
        "Meisterschulen am Ostbahnhof München.\n"
        "Deine Aufgabe ist es, Pull-Request-Diffs gründlich, konstruktiv und präzise zu prüfen.\n\n"
        "Prüfkriterien:\n"
        "1. **Sicherheit:** Keine Secrets/API-Keys im Code, Schutz vor Injection (SQL/Command/XSS), "
        "unsichere Abhängigkeiten oder unzureichende Validierung.\n"
        "2. **Korrektheit & Logik:** Mögliche Bugs, unbehandelte Ausnahmen, Null/None-Pointer-Zugriffe, "
        "fehlende Fehlerbehandlung oder ungültige Randfälle.\n"
        "3. **Code-Qualität:** Lesbarkeit, Einhaltung von Best Practices, saubere Typisierung und Dokumentation.\n"
        "4. **Performance:** Ineffiziente Schleifen, unnötige Ressourcenbelegung oder Memory-Leaks.\n\n"
        "Format der Antwort (ausschließlich in sauberem Markdown):\n"
        "- **📋 Zusammenfassung:** 2-3 Sätze zum Zweck der Änderungen.\n"
        "- **🚨 Kritische Befunde:** Konkrete Probleme mit Datei- und Zeilenbezug (falls vorhanden) "
        "sowie konkreter Korrekturcode.\n"
        "- **💡 Empfehlungen:** Wartbarkeit, Best Practices und Stil.\n"
        "- **🏁 Verdict:**\n"
        "  - `✅ SHIP IT` (Keine Blocker, bereit zum Mergen)\n"
        "  - `⚠️ REVISE` (Verbesserungsvorschläge empfohlen, keine kritischen Blocker)\n"
        "  - `🛑 BLOCKED` (Kritische Sicherheits- oder Logikfehler vorhanden, Behebung zwingend erforderlich)"
    )

    config = LocalAgentConfig(
        system_instructions=system_instructions,
    )

    async with Agent(config) as agent:
        prompt_parts = [
            "Bitte überprüfe den folgenden Pull-Request-Diff auf Sicherheit, Korrektheit und Qualität:\n\n",
            "```diff\n",
            diff,
            "\n```",
        ]
        if truncated:
            prompt_parts.append(
                "\n\n*(Hinweis: Der Diff war sehr groß und wurde auf die ersten 80.000 Zeichen gekürzt.)*"
            )

        prompt = "".join(prompt_parts)
        response = await agent.chat(prompt)
        return await response.text()


def main():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    vertex_enabled = os.getenv("GOOGLE_GENAI_USE_VERTEXAI")

    if not api_key and not vertex_enabled:
        error_msg = (
            "### 🤖 AGY Automated Code Review - Warnung\n\n"
            "⚠️ Es wurde weder ein `GEMINI_API_KEY` noch eine Vertex AI Konfiguration gefunden. "
            "Bitte hinterlege `GEMINI_API_KEY` in den GitHub Actions Secrets."
        )
        print(error_msg, file=sys.stderr)
        with open("review_output.md", "w", encoding="utf-8") as f:
            f.write(error_msg)
        return

    print("Ermittle Git-Diff für den Pull Request...")
    diff = get_git_diff().strip()

    if not diff:
        print("Keine Code-Änderungen im Diff gefunden.")
        with open("review_output.md", "w", encoding="utf-8") as f:
            f.write("### 🤖 AGY Automated Code Review\n\n✅ Keine Code-Änderungen zur Überprüfung gefunden.")
        return

    print(f"Diff gefunden ({len(diff)} Zeichen). Starte Antigravity Agent...")
    try:
        review_markdown = asyncio.run(run_review(diff))
    except Exception as e:
        error_md = (
            f"### 🤖 AGY Automated Code Review - Fehler\n\n"
            f"Bei der Überprüfung mit dem Antigravity Agenten ist ein Fehler aufgetreten:\n\n"
            f"```\n{e}\n```"
        )
        print(f"Fehler beim Agent-Review: {e}", file=sys.stderr)
        with open("review_output.md", "w", encoding="utf-8") as f:
            f.write(error_md)
        return

    output_content = (
        "### 🤖 Antigravity AI Code Review\n\n"
        f"{review_markdown}\n\n"
        "---\n"
        "*Automatisch geprüft durch das [Google Antigravity SDK](https://github.com/google-antigravity/antigravity-sdk-python) "
        "im Repository [Meisterschulen-am-Ostbahnhof-Munchen/.github](https://github.com/Meisterschulen-am-Ostbahnhof-Munchen/.github).*"
    )

    with open("review_output.md", "w", encoding="utf-8") as f:
        f.write(output_content)

    print("Review erfolgreich in 'review_output.md' geschrieben.")


if __name__ == "__main__":
    main()
