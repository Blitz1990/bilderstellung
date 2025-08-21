import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
import re

# Load environment variables from a .env file
load_dotenv()

# --- Configuration ---
# It's recommended to set the OpenAI API key as an environment variable
# for security reasons. Create a file named .env in the same directory
# and add the following line:
# OPENAI_API_KEY="your_secret_api_key_here"
API_KEY = os.getenv("OPENAI_API_KEY")
OUTPUT_DIR = "generated_images"
PROMPTS_FILE = "prompts.txt"
# This suffix is added to each prompt to get the desired coloring book style
STYLE_SUFFIX = ", for a children's coloring book, simple, clean lines, black and white, vector illustration, no shading"

def generate_image(client, prompt):
    """
    Generates an image using the OpenAI DALL-E API.
    """
    full_prompt = prompt + STYLE_SUFFIX
    print(f"🎨 Generating image for prompt: '{prompt}'...")
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=full_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        print("✅ Image generated successfully.")
        return image_url
    except Exception as e:
        print(f"❌ Error generating image: {e}")
        return None

def download_and_save_image(image_url, prompt):
    """
    Downloads an image from a URL and saves it to the output directory.
    """
    if not image_url:
        return

    print(f"⬇️ Downloading image...")
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Create a safe filename from the prompt
        safe_filename = re.sub(r'[\\/*?:"<>|]', "", prompt)[:50] + ".png"
        output_path = os.path.join(OUTPUT_DIR, safe_filename)

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)

        print(f"💾 Image saved successfully to: {output_path}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading image: {e}")

def main():
    """
    Main function to run the image generation process.
    """
    print("--- 🎨 Coloring Book Image Generator ---")

    if not API_KEY:
        print("❌ FATAL: OpenAI API key not found.")
        print("Please set the OPENAI_API_KEY environment variable.")
        print("You can do this by creating a .env file with the line: OPENAI_API_KEY='your_key_here'")
        return

    try:
        client = OpenAI(api_key=API_KEY)
    except Exception as e:
        print(f"❌ FATAL: Could not initialize OpenAI client: {e}")
        return

    # Create the output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        print(f"📁 Creating output directory: {OUTPUT_DIR}")
        os.makedirs(OUTPUT_DIR)

    # Read prompts from the file
    try:
        with open(PROMPTS_FILE, 'r') as f:
            prompts = [line.strip() for line in f if line.strip()]
        if not prompts:
            print(f"⚠️ No prompts found in {PROMPTS_FILE}. Please add some prompts to the file.")
            return
    except FileNotFoundError:
        print(f"❌ FATAL: Prompts file not found at '{PROMPTS_FILE}'.")
        print("Please create it and add one prompt per line.")
        return

    print(f"Found {len(prompts)} prompts in {PROMPTS_FILE}.")

    # Generate and save an image for each prompt
    for prompt in prompts:
        image_url = generate_image(client, prompt)
        if image_url:
            download_and_save_image(image_url, prompt)
        print("-" * 20)

    print("✨ All done!")

if __name__ == "__main__":
    main()
