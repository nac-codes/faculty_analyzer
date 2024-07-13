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
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
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
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href^='/history/faculty/']")))
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
        for link in soup.find_all('a', href=lambda href: href and href.startswith('/history/faculty/')):
            # make sure link is not in  https://liberalarts.utexas.edu/history/faculty/ https://liberalarts.utexas.edu/history/faculty/thematic-fields/ https://liberalarts.utexas.edu/history/faculty/resources.html https://liberalarts.utexas.edu/history/faculty/online-teaching.html https://liberalarts.utexas.edu/history/faculty/book-publications.html
            if link['href'] == '/history/faculty/thematic-fields/' or link['href'] == '/history/faculty/resources.html' or link['href'] == '/history/faculty/online-teaching.html' or link['href'] == '/history/faculty/book-publications.html' or link['href'] == '/history/faculty/':
                continue

            full_url = 'https://liberalarts.utexas.edu' + link['href']
            people_links.append(full_url)
        
        logger.info(f"Found {len(people_links)} faculty links")
        
        if not people_links:
            logger.error("No faculty links found. Page source:")
            logger.error(driver.page_source)
        
        return people_links
    finally:
        driver.quit()

def scrape_person_page(url):
    logging.debug(f"Scraping URL: {url}")
    driver = initialize_driver()
    try:
        driver.get(url)
        
        # Wait for the content to load
        wait = WebDriverWait(driver, 20)
        try:
            wait.until(EC.presence_of_element_located((By.ID, "person-profile")))
        except TimeoutException:
            logging.error(f"Timed out waiting for profile to load: {url}")
            return {}

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        data = {}
        
        # Name
        name_elem = soup.find('h1')
        data['name'] = name_elem.text.strip() if name_elem else "No name found"
        logging.debug(f"Name: {data['name']}")
        
        # Position
        position_elem = soup.find('p', class_='title')
        data['position'] = position_elem.text.strip() if position_elem else "No position found"
        logging.debug(f"Position: {data['position']}")
        
        # Education
        degree_elem = soup.find('p', class_='degree')
        data['education'] = degree_elem.text.strip() if degree_elem else "No education found"
        logging.debug(f"Education: {data['education']}")
        
        # CV
        cv_elem = soup.find('p', class_='cv')
        data['cv'] = cv_elem.find('a')['href'] if cv_elem and cv_elem.find('a') else "No CV found"
        logging.debug(f"CV: {data['cv']}")
        
        # Email
        email_elem = soup.find('p', class_='email')
        data['email'] = email_elem.find('a').text.strip() if email_elem and email_elem.find('a') else "No email found"
        logging.debug(f"Email: {data['email']}")
        
        # Phone
        phone_elem = soup.find('p', class_='phone')
        data['phone'] = phone_elem.text.strip() if phone_elem else "No phone found"
        logging.debug(f"Phone: {data['phone']}")
        
        # Office
        office_elem = soup.find('p', class_='office')
        data['office'] = office_elem.text.strip() if office_elem else "No office found"
        logging.debug(f"Office: {data['office']}")
        
        # Photo
        photo_elem = soup.find('img', class_='profile-image')
        data['photo'] = photo_elem['src'] if photo_elem else "No photo found"
        logging.debug(f"Photo: {data['photo']}")
        
        # Intro paragraphs
        intro_elems = soup.find_all('p', attrs={'data-v-4352a9ba': ''})
        intro_paragraphs = [elem.get_text(strip=True) for elem in intro_elems]
        data['intro'] = ' '.join(intro_paragraphs) if intro_paragraphs else "No intro found"
        logger.debug(f"Intro: {data['intro']}")
        
        # Courses
        courses_elems = soup.find_all('h4', attrs={'data-v-34dfe718': ''})
        courses = [elem.get_text(strip=True).replace('\n', ' ').replace('•', ' - ') for elem in courses_elems]
        data['courses'] = '; '.join(courses) if courses else "No courses found"
        logger.debug(f"Courses: {data['courses']}")

        return data
    finally:
        driver.quit()

def main():
    faculty_url = "https://liberalarts.utexas.edu/history/faculty/"
    people_links = scrape_faculty_page(faculty_url)
    
    faculty_data = []
    
    for link in people_links:
        try:
            person_data = scrape_person_page(link)
            faculty_data.append(person_data)
            logging.info(f"Scraped data for {person_data['name']}")
        except Exception as e:
            logging.error(f"Error scraping {link}: {str(e)}", exc_info=True)
            # Optionally, add a placeholder entry for failed scrapes
            faculty_data.append({"name": "Scraping failed", "url": link})
        time.sleep(1)  # Add a 1-second delay between requests
    
    with open('faculty_data_utAustin.json', 'w', encoding='utf-8') as jsonfile:
        json.dump(faculty_data, jsonfile, ensure_ascii=False, indent=4)

    logging.info(f"Scraped {len(faculty_data)} faculty members. Check faculty_data_ut_austin.json for results.")

if __name__ == "__main__":
    main()