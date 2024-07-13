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
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "node-person")))
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
        for article in soup.find_all('article', class_='node-person'):
            link = article.find('h1', class_='node-title').find('a')
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
    name_elem = soup.find('h1', class_='node-title')
    data['name'] = name_elem.text.strip() if name_elem else "No name found"
    
    # Position
    position_elem = soup.find('div', class_='field-name-field-professional-title')
    data['position'] = position_elem.text.strip() if position_elem else "No position found"
    
    # Phone
    phone_elem = soup.find('div', class_='field-name-field-phone')
    data['phone'] = phone_elem.text.strip() if phone_elem else "No phone found"
    
    # Email
    email_elem = soup.find('div', class_='field-name-field-email')
    data['email'] = email_elem.find('a').text.strip() if email_elem and email_elem.find('a') else "No email found"
    
    # CV (not typically present, keeping the column for consistency)
    data['cv'] = "No CV found"
    
    # Specialties (using Theme and Methodology as an equivalent)
    specialties_elem = soup.find('div', class_='block theme')
    if specialties_elem:
        specialties = [a.text for a in specialties_elem.find_all('a')]
        data['specialties'] = '; '.join(specialties)
    else:
        data['specialties'] = "No specialties found"
    
    # Education (not typically present, keeping the column for consistency)
    data['education'] = "No education found"
    
    # Photo
    photo_elem = soup.find('img', class_='image-style-profile-full')
    data['photo'] = requests.compat.urljoin(url, photo_elem['src']) if photo_elem else "No photo found"
    
    # Intro (now capturing the entire main body content)
    intro_elem = soup.find('div', class_='field-name-body')
    if intro_elem:
        paragraphs = intro_elem.find_all('p')
        intro_text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])
        data['intro'] = intro_text if intro_text else "No intro found"
    else:
        data['intro'] = "No intro found"
    
    # Publications (not typically present in the same format, keeping the column for consistency)
    data['publications'] = "No publications found"
    
    return data

def main():
    faculty_url = "https://history.fas.harvard.edu/people/faculty_alpha"
    people_links = scrape_faculty_page(faculty_url)
    
    faculty_data = []
    
    for link in people_links:
        person_data = scrape_person_page(link)
        faculty_data.append(person_data)
        print(f"Scraped data for {person_data['name']}")
        time.sleep(1)  # Add a 1-second delay between requests
    
    with open('faculty_data_harvard.json', 'w', encoding='utf-8') as jsonfile:
        json.dump(faculty_data, jsonfile, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()