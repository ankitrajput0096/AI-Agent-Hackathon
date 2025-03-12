from query_processor import QueryProcessor
from linkedin_scraper import LinkedInScraper
from connection_manager import ConnectionManager
from config import FeatureFlags
import sys
import csv

def main():
    # Check if we're only testing GROQ
    if FeatureFlags.TEST_GROQ_ONLY:
        print("Running in GROQ test mode only...")
        from test_groq import test_groq_query_parsing
        test_groq_query_parsing()
        return
        
    # Normal application flow
    try:
        # Initialize components
        query_processor = QueryProcessor()
        scraper = LinkedInScraper()
        connection_manager = ConnectionManager(scraper)
        
        # Login to LinkedIn
        scraper.login()
        
        while True:
            # Get user input
            query = input("Enter your search query (or 'quit' to exit): ")
            if query.lower() == 'quit':
                break
                
            if FeatureFlags.DEBUG_MODE:
                print("\nDebug: Processing query...")
                
            # Process the query
            search_params = query_processor.process_query(query)
            query_context = query_processor.last_parsed_query
            
            if FeatureFlags.DEBUG_MODE:
                print(f"\nDebug: Search parameters: {search_params.dict()}")
            
            # Search for profiles
            profiles = scraper.search_profiles(search_params)
            print("Profiles : ", profiles)
            
            if not profiles:
                print("No profiles found matching the search criteria")
                continue
            
            # Take top 10 profiles (if more than 10 are returned)
            top_profiles = profiles[:10]
            print("Top profiles",top_profiles)
            
            # Display results
            print("\nTop 10 profiles found:")
            for i, profile in enumerate(top_profiles, 1):
                print(f"\n{i}. {profile.name}")
                print(f"   Title: {profile.headline}")
                print(f"   Profile URL: {profile.profile_url}")
            
            # Export to CSV
            csv_file = "linkedin_top_10_results.csv"
            try:
                with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    # Write header
                    writer.writerow(["Rank", "Name", "Title", "Profile Link"])
                    # Write data
                    for i, profile in enumerate(top_profiles, 1):
                        writer.writerow([i, profile.name, profile.headline, profile.profile_url])
                print(f"\nCSV file '{csv_file}' has been created successfully. You can download it from the current directory.")
            except Exception as e:
                print(f"Error creating CSV file: {str(e)}")
                if FeatureFlags.DEBUG_MODE:
                    import traceback
                    traceback.print_exc()
            # query = input("Enter your search query (or 'quit' to exit): ")
            # if query.lower() == 'quit':
            #     break
                
            # if FeatureFlags.DEBUG_MODE:
            #     print("\nDebug: Processing query...")
                
            # # Process the query
            # search_params = query_processor.process_query(query)
            # query_context = query_processor.last_parsed_query
            
            # if FeatureFlags.DEBUG_MODE:
            #     print(f"\nDebug: Search parameters: {search_params.dict()}")
            
            # # Search for profiles
            # profiles = scraper.search_profiles(search_params)
            
            # if not profiles:
            #     print("No profiles found matching the search criteria")
            #     continue
            
            # # Display results
            # print("\nFound profiles:")
            # for i, profile in enumerate(profiles, 1):
            #     print(f"\n{i}. {profile.name}")
            #     print(f"   {profile.headline}")
            #     print(f"   {profile.profile_url}")
            
            # # Ask which profiles to connect with
            # connect_choice = input("\nEnter the numbers of profiles you want to connect with (comma-separated) or 'skip': ")
            # if connect_choice.lower() != 'skip':
            #     profile_indices = [int(x.strip()) - 1 for x in connect_choice.split(',')]
                
            #     # Send connection requests with auto-generated messages
            #     for idx in profile_indices:
            #         if 0 <= idx < len(profiles):
            #             try:
            #                 success = connection_manager.send_connection_request(profiles[idx], query_context)
            #                 if success:
            #                     print(f"Successfully sent connection request to {profiles[idx].name}")
            #                 else:
            #                     print(f"Failed to send connection request to {profiles[idx].name}")
            #             except Exception as e:
            #                 print(f"Error sending connection request: {str(e)}")
            #                 if FeatureFlags.DEBUG_MODE:
            #                     import traceback
            #                     traceback.print_exc()
        
        # Clean up
        scraper.driver.quit()
        
    except Exception as e:
        print(f"Error in main application: {str(e)}")
        if FeatureFlags.DEBUG_MODE:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 