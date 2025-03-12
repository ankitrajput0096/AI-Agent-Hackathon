from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from config import LINKEDIN_EMAIL, LINKEDIN_PASSWORD, DELAY_BETWEEN_REQUESTS, FeatureFlags, MAX_SEARCH_RESULTS, GROQ_API_KEY
from typing import List
from models import SearchParameters, LinkedInProfile
import json
import logging
import groq

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LinkedInScraper:
    def __init__(self):
        self.driver = None
        self.groq_client = groq.Groq(api_key=GROQ_API_KEY)  # Initialize GROQ client
        self.setup_driver()
        
    def setup_driver(self):
        """Initialize and configure the Chrome WebDriver"""
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        import platform
        
        options = Options()
        options.add_argument('--disable-notifications')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--ignore-certificate-errors')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from webdriver_manager.core.utils import ChromeType
            from webdriver_manager.core.os_manager import ChromeType
            
            # Force specific version that's known to work
            driver_path = ChromeDriverManager(version="114.0.5735.90").install()
            service = Service(executable_path=driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            
        except Exception as e:
            print(f"Error initializing Chrome driver: {str(e)}")
            print("Attempting alternative setup...")
            try:
                service = Service()
                self.driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                print(f"Alternative setup failed: {str(e)}")
                raise
        
    def login(self):
        """Log in to LinkedIn"""
        try:
            self.driver.get('https://www.linkedin.com/login')
            
            # Wait for email field and enter email
            email_elem = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_elem.send_keys(LINKEDIN_EMAIL)
            
            # Enter password
            password_elem = self.driver.find_element(By.ID, "password")
            password_elem.send_keys(LINKEDIN_PASSWORD)
            
            # Click login button
            self.driver.find_element(By.CSS_SELECTOR, "[type='submit']").click()
            
            # Wait for login to complete by checking for feed or home page
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "global-nav"))
            )
            
            # Additional wait to ensure everything is loaded
            time.sleep(5)
            
        except Exception as e:
            print(f"Login failed: {str(e)}")
            raise
        
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
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-chameleon-result-urn]'))
            )
            
            # Find all profile cards using the data attribute
            profile_cards = self.driver.find_elements(By.CSS_SELECTOR, '[data-chameleon-result-urn^="urn:li:member:"]')
            logger.info(f"Found {len(profile_cards)} profile cards")
            
            # Scroll down to ensure more results are loaded if needed
            if len(profile_cards) < 10:
                self._scroll_for_more_results(min_profiles_needed=10)
                # Re-fetch the cards after scrolling
                profile_cards = self.driver.find_elements(By.CSS_SELECTOR, '[data-chameleon-result-urn^="urn:li:member:"]')
                logger.info(f"After scrolling, found {len(profile_cards)} profile cards")
            
            # Process cards in batches
            profiles = []
            # Changed from 4 to 10 profiles
            for i in range(0, min(10, len(profile_cards)), batch_size):
                batch = profile_cards[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} cards)")
                
                try:
                    # Combine HTML of all cards in batch
                    batch_html = "\n".join([card.get_attribute('outerHTML') for card in batch])
                    batch_profiles = self._parse_profiles_with_llm(batch_html, len(batch))
                    print(batch_profiles)
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
            print("Max results", MAX_SEARCH_RESULTS)
            return profiles[:MAX_SEARCH_RESULTS]
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}", exc_info=True)
            return []
    
    def _scroll_for_more_results(self, min_profiles_needed=10, max_scrolls=5):
        """Scroll down the page to load more results until we have enough profiles"""
        current_count = len(self.driver.find_elements(By.CSS_SELECTOR, '[data-chameleon-result-urn^="urn:li:member:"]'))
        scroll_count = 0
        
        while current_count < min_profiles_needed and scroll_count < max_scrolls:
            # Scroll down to the bottom of the page
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for content to load
            
            # Check if we have more profiles
            new_count = len(self.driver.find_elements(By.CSS_SELECTOR, '[data-chameleon-result-urn^="urn:li:member:"]'))
            
            # If no new profiles were loaded, break out of the loop
            if new_count == current_count:
                scroll_count += 1  # Increment scroll attempt counter
            else:
                current_count = new_count
                logger.info(f"Scrolled and found {current_count} profiles")
            
            # Check "Show more results" button if present
            try:
                show_more_button = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Show more results')]"))
                )
                show_more_button.click()
                time.sleep(2)
                logger.info("Clicked 'Show more results' button")
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
                        "profile_url": "their profile URL"
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
                model="deepseek-r1-distill-llama-70b",
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
                    required_fields = ["name", "headline", "profile_url"]
                    for field in required_fields:
                        if field not in profile_data:
                            logger.warning(f"Missing required field '{field}' in profile data: {profile_data}")
                            profile_data[field] = "" if field != "profile_url" else "https://linkedin.com/in/unknown"
                    
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
        
        # Add location only if specified
        # if search_params.location:
        #     query_parts.append(f"location=[{search_params.location}]")
        
        # Combine all query parameters
        query_string = '?' + '&'.join(query_parts)
        
        if FeatureFlags.DEBUG_MODE:
            print(f"\nDebug: Search URL: {base_url + query_string}")
        
        return base_url + query_string