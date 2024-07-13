import requests
from bs4 import BeautifulSoup
import json
import time

def scrape_faculty_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    people_links = []
    faculty_list = soup.find_all('div', class_='row people-list views-row')
    for item in faculty_list:
        link = item.find('a')
        if link and link.get('href'):
            people_links.append('https://www.history.upenn.edu' + link['href'])
    
    return people_links
def scrape_person_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    data = {}
    
    # Name
    name_elem = soup.find('h1', class_='page-header')
    if name_elem:
        name_span = name_elem.find('span')
        data['name'] = name_span.text.strip() if name_span else name_elem.text.strip()
    else:
        name_elem = soup.find('h1', class_='title')
        data['name'] = name_elem.text.strip() if name_elem else "No name found"
    
    # Position
    position_elem = soup.find('p', class_='title')
    if position_elem:
        title_span = position_elem.find('span', class_='title')
        data['position'] = title_span.text.strip() if title_span else position_elem.text.strip()
    else:
        data['position'] = "No position found"
    
    # Contact info
    contact_elem = soup.find('p', class_='contact')
    if contact_elem:
        email = contact_elem.find('span', class_='email')
        phone = contact_elem.find('span', class_='phone')
        data['email'] = email.find('a').text.strip() if email and email.find('a') else "No email found"
        data['phone'] = phone.find('a').text.strip() if phone and phone.find('a') else "No phone found"
    else:
        data['email'] = "No email found"
        data['phone'] = "No phone found"
    
    # Office
    office_elem = soup.find('p', text=lambda text: text and 'Hall' in text)
    data['office'] = office_elem.text.strip() if office_elem else "No office found"
    
    # CV (not directly available on the page)
    data['cv'] = "No CV found"
    
    # Specialties
    specialties_elem = soup.find('div', class_='field-specialties-and-regions')
    data['specialties'] = specialties_elem.text.strip() if specialties_elem else "No specialties found"
    
    # Education
    education_elem = soup.find('div', class_='field-education')
    data['education'] = education_elem.text.strip() if education_elem else "No education found"
    
    # Photo
    photo_elem = soup.find('img', class_='img-responsive')
    data['photo'] = 'https://www.history.upenn.edu' + photo_elem['src'] if photo_elem and photo_elem.get('src') else "No photo found"
    
    # Intro
    intro_elem = soup.find('div', class_='body')
    if intro_elem:
        paragraphs = intro_elem.find_all('p')
        data['intro'] = ' '.join([p.text.strip() for p in paragraphs[:2]])  # First two paragraphs as intro
    else:
        data['intro'] = "No intro found"
    
    # Courses Taught
    courses_elem = soup.find('div', class_='field-courses-taught')
    data['courses'] = courses_elem.text.strip() if courses_elem else "No courses found"
    
    return data
def main():
    faculty_url = "https://www.history.upenn.edu/people"
    people_links = scrape_faculty_page(faculty_url)
    
    faculty_data = []
    
    for link in people_links:
        try:
            person_data = scrape_person_page(link)
            faculty_data.append(person_data)
            print(f"Scraped data for {person_data['name']}")
        except Exception as e:
            print(f"Error scraping {link}: {str(e)}")
            # Add a placeholder entry for the failed scrape
            faculty_data.append({"name": "Scraping failed", "url": link})
        time.sleep(1)  # Be polite, wait a second between requests
    
    with open('faculty_data_upenn.json', 'w', encoding='utf-8') as jsonfile:
        json.dump(faculty_data, jsonfile, ensure_ascii=False, indent=4)

    print(f"Scraped {len(faculty_data)} faculty members. Check faculty_data_upenn.json for results.")

if __name__ == "__main__":
    main()