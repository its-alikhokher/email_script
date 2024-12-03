import re
import requests
from bs4 import BeautifulSoup
import html  # For decoding HTML entities
import time


phone_pattern = (
    r'0[1-9]\d{0,2}[\s\-–]?\d{3}[\s\-–]?\d{2,4}[\s\-–]?\d{0,4}'  # Geographic numbers
    r'|07[02369][\s\-–]?\d{3}[\s\-–]?\d{2,4}[\s\-–]?\d{0,4}'      # Mobile numbers
    r'|020[\s\-–]?\d{3,7}'                                           # Toll-free numbers
    r'|0900[\s\-–]?\d{3,6}'                                          # Premium rate numbers
    r'|077[0-7][\s\-–]?\d{3}[\s\-–]?\d{2,4}[\s\-–]?\d{0,4}'        # Shared cost numbers
)

# Email regex pattern
email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

# Keywords for categorizing emails
priority_keywords = ["info", "kontakt"]
other_keywords = ["hej", "kundtjanst", "support"]

# Retry logic for requests
def fetch_with_retry(url, retries=3, timeout=10):
    for i in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()  # Check for errors
            return response.text
        except requests.RequestException as e:
            print(f"Attempt {i+1} failed for {url}: {e}")
            time.sleep(2 ** i)  # Exponential backoff
    return None

# Extract phone numbers and emails from HTML content
def extract_data(url):
    try:
        print(f"Processing: {url}")
        content = fetch_with_retry(url)
        if content is None:
            return set(), set()  # If unable to fetch, return empty sets
        
        # Decode HTML entities like &#8211; to actual characters
        content = html.unescape(content)

        soup = BeautifulSoup(content, 'html.parser')

        # Extract phone numbers and emails from the page text
        # Ensure the phone number is formatted with spaces, no dashes
        phones = set(re.findall(phone_pattern, soup.get_text()))

        # Normalize the phone numbers to ensure they are displayed correctly
        normalized_phones = set()
        for phone in phones:
            phone = phone.replace("–", "-")  # Replace any en dash with a regular dash
            phone = re.sub(r'[\s\-–]+', ' ', phone)  # Normalize spaces/dashes
            normalized_phones.add(phone.strip())

        emails = set(re.findall(email_pattern, soup.get_text()))

        return normalized_phones, emails

    except Exception as e:
        print(f"Error processing {url}: {e}")
        return set(), set()

# Main function
def main():
    input_file = "websites.txt"  # Input file with website links
    priority_email_file = "priority_email.txt"  # File for priority emails
    other_email_file = "other_email.txt"  # File for other emails

    try:
        # Read URLs from the input file
        with open(input_file, 'r') as file:
            urls = [line.strip() for line in file.readlines()]

        # Prepare files for output
        with open(priority_email_file, 'w') as priority_output, open(other_email_file, 'w') as other_output:
            for url in urls:
                phones, emails = extract_data(url)

                # Categorize emails into priority and others
                priority_emails = {email for email in emails if any(keyword in email for keyword in priority_keywords)}
                other_emails = emails - priority_emails

                # Write results to the priority email file
                if priority_emails or phones:
                    priority_output.write(f"Website: {url}\n")
                    if phones:
                        priority_output.write(f"Phone Numbers: {', '.join(sorted(phones))}\n")
                    if priority_emails:
                        priority_output.write(f"Priority Emails: {', '.join(sorted(priority_emails))}\n")
                    priority_output.write("\n")

                # Write results to the other email file
                if other_emails or phones:
                    other_output.write(f"Website: {url}\n")
                    if phones:
                        other_output.write(f"Phone Numbers: {', '.join(sorted(phones))}\n")
                    if other_emails:
                        other_output.write(f"Emails: {', '.join(sorted(other_emails))}\n")
                    other_output.write("\n")

        print(f"Results saved to {priority_email_file} and {other_email_file}")

    except FileNotFoundError:
        print(f"The file {input_file} was not found.")

if __name__ == "__main__":
    main()
