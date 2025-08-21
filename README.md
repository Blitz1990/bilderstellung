# Malbuch-Bildgenerator

Dieses Tool verwendet KI, um automatisch Bilder im Stil von Malbüchern (oder anderen Stilen) aus einer Liste von Text-Prompts zu erstellen. Es unterstützt mehrere KI-Anbieter.

## Features

- **Multi-API-Unterstützung**: Wählen Sie zwischen verschiedenen KI-Anbietern (`OpenAI`, `StabilityAI`), um Bilder zu generieren.
- **Bulk-Generierung**: Erzeugt mehrere Bilder auf einmal aus der `prompts.txt`-Datei.
- **Anpassbare Stile**: Passen Sie den Bildstil für jeden Anbieter individuell in der `config.ini`-Datei an.
- **PDF-Export**: Fasst alle generierten Bilder automatisch in einer einzigen, druckfertigen PDF-Datei (`Malbuch.pdf`) zusammen.

## Setup und Installation

### 1. Abhängigkeiten installieren

Stellen Sie sicher, dass Sie Python 3 auf Ihrem System installiert haben. Führen Sie dann den folgenden Befehl im Projektverzeichnis aus, um die notwendigen Python-Bibliotheken zu installieren:

```bash
pip install -r requirements.txt
```

### 2. API-Schlüssel einrichten

Das Skript benötigt API-Schlüssel für die Dienste, die Sie verwenden möchten. Sie müssen diese als Umgebungsvariablen einrichten.

1.  Erstellen Sie eine neue Datei im Hauptverzeichnis des Projekts und nennen Sie sie `.env`.
2.  Öffnen Sie die `.env`-Datei und fügen Sie die Schlüssel für die Dienste hinzu, die Sie nutzen möchten. Sie müssen nicht beide hinzufügen, nur den/die, den/die Sie in `config.ini` auswählen.

    ```
    # Ihr Schlüssel von platform.openai.com
    OPENAI_API_KEY="dein_openai_api_key"

    # Ihr Schlüssel von platform.stability.ai
    STABILITY_API_KEY="dein_stability_api_key"
    ```

Das Skript lädt den entsprechenden Schlüssel automatisch, basierend auf Ihrer Anbieterauswahl in `config.ini`.

## Konfiguration (`config.ini`)

Die Hauptkonfiguration erfolgt über die `config.ini`-Datei.

### Anbieter auswählen
Im `[General]`-Abschnitt wählen Sie den zu verwendenden Anbieter.

```ini
[General]
# Optionen: openai, stabilityai
provider = openai
```

### Stile anpassen
In den anbieterspezifischen Abschnitten (`[OpenAI]`, `[StabilityAI]`) können Sie den Stil für jeden Dienst anpassen. Jeder Anbieter reagiert unterschiedlich auf Prompts, daher können Sie hier für jeden den optimalen Stil definieren.

-   **`style_suffix`**: Dieser Text wird an jeden Ihrer Prompts angehängt.

*Beispiel für OpenAI:*
```ini
[OpenAI]
style_suffix = , for a children's coloring book, simple, clean lines, black and white, vector illustration, no shading
```

*Beispiel für StabilityAI:*
```ini
[StabilityAI]
style_suffix = , coloring book page, line art, black and white
```

## Wie man das Tool benutzt

### 1. Prompts hinzufügen

Öffnen Sie die Datei `prompts.txt`. Fügen Sie hier Ihre Ideen für Bilder ein, eine Idee pro Zeile. Zum Beispiel:

```
Ein niedliches Einhorn das über einen Regenbogen springt
Ein Rennauto auf einer Rennstrecke
Ein Schloss im Weltraum
```

### 2. Das Skript ausführen

Öffnen Sie Ihr Terminal oder Ihre Kommandozeile, navigieren Sie zum Projektordner und führen Sie das Skript mit dem folgenden Befehl aus:

```bash
python image_generator.py
```

Das Skript wird nun beginnen, für jeden Prompt in `prompts.txt` ein Bild zu generieren. Sie werden den Fortschritt im Terminal sehen.

### 3. Ergebnisse finden

Die fertigen Bilder werden im Ordner `generated_images` als `.png`-Dateien gespeichert. Der Dateiname wird aus dem jeweiligen Prompt abgeleitet.

Zusätzlich wird eine Datei namens `Malbuch.pdf` im Hauptverzeichnis erstellt, die alle Bilder als druckfertiges Malbuch enthält.

---
Viel Spaß beim Erstellen Ihrer Malbuchseiten!
