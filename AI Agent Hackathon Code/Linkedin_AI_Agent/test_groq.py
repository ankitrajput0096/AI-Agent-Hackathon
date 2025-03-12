from query_processor import QueryProcessor
from config import FeatureFlags, GROQ_API_KEY
import json

def test_groq_query_parsing():
    """Test GROQ's ability to parse different types of queries"""
    
    if not GROQ_API_KEY:
        print("Error: GROQ API key not found in environment variables")
        return False
        
    test_queries = [
        "Find software engineers at Microsoft for referral",
        "Connect with HR managers at Google in San Francisco",
        "Looking for senior developers at Amazon in Seattle",
        "Find technical recruiters at Meta for networking"
    ]
    
    query_processor = QueryProcessor()
    
    print("\n=== Testing GROQ Query Parsing ===\n")
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        try:
            # Test raw GROQ parsing
            # parsed_query = query_processor._parse_query_with_groq(query)
            # print("\nParsed result:")
            # print(json.dumps(parsed_query.dict(exclude_none=True), indent=2))
            
            # Test search parameter generation
            search_params = query_processor.process_query(query)
            print("\nGenerated search parameters:")
            print(json.dumps(search_params.dict(exclude_none=True), indent=2))
            
            print("\n✅ Query processed successfully")
            
        except Exception as e:
            print(f"\n❌ Error processing query: {str(e)}")
            return False
    
    return True
    try:
        # Define the prompt template
        prompt = f"""
        Given this search query: "{query}"
        Extract the following information in JSON format:
        {{
            "keywords": "the search terms",
            "title": "job title if specified",
            "company": "company name if specified",
            "location": "location if specified"
        }}
        Only include fields that are explicitly mentioned in the query.
        """
        
        # Call GROQ API
        response = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts search parameters from queries."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="mixtral-8x7b-32768",
            temperature=0,
            max_tokens=500,
        )
        
        # Extract the actual response content
        print(f"\nRaw LLM Response:\n{response}")
        llm_response = response.choices[0].message.content
        
        # Parse the response
        parsed_result = parse_llm_response(llm_response)
        print("\nParsed result:")
        print(parsed_result)
        
        # Convert to search parameters
        search_params = {
            "keywords": parsed_result.get("keywords", ""),
            "connection_degree": ["2nd"],
            "network_depth": "S",
            "origin": "SEARCH_RESULTS"
        }
        
        return search_params
        
    except Exception as e:
        print(f"Error generating search parameters: {e}")
        return {}

if __name__ == "__main__":
    if test_groq_query_parsing():
        print("\n✅ All GROQ tests passed successfully!")
    else:
        print("\n❌ Some GROQ tests failed") 