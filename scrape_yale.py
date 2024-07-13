import requests
from bs4 import BeautifulSoup
import json
import time

def scrape_faculty_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    people_links = []
    faculty_table = soup.find('table', class_='views-table')
    if faculty_table:
        for row in faculty_table.find_all('tr')[1:]:  # Skip the header row
            link = row.find('a')
            if link and link.get('href'):
                people_links.append('https://history.yale.edu' + link['href'])
    
    return people_links

def scrape_person_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    data = {}
    
    # Name
    name_elem = soup.find('h1', class_='title', id='page-title')
    data['name'] = name_elem.text.strip() if name_elem else "No name found"
    
    # Position
    position_elem = soup.find('div', class_='field-name-field-title')
    data['position'] = position_elem.text.strip() if position_elem else "No position found"
    
    # Email
    email_elem = soup.find('div', class_='field-name-field-email')
    data['email'] = email_elem.find('a').text.strip() if email_elem and email_elem.find('a') else "No email found"
    
    # Office
    office_elem = soup.find('div', class_='field-name-field-office')
    data['phone'] = office_elem.find('div', class_='field-item').text.strip() if office_elem else "No office found"
    
    # Phone
    phone_elem = soup.find('div', class_='field-name-field-phone')
    data['phone'] = phone_elem.find('div', class_='field-item').text.strip() if phone_elem else "No phone found"
    
    # CV
    cv_elem = soup.find('div', class_='field-name-field-cv')
    if cv_elem and cv_elem.find('a'):
        data['cv'] = 'https://history.yale.edu' + cv_elem.find('a')['href']
    else:
        data['cv'] = "No CV found"
    
    # Fields of interest (Specialties)
    specialties_elem = soup.find('div', class_='field-name-field-field-s-of-interest')
    data['specialties'] = specialties_elem.find('div', class_='field-item').text.strip() if specialties_elem else "No specialties found"
    
    # Education (not directly available on the page)
    data['education'] = "No education information found"
    
    # Photo
    photo_elem = soup.find('div', class_='user-picture').find('img')
    data['photo'] = 'https://history.yale.edu' + photo_elem['src'] if photo_elem else "No photo found"
    
    # Bio
    bio_elem = soup.find('div', class_='field-name-field-bio')
    if bio_elem:
        paragraphs = bio_elem.find_all('p')
        data['intro'] = ' '.join([p.text.strip() for p in paragraphs[:2]])  # First two paragraphs as intro
    else:
        data['intro'] = "No bio found"
    
    # Publications (not directly available on the page)
    data['publications'] = "No publications information found"
    
    return data

def main():
    base_url = "https://history.yale.edu/people/faculty"
    all_people_links = []
    
    # Scrape main page and additional pages
    for i in range(5):  # 0 to 4
        url = base_url if i == 0 else f"{base_url}?page={i}"
        people_links = scrape_faculty_page(url)
        all_people_links.extend(people_links)
        print(f"Scraped {len(people_links)} links from page {i}")
        time.sleep(1)  # Be polite, wait a second between requests
    
    faculty_data = []
    
    for link in all_people_links:
        try:
            person_data = scrape_person_page(link)
            faculty_data.append(person_data)
            print(f"Scraped data for {person_data['name']}")
        except Exception as e:
            print(f"Error scraping {link}: {str(e)}")
        time.sleep(1)  # Be polite, wait a second between requests
    
    with open('faculty_data_yale.json', 'w', encoding='utf-8') as jsonfile:
        json.dump(faculty_data, jsonfile, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()