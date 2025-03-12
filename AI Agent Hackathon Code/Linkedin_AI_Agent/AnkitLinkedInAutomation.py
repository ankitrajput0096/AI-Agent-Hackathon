from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
import time
import json
import logging
import groq
from typing import List
from pydantic import BaseModel
import os
from flask_cors import CORS  # Import CORS from flask_cors

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
        options.add_argument('--headless')  # Run in headless mode for API
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        try:
            # Fixed: Remove the version parameter which caused the error
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
            
            # Wait for email field and enter email
            email_elem = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_elem.send_keys(self.linkedin_email)
            
            # Enter password
            password_elem = self.driver.find_element(By.ID, "password")
            password_elem.send_keys(self.linkedin_password)
            
            # Click login button
            self.driver.find_element(By.CSS_SELECTOR, "[type='submit']").click()
            
            # Wait for login to complete by checking for feed or home page
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "global-nav"))
            )
            
            # Additional wait to ensure everything is loaded
            time.sleep(5)
            logger.info("Successfully logged in to LinkedIn")
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False
        
    def search_profiles(self, search_params: SearchParameters, batch_size: int = 5) -> List[LinkedInProfile]:
        """Search LinkedIn profiles based on given parameters"""
        try:
            logger.info(f"Starting profile search with parameters: {search_params}")
            search_url = self._build_search_url(search_params)
            logger.debug(f"Generated search URL: {search_url}")
            
            self.driver.get(search_url)
            time.sleep(DELAY_BETWEEN_REQUESTS)
            
            logger.info("Waiting for search results to load...")
            # Wait for profile cards to appear
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-chameleon-result-urn]'))
                )
            except Exception as e:
                logger.warning(f"Timeout waiting for standard profile cards: {str(e)}")
                logger.info("Attempting alternative selectors...")
                
                # Try alternative selectors for profile cards
                selectors = [
                    "li.reusable-search__result-container",
                    ".search-result__wrapper",
                    ".entity-result__item",
                    "li.search-result"
                ]
                
                found = False
                for selector in selectors:
                    try:
                        WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        logger.info(f"Found results with selector: {selector}")
                        found = True
                        break
                    except:
                        continue
                
                if not found:
                    # Take screenshot for debugging
                    if FeatureFlags.DEBUG_MODE:
                        self.driver.save_screenshot("search_results_debug.png")
                        logger.debug("Saved search results screenshot for debugging")
                    raise Exception("Could not find any profile cards on the page")
            
            # Find all profile cards using the data attribute
            profile_cards = self.driver.find_elements(By.CSS_SELECTOR, '[data-chameleon-result-urn^="urn:li:member:"]')
            
            # If no results with primary selector, try alternative selectors
            if len(profile_cards) == 0:
                alternative_selectors = [
                    "li.reusable-search__result-container",
                    ".entity-result__item",
                    "li.search-result",
                    ".search-result__wrapper"
                ]
                
                for selector in alternative_selectors:
                    profile_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(profile_cards) > 0:
                        logger.info(f"Found {len(profile_cards)} profile cards with selector: {selector}")
                        break
            
            logger.info(f"Found {len(profile_cards)} profile cards")
            
            # Scroll down to ensure more results are loaded if needed
            if len(profile_cards) < 10:
                self._scroll_for_more_results(min_profiles_needed=10)
                # Re-fetch the cards after scrolling
                profile_cards = self.driver.find_elements(By.CSS_SELECTOR, '[data-chameleon-result-urn^="urn:li:member:"]')
                
                # If still no results with primary selector, try alternatives again
                if len(profile_cards) == 0:
                    for selector in alternative_selectors:
                        profile_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if len(profile_cards) > 0:
                            break
                
                logger.info(f"After scrolling, found {len(profile_cards)} profile cards")
            
            # Process cards in batches

            profiles = []
            for i in range(0, min(10, len(profile_cards)), batch_size):
                batch = profile_cards[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} cards)")
                
                try:
                    # Combine HTML of all cards in batch

                    batch_profiles = []
                    for card in batch:
                        item_html = card.get_attribute('outerHTML')
                        batch_item = self._parse_profiles_with_llm(item_html, 1)
                        batch_profiles.append(batch_item[0])

                    logger.info("batch_profile")
                    logger.info(batch_profiles)  

                    if batch_profiles:
                        profiles.extend(batch_profiles)
                        logger.debug(f"Successfully parsed {len(batch_profiles)} profiles from batch")
                    




                    # Add delay between batches to respect rate limits
                    if i + batch_size < len(profile_cards):
                        time.sleep(2)
                        
                except Exception as e:
                    logger.warning(f"Failed to parse batch: {str(e)}")
                    continue
            
            logger.info(f"Successfully parsed {len(profiles)} profiles")
            return profiles[:MAX_SEARCH_RESULTS]
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}", exc_info=True)
            return []

    def _scroll_for_more_results(self, min_profiles_needed=10, max_scrolls=5):
        """Scroll down the page to load more results until we have enough profiles"""
        # Try with different selectors to find profile cards
        selectors = [
            '[data-chameleon-result-urn^="urn:li:member:"]',
            "li.reusable-search__result-container",
            ".entity-result__item",
            "li.search-result"
        ]
        
        # Use the first selector that finds elements
        selector_to_use = selectors[0]
        for selector in selectors:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if len(elements) > 0:
                selector_to_use = selector
                break
        
        current_count = len(self.driver.find_elements(By.CSS_SELECTOR, selector_to_use))
        scroll_count = 0
        
        while current_count < min_profiles_needed and scroll_count < max_scrolls:
            # Scroll down to the bottom of the page
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for content to load
            
            # Check if we have more profiles
            new_count = len(self.driver.find_elements(By.CSS_SELECTOR, selector_to_use))
            
            # If no new profiles were loaded, break out of the loop
            if new_count == current_count:
                scroll_count += 1  # Increment scroll attempt counter
            else:
                current_count = new_count
                logger.info(f"Scrolled and found {current_count} profiles")
            
            # Check "Show more results" button if present
            try:
                # Try different button texts
                button_texts = ["Show more results", "See more results", "Load more"]
                for text in button_texts:
                    try:
                        show_more_button = WebDriverWait(self.driver, 2).until(
                            EC.presence_of_element_located((By.XPATH, f"//button[contains(text(), '{text}')]"))
                        )
                        show_more_button.click()
                        logger.info(f"Clicked '{text}' button")
                        time.sleep(2)
                        break
                    except:
                        continue
            except:
                # No button found, continue with scrolling
                pass

    def _parse_profiles_with_llm(self, html_content: str, expected_count: int) -> List[LinkedInProfile]:
        """Use GROQ to parse LinkedIn profile data from HTML"""
        try:
            logger.info("Preparing GROQ prompt for HTML parsing")
            prompt = f"""
            Extract information for {expected_count} LinkedIn profiles from this HTML content.
            For each profile card, extract:
            - Full name of the person
            - Their headline/job title
            - Profile URL (the link that starts with linkedin.com/in/)
            
            Return the information in this JSON format:
            {{
                "profiles": [
                    {{
                        "name": "person's name",
                        "headline": "their headline/title",
                        "url": "their profile URL"
                    }}
                    // Repeat for each profile in the HTML...
                ]
            }}

            HTML Content:
            {html_content}
            """
            
            logger.debug("Sending request to GROQ API")
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at parsing LinkedIn profile information from HTML. Extract exactly the number of profiles specified."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                model="mixtral-8x7b-32768",
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            profiles_data = json.loads(response.choices[0].message.content)
            
            # Debug log to inspect the structure of the returned data
            logger.debug(f"Received profiles data: {json.dumps(profiles_data, indent=2)}")
            
            profiles = []
            for profile_data in profiles_data.get("profiles", []):
                try:
                    # Ensure required fields are present
                    required_fields = ["name", "headline", "url"]
                    for field in required_fields:
                        if field not in profile_data:
                            logger.warning(f"Missing required field '{field}' in profile data: {profile_data}")
                            profile_data[field] = "" if field != "url" else "https://linkedin.com/in/unknown"
                    
                    # Create profile instance with validated data
                    profile = LinkedInProfile(**profile_data)
                    profiles.append(profile)
                    
                except Exception as e:
                    logger.warning(f"Failed to create LinkedInProfile instance: {str(e)}")
                    logger.warning(f"Problematic data: {profile_data}")
                    continue
            
            return profiles
            
        except Exception as e:
            logger.error(f"Failed to parse profiles with LLM: {str(e)}", exc_info=True)
            return []

    def _build_search_url(self, search_params: SearchParameters) -> str:
        """Build the search URL based on the given search parameters"""
        base_url = "https://www.linkedin.com/search/results/people/"
        query_parts = []
        
        # Use the optimized search text
        if search_params.keywords:
            query_parts.append(f"keywords={search_params.keywords}")
        
        # Combine all query parameters
        query_string = '?' + '&'.join(query_parts)
        
        if FeatureFlags.DEBUG_MODE:
            logger.debug(f"Search URL: {base_url + query_string}")
        
        return base_url + query_string
        
    def clean_up(self):
        """Close the browser and clean up resources"""
        if self.driver:
            self.driver.quit()

