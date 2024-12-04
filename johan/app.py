import requests
import re
import csv
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright
import concurrent.futures

def normalize_url(url):
    normalized_url = url.lower().replace('www.', '')
    return normalized_url

def is_image_url(url):
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.tiff'}
    return any(url.lower().endswith(ext) for ext in image_extensions)

def has_subpath(url):
    parsed_url = urlparse(url)
    return bool(parsed_url.path and parsed_url.path != '/')

def filter_items_containing_words(input_list):
    words_to_remove = ["/product", "/category", "/collection"]
    result_list = [item for item in input_list if not any(word in item for word in words_to_remove)]
    return result_list

def process_url_list(input_list):
    filtered_urls = [url for url in input_list if '#' not in url]

    if len(filtered_urls) > 10:
        sorted_list = sorted(filtered_urls, key=len)
        return sorted_list[:10]
    else:
        return filtered_urls

def get_all_internal_pages(base_url):

    subpath_check = has_subpath(base_url)

    if (subpath_check == True):
        try:
            response = requests.get(base_url, timeout=15)
            if response.status_code == 200:

                base_url = normalize_url(response.url)
                pages_to_visit = [base_url]
                base_domain = normalize_url(urlparse(base_url).netloc)

                return [base_domain, [base_url]]

            else:
                # print("Link Not Working!")
                return False
        except Exception as e:
            # print(f"Error accessing {base_url}: {e}")
            return False
    else:

        try:
            response = requests.get(base_url, timeout=15)
            if response.status_code == 200:

                base_url = normalize_url(response.url)
                pages_to_visit = [base_url]
                base_domain = normalize_url(urlparse(base_url).netloc)

                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract all links from the current page
                links = [urljoin(base_url, a['href']) for a in soup.find_all('a', href=True)]

                # Filter out external links and image links
                internal_links = [
                    link for link in links
                    if normalize_url(urlparse(link).netloc) == base_domain and not is_image_url(link)
                ]

                internal_links = filter_items_containing_words(internal_links)
                internal_links = process_url_list(internal_links)

                # Add new internal links to the list of pages to visit
                pages_to_visit.extend(link for link in internal_links)
            else:
                print("Link Not Working!")
                return False

        except Exception as e:
            print(f"Error accessing {base_url}: {e}")
            return False

        pages_to_visit = list(dict.fromkeys(pages_to_visit))
        return [base_domain, pages_to_visit]
    
def get_all_internal_pages_pw(base_url):

    subpath_check = has_subpath(base_url)

    if (subpath_check == True):
        
        pages_to_visit = [base_url]
        base_domain = normalize_url(urlparse(base_url).netloc)
        return [base_domain, [base_url]]
    
    else:

        try:
            page_content = get_page_content_pw(base_url)

            base_url = normalize_url(base_url)
            pages_to_visit = [base_url]
            base_domain = normalize_url(urlparse(base_url).netloc)

            soup = BeautifulSoup(page_content, 'html.parser')

            links = [urljoin(base_url, a['href']) for a in soup.find_all('a', href=True)]

            internal_links = [
                link for link in links
                if normalize_url(urlparse(link).netloc) == base_domain and not is_image_url(link)
            ]

            internal_links = filter_items_containing_words(internal_links)
            internal_links = process_url_list(internal_links)

            pages_to_visit.extend(link for link in internal_links)

        except Exception as e:
            # print(f"Error accessing {base_url}: {e}")
            return False

        pages_to_visit = list(dict.fromkeys(pages_to_visit))
        return [base_domain, pages_to_visit]

def get_page_content_pw(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        print(page.title())
        page_content = page.content()
        browser.close()
        return page_content

def extract_emails_from_page(url):
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
            emails = email_pattern.findall(soup.get_text())

            emails = [x.lower() for x in emails]

            return emails
        else:
            print(f"Failed to retrieve content from {url}. Status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error accessing {url}: {e}")
        return []
    
def extract_emails_from_page_v2(url):
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            strict_email_pattern = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')

            emails = set()
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('mailto:'):
                    email = href.split(':')[1]
                    if strict_email_pattern.match(email):
                        emails.add(email.lower())

            all_emails = strict_email_pattern.findall(soup.get_text())
            for email in all_emails:
                emails.add(email.lower())

            return list(emails)
        else:
            # print(f"Failed to retrieve content from {url}. Status code: {response.status_code}")
            return []
    except Exception as e:
        # print(f"Error accessing {url}: {e}")
        return []

def get_emails_pw(website_list):
    t_email_list = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for website in website_list:
            try:
                page.goto(website)
                print(page.title())
                page_content = page.content()
                #browser.close()
                
                soup = BeautifulSoup(page_content, 'html.parser')
                strict_email_pattern = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')

                emails = []
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if href.startswith('mailto:'):
                        email = href.split(':')[1]
                        if strict_email_pattern.match(email):
                            emails.append(email.lower())

                all_emails = strict_email_pattern.findall(soup.get_text())
                for email in all_emails:
                    emails.append(email.lower())

                t_email_list = t_email_list + emails
            except Exception as e:
                print(e)
                print('PW Failed To Load!')

        try:
            browser.close()
        except:
            print("Failed To Close Browser!")

    return t_email_list

def filter_emails_within_domain(raw_email, base_domain):
    index = raw_email.find(base_domain)
    if index != -1:
        substring = raw_email[:index + len(base_domain)]
        return substring
    else:
        return raw_email

def remove_until_special_char(raw_email):
    special_chars = ['>', '<']
    for char in raw_email:
        if char in special_chars:
            index = raw_email.index(char)
            return raw_email[index+1:]
    return raw_email

def get_email_filters():
    with open('email_prefixs.txt', 'r', encoding='utf-8') as file:
        lines = file.readlines()
    words = []
    for line in lines:
        words.append(line.strip())
    return words

def divide_emails(email_list):
    filter_list = get_email_filters()
    priority_emails = []
    other_emails = []

    for email in email_list:
        split_email = email.split('@')
        if (split_email[0] in filter_list):
            priority_emails.append(email)
        else:
            other_emails.append(email)

    return [priority_emails, other_emails]

def processSingleWebsite(website):
    pw = False
    website = website.strip()

    all_links = get_all_internal_pages(website)

    if (all_links == False):
        all_links = get_all_internal_pages_pw(website)

        if (all_links == False):
            with open('failed.txt', 'a', encoding='utf-8') as file:
                file.write(website + '\n')
            return
        else:
            pw = True

    base_domain = all_links[0]

    if (pw == False):
        emails_list = []
        for link in all_links[1]:
            emails = extract_emails_from_page_v2(link)
            emails_list = emails_list + emails
    else:
        emails_list = get_emails_pw(all_links[1])

    emails_list = list(dict.fromkeys(emails_list))

    filtered_email_list = []
    for raw_email in emails_list:
        the_email = filter_emails_within_domain(raw_email, base_domain)
        filtered_email_list.append(the_email)

    filtered_email_list = list(dict.fromkeys(filtered_email_list))
    print(filtered_email_list)

    divided_emails = divide_emails(filtered_email_list)
    priority_emails = divided_emails[0]
    other_emails = divided_emails[1]

    priority_emails.insert(0, website)
    other_emails.insert(0, website)

    with open('priority_emails.csv', mode='a', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(priority_emails)

    with open('other_emails.csv', mode='a', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(other_emails)

def ProcessWebsiteList(data_list):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(processSingleWebsite, data_list))
        return results

with open('websites.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()

ProcessWebsiteList(lines)

