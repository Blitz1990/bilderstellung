import customtkinter as ctk
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
        self.tabs.add("Settings")

        # --- Queue for thread-safe logging ---
        self.log_queue = queue.Queue()

        # --- Setup Tabs ---
        self.setup_generator_tab()
        self.setup_settings_tab()

        # --- Load initial data ---
        self.load_settings()
        self.load_prompts()

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

        self.log("\n✨ Fertig!")
        self.generate_button.configure(state="normal", text="Bilder generieren")