# Initialize Flask app
app = Flask(__name__)
# Enable CORS for all routes
CORS(app)  # This allows all origins for all routes

@app.route('/api/linkedin/search', methods=['POST'])
def search_profiles():
    """
    API endpoint to search LinkedIn profiles
    Expects JSON with:
    - linkedin_email: LinkedIn login email
    - linkedin_password: LinkedIn login password
    - search_query: Search keywords
    - groq_api_key: API key for GROQ service
    
    Returns top 10 LinkedIn profiles matching the search
    """
    try:
        # Get request data
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Validate required fields
        required_fields = ['linkedin_email', 'linkedin_password', 'search_query', 'groq_api_key']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Extract parameters
        linkedin_email = data['linkedin_email']
        linkedin_password = data['linkedin_password']
        search_query = data['search_query']
        groq_api_key = data['groq_api_key']
        
        # Create scraper instance
        scraper = LinkedInScraper(linkedin_email, linkedin_password, groq_api_key)
        
        # Login to LinkedIn
        login_success = scraper.login()
        
        if not login_success:
            scraper.clean_up()
            return jsonify({"error": "Failed to login to LinkedIn. Check credentials."}), 401
        
        # Create search parameters
        search_params = SearchParameters(keywords=search_query)
        
        # Search for profiles
        profiles = scraper.search_profiles(search_params)
        
        # Clean up browser resources
        scraper.clean_up()
        
        if not profiles:
            return jsonify({"message": "No profiles found matching the search criteria", "profiles": []}), 200
        
        # Format response data
        response_data = {
            "message": f"Found {len(profiles)} profiles matching '{search_query}'",
            "profiles": [p.dict() for p in profiles[:10]]
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"API error: {str(e)}", exc_info=True)
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Add a simple health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "API is running"}), 200

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=FeatureFlags.DEBUG_MODE, host='0.0.0.0', port=8070)