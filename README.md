# Malbuch-Bildgenerator

Dieses Tool verwendet die OpenAI DALL-E 3 API, um automatisch Bilder im Stil von Malbüchern aus einer Liste von Text-Prompts zu erstellen.

## Features

- **Bulk-Generierung**: Erzeugt mehrere Bilder auf einmal, basierend auf den Einträgen in `prompts.txt`.
- **Angepasster Stil**: Fügt automatisch Anweisungen zu jedem Prompt hinzu, um den idealen Malbuch-Look zu erzielen (klare Linien, schwarz-weiß, keine Schattierung).
- **Einfache Konfiguration**: Benötigt nur einen OpenAI API-Schlüssel.
- **Organisierte Ausgabe**: Speichert alle generierten Bilder in einem separaten Ordner (`generated_images`).
- **PDF-Export**: Fasst alle generierten Bilder automatisch in einer einzigen, druckfertigen PDF-Datei namens `Malbuch.pdf` zusammen.

## Setup und Installation

Folgen Sie diesen Schritten, um das Tool einzurichten und zu verwenden.

### 1. Abhängigkeiten installieren

Stellen Sie sicher, dass Sie Python 3 auf Ihrem System installiert haben. Führen Sie dann den folgenden Befehl im Projektverzeichnis aus, um die notwendigen Python-Bibliotheken zu installieren:

```bash
pip install -r requirements.txt
```

### 2. OpenAI API-Schlüssel einrichten

Das Skript benötigt einen OpenAI API-Schlüssel, um Bilder generieren zu können.

1.  Erstellen Sie eine neue Datei im Hauptverzeichnis des Projekts und nennen Sie sie `.env`.
2.  Öffnen Sie die `.env`-Datei und fügen Sie die folgende Zeile ein. Ersetzen Sie `"dein_secret_api_key_hier"` durch Ihren tatsächlichen OpenAI API-Schlüssel.

    ```
    OPENAI_API_KEY="dein_secret_api_key_hier"
    ```

Das Skript lädt diesen Schlüssel automatisch, ohne dass Sie ihn direkt im Code preisgeben müssen.

## Konfiguration anpassen

Über die Datei `config.ini` können Sie das Verhalten des Generators anpassen.

-   **`style_suffix`**: Dieser Text wird an jeden Ihrer Prompts angehängt. Standardmäßig ist er so eingestellt, dass er Bilder im Malbuch-Stil erzeugt. Sie können diesen Wert ändern, um völlig andere Stile zu erhalten.

    *Beispiel für einen fotorealistischen Stil:*
    ```ini
    style_suffix = , photorealistic, 4k, high detail
    ```
    *Beispiel für einen Aquarell-Stil:*
    ```ini
    style_suffix = , in a watercolor painting style, vibrant colors
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
