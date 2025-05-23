import requests
import os
import json
from typing import Dict, Any

from dotenv import load_dotenv

# --- Configuration ---
ANYMAILFINDER_API_ENDPOINT = "https://api.anymailfinder.com/v5.0/search/decision-maker.json"
TARGET_DOMAIN = "dhl.com"
DECISION_MAKER_CATEGORY = "hr"  # Category for Human Resources
API_TIMEOUT_SECONDS = 180 # Recommended timeout

# --- Script ---

load_dotenv()

def get_api_key() -> str:
    """Gets the API key from user input or environment variable."""
    # Prioritize environment variable for security
    api_key = os.environ.get("ANYMAILFINDER_API_KEY")
    if api_key:
        print("Using API key from environment variable ANYMAILFINDER_API_KEY")
        return api_key
    else:
        # If not in environment, prompt the user
        api_key = input("Please enter your Anymailfinder API Key: ")
        if not api_key:
            print("API Key is required.")
            exit(1)
        return api_key

def find_hr_manager(api_key: str, domain: str) -> None:
    """Searches for the HR manager at a specific domain and prints the result."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "domain": domain,
        "decision_maker_category": DECISION_MAKER_CATEGORY
    }

    print(f"Searching for {DECISION_MAKER_CATEGORY} at {domain}...")

    try:
        response = requests.post(
            ANYMAILFINDER_API_ENDPOINT,
            headers=headers,
            json=data,
            timeout=API_TIMEOUT_SECONDS
        )

        # Check for HTTP errors (4xx or 5xx)
        response.raise_for_status()

        # Parse the JSON response
        result = response.json()

        # --- Process the API response ---
        if result.get("success") is True and result.get("result") is not None:
            found_person = result["result"]
            name = found_person.get("personFullName", "N/A")
            email = found_person.get("email", "N/A")
            job_title = found_person.get("personJobTitle", "N/A")
            verification_status = "Verified" if found_person.get("emailVerified") else "Risky/Unverified"
            linkedin_url = found_person.get("personLinkedinUrl", "N/A")

            print("\n--- HR Manager Found ---")
            print(f"Company Domain: {domain}")
            print(f"Name: {name}")
            print(f"Email: {email}")
            print(f"Job Title: {job_title}")
            print(f"Verification Status: {verification_status}")
            print(f"LinkedIn URL: {linkedin_url}")
            print("------------------------")

        elif result.get("success") is False:
             error_explained = result.get("error_explained", "No explanation provided.")
             print(f"\nSearch failed for {domain}. API returned an error:")
             print(f"Error: {result.get('error', 'Unknown Error')}")
             print(f"Explanation: {error_explained}")

        else:
            # This handles cases where success is true but result is null, or unexpected structures
            print(f"\nNo {DECISION_MAKER_CATEGORY} email found for {domain}.")
            print(f"API Response success: {result.get('success')}")
            print(f"API Response result: {result.get('result')}") # Print for debugging unexpected no result cases


    except requests.exceptions.Timeout:
        print(f"\nRequest timed out for {domain}.")
    except requests.exceptions.ConnectionError:
         print(f"\nConnection error for {domain}. Check your internet connection.")
    except requests.exceptions.RequestException as e:
        print(f"\nAPI Request failed for {domain}: {e}")
        try:
            # Try to print error details if available in the response body
            if response is not None and response.content:
                 print(f"Response Status Code: {response.status_code}")
                 print(f"Response Body: {response.text}")
        except Exception as parse_error:
            print(f"Could not parse error response body: {parse_error}")

    except Exception as e:
        print(f"\nAn unexpected error occurred for {domain}: {e}")


def main():
    api_key = get_api_key()
    find_hr_manager(api_key, TARGET_DOMAIN)

if __name__ == "__main__":
    main()