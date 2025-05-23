import json

import requests
import csv
import time
import os
import urllib.parse
from typing import List, Dict, Any

from dotenv import load_dotenv

# --- Configuration ---
ANYMAILFINDER_API_ENDPOINT = "https://api.anymailfinder.com/v5.0/search/decision-maker.json"
DECISION_MAKER_CATEGORY = "hr"  # Category for Human Resources
INPUT_DOMAINS_FILE = "domains.txt"  # File containing domains, one per line
OUTPUT_CSV_FILE = "hr_emails_results_bulk.csv"  # Output CSV file
API_TIMEOUT_SECONDS = 180 # Recommended timeout
REQUEST_DELAY_SECONDS = 0.1 # Small delay between requests (API says no rate limits, but a small delay can be gentle)

load_dotenv()

# --- Script ---

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

def clean_domain(domain_input: str) -> str:
    """
    Cleans a domain string by removing URL prefixes (http/https),
    'www.', and trailing slashes.
    """
    if not domain_input:
        return ""

    # Add a dummy scheme if none exists, to help urlparse
    if not domain_input.startswith('http://') and not domain_input.startswith('https://'):
        domain_input = 'http://' + domain_input # Use http as a placeholder

    parsed_url = urllib.parse.urlparse(domain_input)
    cleaned_domain = parsed_url.netloc

    # Remove 'www.' if present
    if cleaned_domain.startswith('www.'):
        cleaned_domain = cleaned_domain[4:]

    # Ensure no trailing slash remains (though netloc shouldn't have one)
    if cleaned_domain.endswith('/'):
        cleaned_domain = cleaned_domain[:-1]

    return cleaned_domain

def read_domains_from_file(filename: str) -> List[str]:
    """
    Reads domains from a text file, one domain per line,
    cleans them, and returns a list of unique, valid domains.
    """
    domains = set() # Use a set to automatically handle duplicates
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                raw_domain = line.strip()
                cleaned = clean_domain(raw_domain)
                if cleaned: # Only add if cleaning resulted in a non-empty string
                    domains.add(cleaned)

        domain_list = list(domains) # Convert back to list
        print(f"Read and cleaned {len(domain_list)} unique domains from {filename}")
        return domain_list
    except FileNotFoundError:
        print(f"Error: Input file '{filename}' not found.")
        exit(1)
    except Exception as e:
        print(f"Error reading domains file: {e}")
        exit(1)

def search_decision_maker(api_key: str, domain: str, category: str) -> Dict[str, Any]:
    """Searches for a decision maker using the Anymailfinder API."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "domain": domain, # Use the cleaned domain here
        "decision_maker_category": category
    }

    print(f"Searching for {category} at {domain}...")

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
        return response.json()

    except requests.exceptions.Timeout:
        print(f"  Request timed out for {domain}.")
        return {"success": False, "error": "timeout", "error_explained": "Request timed out."}
    except requests.exceptions.ConnectionError:
         print(f"  Connection error for {domain}. Check your internet connection.")
         return {"success": False, "error": "connection_error", "error_explained": "Connection error."}
    except requests.exceptions.RequestException as e:
        print(f"  API Request failed for {domain}: {e}")
        status_code = 'N/A'
        response_text = 'N/A'
        try:
            if e.response is not None:
                 status_code = e.response.status_code
                 response_text = e.response.text # Get raw text in case JSON parsing fails
                 error_details = e.response.json() # Attempt to get JSON error details
                 return {"success": False, "error": error_details.get('error', 'request_exception'), "error_explained": error_details.get('error_explained', str(e))}
            else:
                 return {"success": False, "error": "request_exception", "error_explained": str(e)}
        except json.JSONDecodeError:
             # If response body is not JSON
             return {"success": False, "error": "api_error", "error_explained": f"API returned status {status_code} with non-JSON body: {response_text[:100]}..."} # Limit body print
        except Exception as parse_error:
            return {"success": False, "error": "api_error", "error_explained": f"API returned status {status_code} and parsing error: {parse_error}"}
    except Exception as e:
        print(f"  An unexpected error occurred for {domain}: {e}")
        return {"success": False, "error": "unexpected_error", "error_explained": str(e)}


def main():
    api_key = get_api_key()
    domains = read_domains_from_file(INPUT_DOMAINS_FILE)

    if not domains:
        print("No valid domains found in the input file after cleaning. Exiting.")
        return

    with open(OUTPUT_CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Write header row based on expected output
        csv_writer.writerow([
            "Domain Searched",
            "Category Searched",
            "Found Name",
            "Found Email",
            "Email Verified",
            "Job Title",
            "LinkedIn URL",
            "Search Success",
            "API Error Type",
            "API Error Explanation"
        ])

        for domain in domains:
            if not domain:
                continue # Should not happen with cleaned domains

            result = search_decision_maker(api_key, domain, DECISION_MAKER_CATEGORY)

            # --- Process the API response and write to CSV ---
            name = "N/A"
            email = "N/A"
            email_verified = "N/A"
            job_title = "N/A"
            linkedin_url = "N/A"
            search_success = "False" # Default to false, update if successful
            api_error_type = "N/A"
            api_error_explained = "N/A"


            if result.get("success") is True and result.get("result") is not None:
                # Successful find
                found_person = result["result"]
                name = found_person.get("personFullName", "N/A")
                email = found_person.get("email", "N/A")
                email_verified = found_person.get("emailVerified", False) # Get boolean, will write as True/False
                job_title = found_person.get("personJobTitle", "N/A")
                linkedin_url = found_person.get("personLinkedinUrl", "N/A")
                search_success = "True"
                print(f"  Success: Found {name} ({email})")

            elif result.get("success") is False:
                 # API returned a specific error (e.g., bad_request, not_found, payment_needed) or our script caught an exception
                 api_error_type = result.get("error", "Unknown")
                 api_error_explained = result.get("error_explained", "No explanation provided.")
                 print(f"  Failed: {api_error_type} - {api_error_explained}")

            else:
                # Handles cases with success=True but result=None, or unexpected API response structure
                search_success = "False"
                api_error_type = "no_result_found"
                api_error_explained = "API call successful but no result found or unexpected response structure."
                print(f"  Failed: No result found or unexpected response.")


            # Write the row to the CSV
            csv_writer.writerow([
                domain,
                DECISION_MAKER_CATEGORY,
                name,
                email,
                email_verified,
                job_title,
                linkedin_url,
                search_success,
                api_error_type,
                api_error_explained
            ])

            # Add a small delay between requests to be courteous
            time.sleep(REQUEST_DELAY_SECONDS)


    print(f"\nScript finished. Results saved to {OUTPUT_CSV_FILE}")

if __name__ == "__main__":
    main()