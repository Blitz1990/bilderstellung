import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
import re
import configparser
from fpdf import FPDF
import base64

# --- Setup ---
load_dotenv()

# --- Constants ---
OUTPUT_DIR = "generated_images"
PROMPTS_FILE = "prompts.txt"
CONFIG_FILE = "config.ini"

# --- Logging Helper ---
def _log(message, callback=None):
    """Log a message using a callback or print."""
    if callback:
        callback(message)
    else:
        print(message)

# --- Base Class for Image Generation ---
class ImageGenerator:
    """Abstract base class for image generators."""
    def __init__(self, api_key, style_suffix):
        if not api_key:
            raise ValueError("API key is missing for the selected provider.")
        self.api_key = api_key
        self.style_suffix = style_suffix

    def generate(self, prompt, log_callback=None):
        """Generates an image from a prompt. Returns image data as bytes or a URL."""
        raise NotImplementedError

# --- OpenAI DALL-E 3 Generator ---
class OpenAIGenerator(ImageGenerator):
    """Image generator using OpenAI's DALL-E 3."""
    def __init__(self, api_key, style_suffix):
        super().__init__(api_key, style_suffix)
        self.client = OpenAI(api_key=self.api_key)

    def generate(self, prompt, log_callback=None):
        full_prompt = prompt + self.style_suffix
        _log(f"🎨 Generating with OpenAI for prompt: '{prompt}'...", log_callback)
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=full_prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
            _log("✅ OpenAI image generated successfully.", log_callback)
            return image_url
        except Exception as e:
            _log(f"❌ Error generating image with OpenAI: {e}", log_callback)
            return None

# --- Stability AI Generator ---
class StabilityAIGenerator(ImageGenerator):
    """Image generator using Stability AI's API."""
    def generate(self, prompt, log_callback=None):
        full_prompt = prompt + self.style_suffix
        _log(f"🎨 Generating with StabilityAI for prompt: '{prompt}'...", log_callback)
        api_host = "https://api.stability.ai"
        engine_id = "stable-diffusion-v1-6"
        url = f"{api_host}/v1/generation/{engine_id}/text-to-image"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "text_prompts": [{"text": full_prompt}],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            image_b64 = data["artifacts"][0]["base64"]
            _log("✅ StabilityAI image generated successfully.", log_callback)
            return base64.b64decode(image_b64)
        except Exception as e:
            _log(f"❌ Error generating image with StabilityAI: {e}", log_callback)
            return None

# --- Helper Functions ---
def save_image(image_data, prompt, log_callback=None):
    """Saves image data (URL or bytes) to a file."""
    if not image_data:
        return None

    _log(f"⬇️ Saving image...", log_callback)
    try:
        safe_filename = re.sub(r'[\\/*?:"<>|]', "", prompt)[:50] + ".png"
        output_path = os.path.join(OUTPUT_DIR, safe_filename)

        if isinstance(image_data, str):
            response = requests.get(image_data, stream=True)
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(8192):
                    f.write(chunk)
        elif isinstance(image_data, bytes):
            with open(output_path, 'wb') as f:
                f.write(image_data)

        _log(f"💾 Image saved successfully to: {output_path}", log_callback)
        return output_path
    except Exception as e:
        _log(f"❌ Error saving image: {e}", log_callback)
        return None

def create_pdf_from_images(image_paths, pdf_filename="Malbuch.pdf", log_callback=None):
    """Creates a PDF from a list of image files."""
    if not image_paths:
        _log("\n⚠️ No images were generated, skipping PDF creation.", log_callback)
        return

    _log(f"\n📚 Creating PDF from {len(image_paths)} images...", log_callback)
    try:
        pdf = FPDF('P', 'mm', 'A4')
        margin = 10
        page_width = 210
        page_height = 297
        max_width = page_width - 2 * margin
        max_height = page_height - 2 * margin

        for image_path in image_paths:
            pdf.add_page()
            x_pos = (page_width - max_width) / 2
            y_pos = (page_height - max_height) / 2
            pdf.image(image_path, x=x_pos, y=y_pos, w=max_width)

        pdf.output(pdf_filename)
        _log(f"✅ PDF created successfully: {pdf_filename}", log_callback)
    except Exception as e:
        _log(f"❌ Error creating PDF: {e}", log_callback)

# --- Main Execution ---
def main():
    """Main function to run the image generation process."""
    log_func = print # Use print for command-line logging
    log_func("--- 🎨 Coloring Book Image Generator ---")

    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        log_func(f"❌ FATAL: Configuration file '{CONFIG_FILE}' not found.")
        return
    config.read(CONFIG_FILE)

    provider = config.get('General', 'provider', fallback='openai').lower()

    try:
        if provider == 'openai':
            style_suffix = config.get('OpenAI', 'style_suffix', fallback="")
            api_key = os.getenv("OPENAI_API_KEY")
            generator = OpenAIGenerator(api_key, style_suffix)
        elif provider == 'stabilityai':
            style_suffix = config.get('StabilityAI', 'style_suffix', fallback="")
            api_key = os.getenv("STABILITY_API_KEY")
            generator = StabilityAIGenerator(api_key, style_suffix)
        else:
            log_func(f"❌ FATAL: Unknown provider '{provider}' in {CONFIG_FILE}. Options are 'openai' or 'stabilityai'.")
            return
    except ValueError as e:
        log_func(f"❌ FATAL: {e}")
        return

    log_func(f"ℹ️ Using provider: {provider}")

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    try:
        with open(PROMPTS_FILE, 'r') as f:
            prompts = [line.strip() for line in f if line.strip()]
        if not prompts:
            log_func(f"⚠️ No prompts found in {PROMPTS_FILE}.")
            return
    except FileNotFoundError:
        log_func(f"❌ FATAL: Prompts file not found at '{PROMPTS_FILE}'.")
        return

    log_func(f"Found {len(prompts)} prompts in {PROMPTS_FILE}.")

    saved_image_paths = []
    for prompt in prompts:
        image_data = generator.generate(prompt, log_callback=log_func)
        if image_data:
            saved_path = save_image(image_data, prompt, log_callback=log_func)
            if saved_path:
                saved_image_paths.append(saved_path)
        log_func("-" * 20)

    create_pdf_from_images(saved_image_paths, log_callback=log_func)

    log_func("\n✨ All done!")

if __name__ == "__main__":
    main()
