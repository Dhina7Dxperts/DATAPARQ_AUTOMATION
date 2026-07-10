import os
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv()

class Config:
    BASE_URL = os.getenv("BASE_URL", "https://gcp.dataparq.com")
    USERNAME = os.getenv("PARQ_USERNAME", "")
    PASSWORD = os.getenv("PARQ_PASSWORD", "")