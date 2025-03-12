from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from pymongo import MongoClient
from datetime import datetime
import time
import json
import logging
import groq
import os
from typing import List
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('combined_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app with CORS
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# MongoDB setup
client = MongoClient('mongodb://mongo:27017/')
db = client['user_management']
users_collection = db['users']
activity_collection = db['useractivity']

# Global user tracking (Note: For production, use proper session management)
current_user = None

# Constants
DELAY_BETWEEN_REQUESTS = 2
MAX_SEARCH_RESULTS = 10

# Feature flags
class FeatureFlags:
    DEBUG_MODE = os.environ.get('DEBUG_MODE', 'False').lower() == 'true'

# Models
class SearchParameters(BaseModel):
    keywords: str = ""
    
class LinkedInProfile(BaseModel):
    name: str
    headline: str
    url: str

# LinkedIn Scraper Class
class LinkedInScraper:
    def __init__(self, linkedin_email, linkedin_password, groq_api_key):
        self.linkedin_email = linkedin_email
        self.linkedin_password = linkedin_password
        self.driver = None
        self.groq_client = groq.Groq(api_key=groq_api_key)
        self.setup_driver()
        
    def setup_driver(self):
        """Initialize and configure the Chrome WebDriver"""
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument('--disable-notifications')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--headless')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            logger.info("Chrome driver initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Chrome driver: {str(e)}")
            logger.info("Attempting alternative setup...")
            try:
                service = Service()
                self.driver = webdriver.Chrome(service=service, options=options)
                logger.info("Alternative Chrome driver setup successful")
            except Exception as e:
                logger.error(f"Alternative setup failed: {str(e)}")
                raise
        
    def login(self):
        """Log in to LinkedIn"""
        try:
            self.driver.get('https://www.linkedin.com/login')
            email_elem = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_elem.send_keys(self.linkedin_email)
            password_elem = self.driver.find_element(By.ID, "password")
            password_elem.send_keys(self.linkedin_password)
            self.driver.find_element(By.CSS_SELECTOR, "[type='submit']").click()
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "global-nav"))
            )
            time.sleep(5)
            logger.info("Successfully logged in to LinkedIn")
            return True
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False
        
    def search_profiles(self, search_params: SearchParameters, batch_size: int = 5) -> List[LinkedInProfile]:
        """Search LinkedIn profiles based on given parameters"""
        try:
            search_url = self._build_search_url(search_params)
            self.driver.get(search_url)
            time.sleep(DELAY_BETWEEN_REQUESTS)
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-chameleon-result-urn]'))
                )
            except Exception as e:
                logger.warning(f"Timeout waiting for profile cards: {str(e)}")
                selectors = [
                    "li.reusable-search__result-container",
                    ".search-result__wrapper",
                    ".entity-result__item",
                    "li.search-result"
                ]
                found = False
                for selector in selectors:
                    try:
                        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        found = True
                        break
                    except: continue
                if not found:
                    if FeatureFlags.DEBUG_MODE:
                        self.driver.save_screenshot("search_results_debug.png")
                    raise Exception("Could not find profile cards")
            
            profile_cards = self.driver.find_elements(By.CSS_SELECTOR, '[data-chameleon-result-urn^="urn:li:member:"]')
            if len(profile_cards) == 0:
                alternative_selectors = [
                    "li.reusable-search__result-container",
                    ".entity-result__item",
                    "li.search-result",
                    ".search-result__wrapper"
                ]
                for selector in alternative_selectors:
                    profile_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(profile_cards) > 0: break
            
            if len(profile_cards) < 10:
                self._scroll_for_more_results(min_profiles_needed=10)
                profile_cards = self.driver.find_elements(By.CSS_SELECTOR, '[data-chameleon-result-urn^="urn:li:member:"]')
                if len(profile_cards) == 0:
                    for selector in alternative_selectors:
                        profile_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if len(profile_cards) > 0: break
            
            profiles = []
            for i in range(0, min(10, len(profile_cards)), batch_size):
                batch = profile_cards[i:i + batch_size]
                try:
                    batch_profiles = []
                    for card in batch:
                        item_html = card.get_attribute('outerHTML')
                        batch_item = self._parse_profiles_with_llm(item_html, 1)
                        batch_profiles.append(batch_item[0])
                    if batch_profiles:
                        profiles.extend(batch_profiles)
                    if i + batch_size < len(profile_cards):
                        time.sleep(2)
                except Exception as e:
                    logger.warning(f"Failed to parse batch: {str(e)}")
                    continue
            return profiles[:MAX_SEARCH_RESULTS]
        except Exception as e:
            logger.error(f"Search failed: {str(e)}", exc_info=True)
            return []

    def _scroll_for_more_results(self, min_profiles_needed=10, max_scrolls=5):
        selectors = [
            '[data-chameleon-result-urn^="urn:li:member:"]',
            "li.reusable-search__result-container",
            ".entity-result__item",
            "li.search-result"
        ]
        selector_to_use = selectors[0]
        for selector in selectors:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if len(elements) > 0:
                selector_to_use = selector
                break
        
        current_count = len(self.driver.find_elements(By.CSS_SELECTOR, selector_to_use))
        scroll_count = 0
        
        while current_count < min_profiles_needed and scroll_count < max_scrolls:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_count = len(self.driver.find_elements(By.CSS_SELECTOR, selector_to_use))
            if new_count == current_count:
                scroll_count += 1
            else:
                current_count = new_count
            try:
                button_texts = ["Show more results", "See more results", "Load more"]
                for text in button_texts:
                    try:
                        show_more_button = WebDriverWait(self.driver, 2).until(
                            EC.presence_of_element_located((By.XPATH, f"//button[contains(text(), '{text}')]"))
                        )
                        show_more_button.click()
                        time.sleep(2)
                        break
                    except: continue
            except: pass

    def _parse_profiles_with_llm(self, html_content: str, expected_count: int) -> List[LinkedInProfile]:
        try:
            prompt = f"""
            Extract information for {expected_count} LinkedIn profiles from this HTML content.
            Return the information in JSON format with name, headline, and url.
            HTML Content: {html_content}
            """
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Expert LinkedIn profile parser"},
                    {"role": "user", "content": prompt}
                ],
                model="mixtral-8x7b-32768",
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            profiles_data = json.loads(response.choices[0].message.content)
            profiles = []
            for profile_data in profiles_data.get("profiles", []):
                try:
                    required_fields = ["name", "headline", "url"]
                    for field in required_fields:
                        if field not in profile_data:
                            profile_data[field] = "" if field != "url" else "https://linkedin.com/in/unknown"
                    profiles.append(LinkedInProfile(**profile_data))
                except Exception as e:
                    logger.warning(f"Failed to create profile: {str(e)}")
                    continue
            return profiles
        except Exception as e:
            logger.error(f"LLM parsing failed: {str(e)}", exc_info=True)
            return []

    def _build_search_url(self, search_params: SearchParameters) -> str:
        base_url = "https://www.linkedin.com/search/results/people/"
        query_parts = []
        if search_params.keywords:
            query_parts.append(f"keywords={search_params.keywords}")
        query_string = '?' + '&'.join(query_parts)
        return base_url + query_string
        
    def clean_up(self):
        if self.driver:
            self.driver.quit()

