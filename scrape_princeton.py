import requests
from bs4 import BeautifulSoup
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_driver():
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()))

def scrape_faculty_page(url):
    driver = initialize_driver()
    try:
        logger.info(f"Accessing URL: {url}")
        driver.get(url)
        
        # Wait for the faculty list to load
        wait = WebDriverWait(driver, 20)
        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "content-list-item")))
        except TimeoutException:
            logger.error("Timed out waiting for faculty list to load")
            return []

        # Scroll to the bottom of the page until no more new content is loaded
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for the page to load
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # Now that all content is loaded, parse the page
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        people_links = []
        for item in soup.find_all('div', class_='content-list-item-details'):
            link = item.find('span', class_='field--name-title').find('a')
            if link and link.get('href'):
                full_url = requests.compat.urljoin(url, link['href'])
                people_links.append(full_url)
        
        logger.info(f"Found {len(people_links)} faculty links")
        
        # If we still haven't found any links, log the page source for debugging
        if not people_links:
            logger.error("No faculty links found. Page source:")
            logger.error(driver.page_source)
        
        return people_links
    finally:
        driver.quit()

def scrape_person_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    data = {}
    
    # Name
    name_elem = soup.find('h1', class_='page-title')
    data['name'] = name_elem.text.strip() if name_elem else "No name found"
    
    # Position
    position_elem = soup.find('div', class_='field--name-field-ps-people-title')
    data['position'] = position_elem.find('div', class_='field__item').text.strip() if position_elem else "No position found"
    
    # Phone
    phone_elem = soup.find('div', class_='field--name-field-ps-people-phone')
    data['phone'] = phone_elem.find('div', class_='field__item').text.strip() if phone_elem else "No phone found"
    
    # Email
    email_elem = soup.find('div', class_='field--name-field-ps-people-email')
    if email_elem:
        email_span = email_elem.find('span', class_='__cf_email__')
        if email_span:
            data['email'] = email_span['data-cfemail']
        else:
            data['email'] = "Email protected"
    else:
        data['email'] = "No email found"
    
    # CV
    cv_elem = soup.find('div', class_='field--name-field-ps-people-cv')
    data['cv'] = requests.compat.urljoin(url, cv_elem.find('a')['href']) if cv_elem else "No CV found"
    
    # Specialties (using Areas of Interest)
    specialties_elem = soup.find('div', class_='field--name-field-history-area-of-interest')
    if specialties_elem:
        specialties = specialties_elem.find_all('div', class_='field__item')
        data['specialties'] = '; '.join([s.text.strip() for s in specialties if '(In alphabetical order)' not in s.text])
    else:
        data['specialties'] = "No specialties found"
    
    # Education
    education_elem = soup.find('h2', string='Education')
    if education_elem:
        education = education_elem.find_next('p')
        data['education'] = education.text.strip() if education else "No education found"
    else:
        data['education'] = "No education found"
    
    # Photo
    photo_elem = soup.find('div', class_='field--name-field-ps-featured-image')
    if photo_elem:
        img = photo_elem.find('img')
        data['photo'] = requests.compat.urljoin(url, img['src']) if img else "No photo found"
    else:
        data['photo'] = "No photo found"
    
    # Intro (using the first paragraph of the bio)
    intro_elem = soup.find('div', class_='field--name-field-ps-body')
    if intro_elem:
        intro = intro_elem.find('p')
        data['intro'] = intro.text.strip() if intro else "No intro found"
    else:
        data['intro'] = "No intro found"
    
    # Publications
    publications_block = soup.find('div', class_='block-ps-history-person-publications-list')
    if publications_block:
        publications = publications_block.find_all('div', class_='publication-title')
        data['publications'] = '; '.join([p.text.strip() for p in publications])
    else:
        data['publications'] = "No publications found"
    
    return data

def main():
    faculty_url = "https://history.princeton.edu/people/faculty"
    people_links = scrape_faculty_page(faculty_url)
    
    faculty_data = []
    
    for link in people_links:
        person_data = scrape_person_page(link)
        faculty_data.append(person_data)
        print(f"Scraped data for {person_data['name']}")
        time.sleep(1)  # Add a 1-second delay between requests
    
    with open('faculty_data_princeton.json', 'w', encoding='utf-8') as jsonfile:
        json.dump(faculty_data, jsonfile, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()