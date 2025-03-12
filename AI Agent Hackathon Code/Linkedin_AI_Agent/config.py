import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Feature flags
class FeatureFlags:
    TEST_GROQ_ONLY = False  # Set to True to only test GROQ functionality
    DEBUG_MODE = True      # Enable detailed logging

# LinkedIn credentials
LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL')
LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')

# GROQ API configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# LinkedIn search settings
MAX_SEARCH_RESULTS = 5
DELAY_BETWEEN_REQUESTS = 2  # seconds 