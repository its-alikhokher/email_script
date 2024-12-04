import re
import requests

# Main function
def main():
    input_file = "websites.txt"  # Input file with website links
    output_file = "output_results.txt"  # File to save results

    try:
        # Read URLs from the input file
        with open(input_file, 'r') as file:
            urls = [line.strip() for line in file.readlines()]

        with open(output_file, 'w') as output:
            for url in urls:
                try:
                    print(f"Processing: {url}")
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()  # Raise error if the request fails
                    content = response.text

                    # Regex patterns for Swedish phone numbers and emails
                    phone_pattern = r'\+46\s?\d{1,3}\s?\d{3,4}\s?\d{4}'
                    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

                    phones = re.findall(phone_pattern, content)
                    emails = re.findall(email_pattern, content)

                    # Save results to output file
                    output.write(f"Website: {url}\n")
                    output.write(f"Phone Numbers: {', '.join(phones) if phones else 'None'}\n")
                    output.write(f"Emails: {', '.join(emails) if emails else 'None'}\n")
                    output.write("\n")
                except Exception as e:
                    output.write(f"Website: {url}\nError: {e}\n\n")
                    print(f"Error processing {url}: {e}")

        print(f"Results saved to {output_file}")

    except FileNotFoundError:
        print(f"The file {input_file} was not found.")

if __name__ == "__main__":
    main()