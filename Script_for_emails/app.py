import re
import requests
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse
from tldextract import extract as tld_extract

phone_pattern = r"""
    (\+46[\s\-]?\d{1,3}[\s\-]?\d{2,3}[\s\-]?\d{2,4}[\s\-]?\d{0,4})|  # International format for Sweden (+46)
    (0046[\s\-]?\d{1,3}[\s\-]?\d{2,3}[\s\-]?\d{2,4}[\s\-]?\d{0,4})| # International format with 00
    (0[1-9]\d{0,2}[\s\-]?\d{3}[\s\-]?\d{2,4}[\s\-]?\d{0,4})|        # Swedish landline (regional codes)
    (07[02369][\s\-]?\d{3}[\s\-]?\d{2,4}[\s\-]?\d{0,4})|             # Swedish mobile numbers
    (020[\s\-]?\d{3,7})|                                             # Toll-free numbers
    (0900[\s\-]?\d{3,6})|                                            # Premium rate numbers
    (077[0-7][\s\-]?\d{3}[\s\-]?\d{2,4}[\s\-]?\d{0,4})|               # Shared cost numbers
    (\d{3}[\s\-]?\d{2,4}[\s\-]?\d{2,4})                              # Local Swedish phone numbers (e.g., "040 - 93 30 00")
"""
email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

priority_keywords = ["info", "kontakt", "hej", "kundtjanst", "support"]

session = HTMLSession()

def fetch_with_retry(url, retries=2, timeout=5):
    for i in range(retries):
        try:
            response = session.get(url, timeout=timeout)
            response.html.render(sleep=1, timeout=20)  
            return response.text
        except Exception as e:
            print(f"Attempt {i+1} failed for {url}: {e}")
    return None

def normalize_phones(phones):
    return {re.sub(r'[\s\-–]+', ' ', phone).strip() for phone_tuple in phones for phone in phone_tuple if phone}

def extract_data(url):
    try:
        print(f"Processing: {url}")
        content = fetch_with_retry(url)
        if content is None:
            return set(), set()

        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text(separator=" ")

        phones = set(re.findall(phone_pattern, text, re.VERBOSE))
        print(f"Extracted phones (raw): {phones}")

        normalized_phones = normalize_phones(phones)
        print(f"Normalized phones: {normalized_phones}")

        emails = set(re.findall(email_pattern, text))
        return normalized_phones, emails
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return set(), set()

def main():
    input_file = "/home/ahmed/email_script/Script_for_emails/sheet_urls.xlsx"
    output_file = "consolidated_output.xlsx"
    failed_urls_file = "failed_urls.txt"

    results = []

    try:
        df = pd.read_excel(input_file)
        url_columns = [col for col in df.columns if "website" in col.lower() or "homepage" in col.lower()]
        urls = df[url_columns].fillna('').values.flatten()
        urls = list(filter(None, urls)) 

        failed_urls = []

        for url in urls:
            if not url.startswith("http"):
                url = f"http://{url}"

            domain = tld_extract(url).domain

            phones, emails = extract_data(url)
            if not emails:
                for prefix in priority_keywords:
                    test_email = f"{prefix}@{domain}.se"
                    emails.add(test_email)

            priority_emails = {email for email in emails if any(k in email.lower() for k in priority_keywords) or ".se" in email}
            other_emails = emails - priority_emails

            results.append({
                "Hemsida": url,
                "Telefonnummer": ", ".join(sorted(phones)) if phones else "No phone numbers found",
                "Prioriterade e-postadresser": ", ".join(sorted(priority_emails)) if priority_emails else "No priority emails found",
                "Andra e-postadresser": ", ".join(sorted(other_emails)) if other_emails else "No other emails found"
            })

        # Save results to Excel
        results_df = pd.DataFrame(results)
        results_df.to_excel(output_file, index=False)

        # Save failed URLs
        with open(failed_urls_file, 'w') as failed_log:
            for failed_url in failed_urls:
                failed_log.write(f"{failed_url}\n")

        print(f"Results saved to {output_file}")
        print(f"Failed URLs logged to {failed_urls_file}")
    except FileNotFoundError:
        print(f"Filen {input_file} hittades inte.")
    except Exception as e:
        print(f"Ett oväntat fel inträffade: {e}")

if __name__ == "__main__":
    main()
