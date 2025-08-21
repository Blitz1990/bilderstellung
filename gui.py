import customtkinter as ctk
from customtkinter import CTkImage
import configparser
import os
import threading
import queue
from image_logic import (
    OpenAIGenerator,
    StabilityAIGenerator,
    save_image,
    create_pdf_from_images
)
from dotenv import load_dotenv, set_key
from PIL import Image

# --- Constants ---
CONFIG_FILE = "config.ini"
PROMPTS_FILE = "prompts.txt"
ENV_FILE = ".env"
OUTPUT_DIR = "generated_images"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Malbuch Bild-Generator")
        self.geometry("1000x700")
        ctk.set_appearance_mode("dark")

        # --- Main Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.tabs.add("Generator")
        self.tabs.add("Galerie")
        self.tabs.add("Settings")
        self.tabs.add("Hilfe")

        # --- Queue for thread-safe logging ---
        self.log_queue = queue.Queue()

        # --- Setup Tabs ---
        self.setup_generator_tab()
        self.setup_gallery_tab()
        self.setup_settings_tab()
        self.setup_help_tab()

        # --- Load initial data ---
        self.load_settings()
        self.load_prompts()
        self.update_gallery() # Initial gallery load

        # --- Start polling the log queue ---
        self.after(100, self.process_log_queue)

    def setup_generator_tab(self):
        """Create the widgets for the Generator tab."""
        tab = self.tabs.tab("Generator")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        # --- Left Frame: Prompts ---
        prompts_frame = ctk.CTkFrame(tab)
        prompts_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        prompts_frame.grid_rowconfigure(1, weight=1)
        prompts_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(prompts_frame, text="Prompts", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.prompts_textbox = ctk.CTkTextbox(prompts_frame, font=("", 14))
        self.prompts_textbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        self.save_prompts_button = ctk.CTkButton(prompts_frame, text="Prompts speichern", command=self.save_prompts)
        self.save_prompts_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        # --- Right Frame: Actions & Log ---
        log_frame = ctk.CTkFrame(tab)
        log_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.generate_button = ctk.CTkButton(log_frame, text="Bilder generieren", command=self.start_generation_thread, height=40, font=ctk.CTkFont(size=14, weight="bold"))
        self.generate_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.log_textbox = ctk.CTkTextbox(log_frame, state="disabled", font=("", 13))
        self.log_textbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        self.open_pdf_button = ctk.CTkButton(log_frame, text="PDF öffnen", command=lambda: os.startfile("Malbuch.pdf") if os.path.exists("Malbuch.pdf") else None)
        self.open_pdf_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

    def setup_gallery_tab(self):
        """Create the widgets for the Gallery tab."""
        tab = self.tabs.tab("Galerie")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # --- Top Frame for Controls ---
        controls_frame = ctk.CTkFrame(tab)
        controls_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        refresh_button = ctk.CTkButton(controls_frame, text="Aktualisieren", command=self.update_gallery)
        refresh_button.pack(side="left", padx=10, pady=5)

        # --- Scrollable Frame for Images ---
        self.gallery_frame = ctk.CTkScrollableFrame(tab, label_text="Generierte Bilder")
        self.gallery_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

    def update_gallery(self):
        """Loads images from the output directory into the gallery view."""
        self.log("Galerie wird aktualisiert...")

        # Clear existing widgets in the gallery frame
        for widget in self.gallery_frame.winfo_children():
            widget.destroy()

        try:
            if not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR)

            image_files = sorted(
                [f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith('.png')],
                key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)),
                reverse=True
            )

            if not image_files:
                ctk.CTkLabel(self.gallery_frame, text="Noch keine Bilder generiert.").pack(pady=10)
                return

            for filename in image_files:
                filepath = os.path.join(OUTPUT_DIR, filename)

                # Create a frame for each image and its controls
                item_frame = ctk.CTkFrame(self.gallery_frame)
                item_frame.pack(pady=10, padx=10, fill="x")

                # Create thumbnail
                try:
                    img = Image.open(filepath)
                    img.thumbnail((150, 150))
                    ctk_img = CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))

                    img_label = ctk.CTkLabel(item_frame, image=ctk_img, text="")
                    img_label.pack(side="left", padx=10, pady=10)
                except Exception as e:
                    self.log(f"Fehler beim Laden des Thumbnails für {filename}: {e}")
                    img_label = ctk.CTkLabel(item_frame, text=f"Bild konnte nicht\ngeladen werden:\n{filename}")
                    img_label.pack(side="left", padx=10, pady=10)

                # Info label
                info_label = ctk.CTkLabel(item_frame, text=filename, anchor="w", justify="left")
                info_label.pack(side="left", padx=10, pady=10, expand=True, fill="x")

                # --- Interaction ---
                # Delete button
                delete_button = ctk.CTkButton(item_frame, text="Löschen", command=lambda f=filepath: self.delete_image(f))
                delete_button.pack(side="right", padx=10, pady=10)

                # Click to open
                def open_image_handler(f=filepath):
                    self.open_image(f)

                img_label.bind("<Button-1>", open_image_handler)
                info_label.bind("<Button-1>", open_image_handler)
                item_frame.bind("<Button-1>", open_image_handler)


        except Exception as e:
            self.log(f"Fehler beim Aktualisieren der Galerie: {e}")

    def delete_image(self, filepath):
        """Deletes an image file and refreshes the gallery."""
        try:
            os.remove(filepath)
            self.log(f"🗑️ Bild gelöscht: {os.path.basename(filepath)}")
            self.update_gallery()
        except Exception as e:
            self.log(f"❌ Fehler beim Löschen des Bildes {os.path.basename(filepath)}: {e}")

    def open_image(self, filepath):
        """Opens an image file in the default system viewer."""
        try:
            self.log(f"Öffne Bild: {os.path.basename(filepath)}...")
            if os.path.exists(filepath):
                os.startfile(filepath)
            else:
                self.log(f"❌ Fehler: Bild nicht gefunden unter {filepath}")
                self.update_gallery() # Refresh if file is missing
        except Exception as e:
            self.log(f"❌ Fehler beim Öffnen des Bildes: {e}")

    def setup_settings_tab(self):
        """Create the widgets for the Settings tab."""
        tab = self.tabs.tab("Settings")
        tab.grid_columnconfigure(0, weight=1)

        # --- API Keys Frame ---
        api_frame = ctk.CTkFrame(tab)
        api_frame.grid(row=0, column=0, padx=10, pady=10, sticky="new")
        api_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(api_frame, text="API Keys", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(api_frame, text="OpenAI API Key:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.openai_key_entry = ctk.CTkEntry(api_frame, show="*")
        self.openai_key_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(api_frame, text="StabilityAI API Key:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.stability_key_entry = ctk.CTkEntry(api_frame, show="*")
        self.stability_key_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # --- General Settings Frame ---
        general_frame = ctk.CTkFrame(tab)
        general_frame.grid(row=1, column=0, padx=10, pady=10, sticky="new")
        general_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(general_frame, text="Allgemeine Einstellungen", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(general_frame, text="Bild-Anbieter:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.provider_optionmenu = ctk.CTkOptionMenu(general_frame, values=["openai", "stabilityai"])
        self.provider_optionmenu.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # --- Style Suffixes Frame ---
        style_frame = ctk.CTkFrame(tab)
        style_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        style_frame.grid_columnconfigure(1, weight=1)
        style_frame.grid_rowconfigure(1, weight=1)
        style_frame.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(style_frame, text="Stil-Anpassungen", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(style_frame, text="OpenAI Stil Suffix:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.openai_style_textbox = ctk.CTkTextbox(style_frame, height=100)
        self.openai_style_textbox.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")

        ctk.CTkLabel(style_frame, text="StabilityAI Stil Suffix:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.stability_style_textbox = ctk.CTkTextbox(style_frame, height=100)
        self.stability_style_textbox.grid(row=2, column=1, padx=10, pady=5, sticky="nsew")

        # --- Save Button ---
        self.save_settings_button = ctk.CTkButton(tab, text="Einstellungen speichern", command=self.save_settings)
        self.save_settings_button.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

    def setup_help_tab(self):
        """Create the widgets for the Help tab with explanations."""
        tab = self.tabs.tab("Hilfe")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        scroll_frame = ctk.CTkScrollableFrame(tab, label_text="Hilfe & Anleitung")
        scroll_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        scroll_frame.grid_columnconfigure(0, weight=1)

        # --- Define fonts ---
        title_font = ctk.CTkFont(size=18, weight="bold", underline=True)
        subtitle_font = ctk.CTkFont(size=14, weight="bold")
        body_font = ctk.CTkFont(size=12)

        # --- Helper function to add content ---
        def add_section(parent, title, content):
            ctk.CTkLabel(parent, text=title, font=subtitle_font, anchor="w").pack(pady=(15, 5), padx=10, fill="x")
            ctk.CTkLabel(parent, text=content, font=body_font, anchor="w", justify="left", wraplength=700).pack(pady=0, padx=10, fill="x")

        # --- Introduction ---
        ctk.CTkLabel(scroll_frame, text="Anleitung zum Malbuch-Generator", font=title_font, anchor="w").pack(pady=10, padx=10, fill="x")

        # --- Generator Tab Section ---
        generator_content = (
            'Im "Generator"-Tab findet die eigentliche Bilderstellung statt.\n\n'
            'Prompts: Geben Sie hier Ihre Bildideen ein, eine Idee pro Zeile. Ein "Prompt" ist eine detaillierte Beschreibung dessen, was die KI zeichnen soll.\n'
            'Beispiel: Ein Astronaut, der auf einem Elefanten durch den Weltraum reitet\n\n'
            'Bilder generieren: Startet den Prozess. Für jeden Prompt wird ein Bild erstellt. Den Fortschritt können Sie im Log-Fenster auf der rechten Seite verfolgen.\n\n'
            'Prompts speichern: Sichert alle Prompts aus dem Textfeld in der Datei "prompts.txt".\n\n'
            'PDF öffnen: Nachdem die Bilder erstellt wurden, fasst das Tool alle in einer einzigen "Malbuch.pdf"-Datei zusammen. Dieser Knopf öffnet die PDF.'
        )
        add_section(scroll_frame, "Der Generator-Tab", generator_content)

        # --- Gallery Tab Section ---
        gallery_content = (
            'Die "Galerie" zeigt Ihnen alle Bilder an, die im Ordner "generated_images" gespeichert sind.\n\n'
            'Aktualisieren: Lädt die Ansicht neu. Nützlich, wenn Sie Bilder manuell im Ordner geändert haben.\n\n'
            'Auf ein Bild klicken: Öffnet das ausgewählte Bild in voller Größe mit Ihrem Standard-Bildbetrachtungsprogramm.\n\n'
            'Löschen: Entfernt das entsprechende Bild dauerhaft von Ihrer Festplatte.'
        )
        add_section(scroll_frame, "Die Galerie", gallery_content)

        # --- Settings Tab Section ---
        settings_content = (
            'Hier können Sie das Verhalten des Tools anpassen.\n\n'
            'API Keys: Tragen Sie hier Ihre persönlichen Schlüssel für die KI-Dienste ein. Ohne einen gültigen API-Schlüssel können keine Bilder generiert werden. Ihre Schlüssel werden nur lokal auf Ihrem Computer gespeichert.\n\n'
            'Bild-Anbieter: Wählen Sie den KI-Dienst, den Sie verwenden möchten. "openai" (DALL-E 3) und "stabilityai" haben unterschiedliche Stärken. Probieren Sie beide aus, um zu sehen, welcher Stil Ihnen besser gefällt.\n\n'
            'Stil-Suffix: Dies ist die wichtigste Einstellung, um den Malbuch-Stil zu erreichen. Der Text, den Sie hier eingeben, wird automatisch an jeden Ihrer Prompts angehängt. So geben Sie der KI die Anweisung, ein Bild in einem bestimmten Stil zu erstellen.\n'
            'Beispiel: , für ein Malbuch für Kinder, einfache klare Linien, schwarz und weiß, keine Schattierungen\n\n'
            'Einstellungen speichern: Sichert alle Änderungen auf dieser Seite.'
        )
        add_section(scroll_frame, "Die Einstellungen", settings_content)


    def log(self, message):
        """Adds a message to the log queue."""
        self.log_queue.put(message)

    def process_log_queue(self):
        """Processes messages from the log queue and updates the GUI."""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_textbox.configure(state="normal")
                self.log_textbox.insert("end", message + "\n")
                self.log_textbox.see("end")
                self.log_textbox.configure(state="disabled")
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_log_queue)

    def load_prompts(self):
        """Loads prompts from prompts.txt into the textbox."""
        self.log("Lade Prompts von prompts.txt...")
        if os.path.exists(PROMPTS_FILE):
            with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                self.prompts_textbox.insert("1.0", f.read())
        else:
            self.log(f"WARNUNG: {PROMPTS_FILE} nicht gefunden. Bitte füge Prompts hinzu.")

    def save_prompts(self):
        """Saves prompts from the textbox to prompts.txt."""
        with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
            f.write(self.prompts_textbox.get("1.0", "end-1c"))
        self.log("✅ Prompts erfolgreich in prompts.txt gespeichert.")

    def load_settings(self):
        """Loads settings from .env and config.ini."""
        self.log("Lade Einstellungen...")
        # Load API keys from .env
        load_dotenv(dotenv_path=ENV_FILE)
        self.openai_key_entry.insert(0, os.getenv("OPENAI_API_KEY", ""))
        self.stability_key_entry.insert(0, os.getenv("STABILITY_API_KEY", ""))

        # Load config from config.ini
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            config.read(CONFIG_FILE)
        else:
            self.log(f"WARNUNG: {CONFIG_FILE} nicht gefunden, Standardwerte werden verwendet.")

        provider = config.get('General', 'provider', fallback='openai')
        self.provider_optionmenu.set(provider)

        self.openai_style_textbox.insert("1.0", config.get('OpenAI', 'style_suffix', fallback=""))
        self.stability_style_textbox.insert("1.0", config.get('StabilityAI', 'style_suffix', fallback=""))

    def save_settings(self):
        """Saves settings to .env and config.ini."""
        # Save API keys to .env
        set_key(ENV_FILE, "OPENAI_API_KEY", self.openai_key_entry.get())
        set_key(ENV_FILE, "STABILITY_API_KEY", self.stability_key_entry.get())

        # Save general config to config.ini
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE) # Read existing to preserve sections

        if not config.has_section('General'): config.add_section('General')
        config.set('General', 'provider', self.provider_optionmenu.get())

        if not config.has_section('OpenAI'): config.add_section('OpenAI')
        config.set('OpenAI', 'style_suffix', self.openai_style_textbox.get("1.0", "end-1c"))

        if not config.has_section('StabilityAI'): config.add_section('StabilityAI')
        config.set('StabilityAI', 'style_suffix', self.stability_style_textbox.get("1.0", "end-1c"))

        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)

        self.log("✅ Einstellungen erfolgreich gespeichert.")
        load_dotenv(dotenv_path=ENV_FILE) # Reload env variables

    def start_generation_thread(self):
        """Starts the image generation in a separate thread."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

        self.generate_button.configure(state="disabled", text="Generiere...")

        thread = threading.Thread(target=self.generation_task)
        thread.daemon = True
        thread.start()

    def generation_task(self):
        """The actual image generation logic that runs in a thread."""
        self.log("--- 🎨 Starte Bild-Generierung ---")

        # Get settings from GUI
        provider = self.provider_optionmenu.get()
        prompts = [line.strip() for line in self.prompts_textbox.get("1.0", "end-1c").split('\n') if line.strip()]

        if not prompts:
            self.log("⚠️ Keine Prompts gefunden. Bitte füge Prompts im Generator-Tab hinzu.")
            self.generate_button.configure(state="normal", text="Bilder generieren")
            return

        try:
            if provider == 'openai':
                style_suffix = self.openai_style_textbox.get("1.0", "end-1c")
                api_key = os.getenv("OPENAI_API_KEY")
                generator = OpenAIGenerator(api_key, style_suffix)
            elif provider == 'stabilityai':
                style_suffix = self.stability_style_textbox.get("1.0", "end-1c")
                api_key = os.getenv("STABILITY_API_KEY")
                generator = StabilityAIGenerator(api_key, style_suffix)
            else:
                self.log(f"❌ FATAL: Unbekannter Anbieter '{provider}'.")
                return
        except ValueError as e:
            self.log(f"❌ FATAL: {e}")
            self.generate_button.configure(state="normal", text="Bilder generieren")
            return

        self.log(f"ℹ️ Anbieter: {provider}")
        self.log(f"Gefundene Prompts: {len(prompts)}")

        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        saved_image_paths = []
        for prompt in prompts:
            image_data = generator.generate(prompt, log_callback=self.log)
            if image_data:
                saved_path = save_image(image_data, prompt, log_callback=self.log)
                if saved_path:
                    saved_image_paths.append(saved_path)
            self.log("-" * 20)

        create_pdf_from_images(saved_image_paths, log_callback=self.log)

        # Schedule gallery update on the main thread
        self.after(0, self.update_gallery)

        self.log("\n✨ Fertig!")
        self.generate_button.configure(state="normal", text="Bilder generieren")
