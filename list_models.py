import google.generativeai as genai
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config import settings

# Configure API
genai.configure(api_key=settings.gemini_api_key)

print("Checking available Gemini models...")

try:
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"Model: {model.name}")
            print(f"  Display name: {model.display_name}")
            print(f"  Supported methods: {model.supported_generation_methods}")
            print()
except Exception as e:
    print(f"Error listing models: {e}")