# Helper Functions
def log_activity(api_name, request_data, response_data):
    if current_user:
        activity = {
            'username': current_user,
            'api': api_name,
            'request': request_data,
            'response': response_data,
            'timestamp': datetime.utcnow()
        }
        activity_collection.insert_one(activity)

# User Management Endpoints
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    if users_collection.find_one({"username": username}):
        return jsonify({"error": "Username exists"}), 400

    users_collection.insert_one({"username": username, "password": password})
    return jsonify({"message": "User registered"}), 201

@app.route('/login', methods=['POST'])
def login():
    global current_user
    data = request.get_json()
    user = users_collection.find_one({
        "username": data.get('username'),
        "password": data.get('password')
    })
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    current_user = data.get('username')
    log_activity('/login', data, {"message": "Login successful"})
    return jsonify({"message": "Login successful"})

@app.route('/logout', methods=['POST'])
def logout():
    global current_user
    if not current_user:
        return jsonify({"error": "No user logged in"}), 400
    log_activity('/logout', {}, {"message": "Logout successful"})
    current_user = None
    return jsonify({"message": "Logout successful"})

# LinkedIn API Endpoint
@app.route('/api/linkedin/search', methods=['POST'])
def linkedin_search():
    try:
        data = request.json
        required_fields = ['linkedin_email', 'linkedin_password', 'search_query', 'groq_api_key']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing {field}"}), 400
        
        scraper = LinkedInScraper(
            data['linkedin_email'],
            data['linkedin_password'],
            data['groq_api_key']
        )
        
        if not scraper.login():
            scraper.clean_up()
            return jsonify({"error": "Login failed"}), 401
        
        profiles = scraper.search_profiles(SearchParameters(keywords=data['search_query']))
        scraper.clean_up()
        
        if not profiles:
            return jsonify({"message": "No profiles found", "profiles": []}), 200
        
        return jsonify({
            "message": f"Found {len(profiles)} profiles",
            "profiles": [p.dict() for p in profiles[:10]]
        }), 200
        
    except Exception as e:
        logger.error(f"API error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/ask_general_query', methods=['POST'])
def ask_general_query():
    try:
        data = request.get_json()
        query = data.get('query')
        
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400

        # Initialize Groq client with only valid parameters
        client = groq.Groq(
            api_key='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'
        )
        
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Always format your response as valid JSON."
                },
                {
                    "role": "user",
                    "content": f"{query}\n\nRespond in JSON format with your answer in the 'response' key."
                }
            ],
            model="mixtral-8x7b-32768",
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        json_response = json.loads(response.choices[0].message.content)
        log_activity('/ask_general_query', data, json_response)
        return jsonify(json_response)

    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON response from AI model"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/text_and_query', methods=['POST'])
def text_and_query():
    try:
        data = request.get_json()
        client = groq.Groq(api_key='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')
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Analyze text and answer in JSON format"},
                {"role": "user", "content": f"TEXT:\n{data.get('text')}\nQUESTION: {data.get('query')}\nRespond in JSON"}
            ],
            model="mixtral-8x7b-32768",
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        json_response = json.loads(response.choices[0].message.content)
        log_activity('/text_and_query', data, json_response)
        return jsonify(json_response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_activities', methods=['GET'])
def get_user_activities():
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        activities = list(activity_collection.find(
            {"username": current_user},
            {"_id": 0, "request": 1, "response": 1, "timestamp": 1}
        ).sort("timestamp", -1))
        for act in activities:
            act['timestamp'] = act['timestamp'].isoformat()
        return jsonify({"activities": activities})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/make_quiz', methods=['POST'])
def make_quiz():
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        data = request.get_json()
        client = groq.Groq(api_key='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')
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Generate quiz in JSON format"},
                {"role": "user", "content": f"Create quiz for: {data.get('query')}"}
            ],
            model="mixtral-8x7b-32768",
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        json_response = json.loads(response.choices[0].message.content)
        log_activity('/make_quiz', data, json_response)
        return jsonify(json_response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health Check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "API operational"}), 200

if __name__ == '__main__':
    app.run(
        debug=FeatureFlags.DEBUG_MODE,
        host='0.0.0.0',
        port=8090,
        use_reloader=False
    )