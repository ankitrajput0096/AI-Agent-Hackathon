import time
from config import DELAY_BETWEEN_REQUESTS, GROQ_API_KEY, FeatureFlags
from models import LinkedInProfile, ConnectionMessage, SearchQuery
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import groq

class ConnectionManager:
    def __init__(self, scraper):
        self.scraper = scraper
        self.client = groq.Groq(api_key=GROQ_API_KEY)
        
    def generate_connection_message(self, profile: LinkedInProfile, query_context: SearchQuery) -> ConnectionMessage:
        """Generate a personalized connection message based on the profile and search context"""
        prompt = f"""
        Generate a brief, professional LinkedIn connection message (max 180 characters) based on this context:
        
        Target Person:
        - Name: {profile.name}
        - Role: {profile.headline}
        
        My Info:
        - Name: Ramdeen
        - Looking for: {query_context.purpose or 'Professional networking'}
        - Target Company: {query_context.company or 'Not specified'}
        - Target Role: {query_context.role or 'Not specified'}
        
        Requirements:
        1. Be concise and professional
        2. Reference their current role
        3. Mention the specific purpose (referral/networking)
        4. Keep under 180 characters
        5. Don't use generic phrases like "I came across your profile"
        6. Use my name (Ramdeen) in the signature
        7. Return ONLY the message text, no explanations or reasoning
        
        Example format:
        Hi [Their Name], I'm reaching out regarding [purpose]. Your experience as [role] is impressive. Best regards, Ramdeen
        """
        
        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a message generator. Output ONLY the message text. No explanations, no <think> tags, no reasoning. Just the message."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                model="mixtral-8x7b-32768",
                temperature=0.3,
            )
            
            message = completion.choices[0].message.content.strip()
            
            # Remove any potential markdown, thinking tags, or extra formatting
            message = message.replace('```', '').replace('`', '').strip()
            message = message.replace('<think>', '').replace('</think>', '').strip()
            
            # Validate the message format and length
            if len(message) > 180 or '<' in message or '>' in message or 'think' in message.lower():
                # If message is invalid, use a template
                message = f"Hi {profile.name}, interested in connecting regarding opportunities in {profile.headline}. Best regards, Ramdeen"
                print("\nUsing template message due to invalid generation")
            
            # Log the generated message
            print(f"\nGenerated connection message for {profile.name}:")
            print(f"'{message}'")
            print(f"Character count: {len(message)}")
            
            return ConnectionMessage(
                message=message,
                context={
                    "profile": profile.dict(),
                    "query": query_context.dict(exclude_none=True)
                }
            )
        except Exception as e:
            print(f"Error generating message: {str(e)}")
            fallback_message = f"Hi {profile.name}, I'm interested in connecting given your experience in {profile.headline}. Best regards, Ramdeen"
            print(f"\nUsing fallback message: '{fallback_message}'")
            return ConnectionMessage(
                message=fallback_message
            )
    
    def send_connection_request(self, profile: LinkedInProfile, query_context: SearchQuery) -> bool:
        """Send a connection request with an auto-generated message"""
        try:
            # Generate personalized message
            connection_message = self.generate_connection_message(profile, query_context)
            
            self.scraper.driver.get(profile.profile_url)
            time.sleep(DELAY_BETWEEN_REQUESTS)
            
            # Scroll through the page to ensure all elements are loaded
            self.scraper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)  # Give more time for elements to load
            
            # Find all primary buttons
            connect_buttons = self.scraper.driver.find_elements(
                By.CSS_SELECTOR, 
                "button.artdeco-button--2.artdeco-button--primary"
            )
            
            if not connect_buttons:
                raise Exception("No connect buttons found on the profile")
            
            # Get the last connect button (the one we want)
            connect_button = connect_buttons[-1]
            
            # Scroll the button into view and click
            self.scraper.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", connect_button)
            time.sleep(2)  # Give time for any overlays to clear
            
            # Try to click using JavaScript if regular click fails
            try:
                connect_button.click()
            except Exception:
                self.scraper.driver.execute_script("arguments[0].click();", connect_button)
            
            time.sleep(2)  # Wait for modal to appear
            
            try:
                # Wait for and click "Add a note" button with exact classes
                add_note_button = WebDriverWait(self.scraper.driver, 5).until(
                    EC.element_to_be_clickable((
                        By.CSS_SELECTOR,
                        "button.artdeco-button.artdeco-button--muted.artdeco-button--2.artdeco-button--secondary"
                    ))
                )
                add_note_button.click()
                time.sleep(1)
                
                # Wait for and fill the message textarea
                message_field = WebDriverWait(self.scraper.driver, 5).until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR, 
                        "textarea#custom-message, textarea[name='message']"
                    ))
                )
                message_field.send_keys(connection_message.message)
                
                # Wait for and click the Send button (first button with these classes)
                send_button = WebDriverWait(self.scraper.driver, 5).until(
                    EC.element_to_be_clickable((
                        By.CSS_SELECTOR,
                        "button.artdeco-button.artdeco-button--2.artdeco-button--primary"
                    ))
                )
                print("Found Send button")
                send_button.click()
                print("Clicked Send button")
                
            except Exception as e:
                if FeatureFlags.DEBUG_MODE:
                    print(f"Failed to add note: {str(e)}")
                # If adding note fails, try to send without note
                send_without_note = WebDriverWait(self.scraper.driver, 5).until(
                    EC.element_to_be_clickable((
                        By.CSS_SELECTOR,
                        "button.artdeco-button--primary[aria-label='Send without a note']"
                    ))
                )
                send_without_note.click()
            
            time.sleep(DELAY_BETWEEN_REQUESTS)  # Wait before next action
            return True
            
        except Exception as e:
            print(f"Failed to send connection request: {str(e)}")
            if FeatureFlags.DEBUG_MODE:
                import traceback
                traceback.print_exc()
            return False 