import json
import groq
from config import GROQ_API_KEY, FeatureFlags
from models import SearchQuery, SearchParameters

class QueryProcessor:
    def __init__(self):
        self.client = groq.Groq(api_key=GROQ_API_KEY)
        self.last_parsed_query = None

    def _parse_query_with_groq(self, query_text: str) -> tuple[SearchQuery, str]:
        """Use GROQ to parse the natural language query and return both metadata and search text"""
        prompt = f"""
        Convert this LinkedIn search query into a natural search string: "{query_text}"
        Return a JSON object with:
        1. search_text: An optimized LinkedIn search string that includes all relevant information
        2. metadata: Original parsed information for context
        
        Example:
        Input: "Find software engineers at Microsoft for referral"
        Output: {{
            "search_text": "software engineer microsoft",
            "metadata": {{
                "company": "Microsoft",
                "role": "software engineer",
                "purpose": "referral"
            }}
        }}
        
        IMPORTANT: The search_text should be optimized for LinkedIn's search, avoiding unnecessary words.
        Return only the JSON object, no additional text.
        """
        
        completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a search query optimizer. Convert natural language queries into efficient search strings."
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
        
        try:
            response_dict = json.loads(completion.choices[0].message.content)
            if FeatureFlags.DEBUG_MODE:
                print(f"\nGROQ Response: {json.dumps(response_dict, indent=2)}")
            
            # Extract both metadata and search_text
            metadata = response_dict.get("metadata", {})
            search_text = response_dict.get("search_text", query_text)
            
            return SearchQuery(**metadata), search_text
            
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return SearchQuery(), query_text

    def process_query(self, query_text: str) -> SearchParameters:
        """Process a natural language query into LinkedIn search parameters"""
        # Get both metadata and search text in one API call
        parsed_query, search_text = self._parse_query_with_groq(query_text)
        self.last_parsed_query = parsed_query
        
        # Build search parameters using the optimized search text
        search_params = {
            "keywords": search_text,  # Use the optimized search text instead of raw query
            "connection_degree": ["1st"],
            "network_depth": "S",
            "origin": "SEARCH_RESULTS"
        }
        
        # Only add location if specifically mentioned
        if parsed_query.location:
            search_params["location"] = parsed_query.location
                
        return SearchParameters(**search_params) 