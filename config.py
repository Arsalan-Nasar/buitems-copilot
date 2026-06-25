# config.py — central settings for BUITEMS Copilot
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "llama-3.3-70b-versatile"

# Path to the student data file
DATA_FILE = "data/student.json"