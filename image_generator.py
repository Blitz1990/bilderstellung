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

# --- Base Class for Image Generation ---
class ImageGenerator:
    """Abstract base class for image generators."""
    def __init__(self, api_key, style_suffix):
        if not api_key:
            raise ValueError("API key is missing for the selected provider.")
        self.api_key = api_key
        self.style_suffix = style_suffix

    def generate(self, prompt):
        """Generates an image from a prompt. Returns image data as bytes or a URL."""
        raise NotImplementedError

# --- OpenAI DALL-E 3 Generator ---
class OpenAIGenerator(ImageGenerator):
    """Image generator using OpenAI's DALL-E 3."""
    def __init__(self, api_key, style_suffix):
        super().__init__(api_key, style_suffix)
        self.client = OpenAI(api_key=self.api_key)

    def generate(self, prompt):
        full_prompt = prompt + self.style_suffix
        print(f"🎨 Generating with OpenAI for prompt: '{prompt}'...")
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=full_prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
            print("✅ OpenAI image generated successfully.")
            return image_url
        except Exception as e:
            print(f"❌ Error generating image with OpenAI: {e}")
            return None

# --- Stability AI Generator ---
class StabilityAIGenerator(ImageGenerator):
    """Image generator using Stability AI's API."""
    def generate(self, prompt):
        full_prompt = prompt + self.style_suffix
        print(f"🎨 Generating with StabilityAI for prompt: '{prompt}'...")
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
            print("✅ StabilityAI image generated successfully.")
            return base64.b64decode(image_b64)
        except Exception as e:
            print(f"❌ Error generating image with StabilityAI: {e}")
            return None

# --- Helper Functions ---
def save_image(image_data, prompt):
    """Saves image data (URL or bytes) to a file."""
    if not image_data:
        return None

    print(f"⬇️ Saving image...")
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

        print(f"💾 Image saved successfully to: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Error saving image: {e}")
        return None

def create_pdf_from_images(image_paths, pdf_filename="Malbuch.pdf"):
    """Creates a PDF from a list of image files."""
    if not image_paths:
        print("\n⚠️ No images were generated, skipping PDF creation.")
        return

    print(f"\n📚 Creating PDF from {len(image_paths)} images...")
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
        print(f"✅ PDF created successfully: {pdf_filename}")
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")

# --- Main Execution ---
def main():
    """Main function to run the image generation process."""
    print("--- 🎨 Coloring Book Image Generator ---")

    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ FATAL: Configuration file '{CONFIG_FILE}' not found.")
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
            print(f"❌ FATAL: Unknown provider '{provider}' in {CONFIG_FILE}. Options are 'openai' or 'stabilityai'.")
            return
    except ValueError as e:
        print(f"❌ FATAL: {e}")
        return

    print(f"ℹ️ Using provider: {provider}")

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    try:
        with open(PROMPTS_FILE, 'r') as f:
            prompts = [line.strip() for line in f if line.strip()]
        if not prompts:
            print(f"⚠️ No prompts found in {PROMPTS_FILE}.")
            return
    except FileNotFoundError:
        print(f"❌ FATAL: Prompts file not found at '{PROMPTS_FILE}'.")
        return

    print(f"Found {len(prompts)} prompts in {PROMPTS_FILE}.")

    saved_image_paths = []
    for prompt in prompts:
        image_data = generator.generate(prompt)
        if image_data:
            saved_path = save_image(image_data, prompt)
            if saved_path:
                saved_image_paths.append(saved_path)
        print("-" * 20)

    create_pdf_from_images(saved_image_paths)

    print("\n✨ All done!")

if __name__ == "__main__":
    main()
