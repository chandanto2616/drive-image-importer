import os
import json
from dotenv import load_dotenv

load_dotenv()

# Cloudinary
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# Database & Redis
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

# Google Service Account from ENV instead of local file
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")  # full JSON string
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")  # optional

# Images dir (optional, if still used locally for caching)
IMAGES_DIR = os.getenv("IMAGES_DIR")
