import requests
from bs4 import BeautifulSoup
import json
import time
import random
from fake_useragent import UserAgent

def get_random_user_agent():
    ua = UserAgent()
    return ua.random

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://cssh.northeastern.edu/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    return session

def scrape_faculty_page(url, session):
    response = session.get(url)
    if response.status_code == 403:
        print(f"Access forbidden. Response content: {response.text}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    people_links = []
    for item in soup.find_all('li', class_='people-list__list-item'):
        link = item.find('a', class_='people-list__link')
        if link and link.get('href'):
            people_links.append(link['href'])
    
    if not people_links:
        print("No faculty links found")
        # save source to text file
        with open('faculty_page_source_northeastern.txt', 'w', encoding='utf-8') as file:
            file.write(response.text)   
        exit(1)

    return people_links

def scrape_person_page(url, session):
    response = session.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    data = {}
    
    
    # Name
    name_elem = soup.find('h1', class_='person__name')
    if name_elem:
        first_name = name_elem.find('span', class_='person__name-first')
        last_name = name_elem.find('span', class_='person__name-last')
        data['name'] = f"{first_name.text.strip()} {last_name.text.strip()}" if first_name and last_name else "No name found"
    else:
        data['name'] = "No name found"
    
    # Position
    position_elem = soup.find('p', class_='person__intro-title')
    data['position'] = position_elem.text.strip() if position_elem else "No position found"
    
    # Phone (not directly available on the page)
    data['phone'] = "No phone found"
    
    # Email
    email_elem = soup.find('a', href=lambda href: href and href.startswith('mailto:'))
    data['email'] = email_elem['href'].replace('mailto:', '') if email_elem else "No email found"
    
    # CV (not directly available on the page)
    data['cv'] = "No CV found"
    
    # Specialties (using Areas of Interest)
    specialties_elem = soup.find('div', class_='person__accomplishments')
    if specialties_elem:
        specialties = specialties_elem.find_all('div', class_='accordion__content')
        data['specialties'] = '; '.join([s.text.strip() for s in specialties if s.text.strip()])
    else:
        data['specialties'] = "No specialties found"
    
    # Education
    education_elem = soup.find('li', class_='person__list-item')
    if education_elem and education_elem.find('h2', text='Education'):
        data['education'] = education_elem.find('p', class_='person__list-text').text.strip()
    else:
        data['education'] = "No education found"
    
    # Photo
    photo_elem = soup.find('img', class_='lazyload')
    data['photo'] = photo_elem['data-src'] if photo_elem else "No photo found"
    
    # Intro
    intro_elem = soup.find('div', class_='person__intro-bio')
    data['intro'] = intro_elem.text.strip() if intro_elem else "No intro found"
    
    # Publications
    publications_elem = soup.find('div', class_='accordion__content', id='toggle-selected-publications')
    if publications_elem:
        publications = publications_elem.find_all('p')
        data['publications'] = '; '.join([p.text.strip() for p in publications if p.text.strip()])
    else:
        data['publications'] = "No publications found"
    
    return data

def main():
    session = create_session()
    faculty_url = "https://cssh.northeastern.edu/history/people/history-faculty/"
    people_links = scrape_faculty_page(faculty_url, session)
    
    if not people_links:
        print("No faculty links found. Exiting.")
        return
    
    faculty_data = []
    
    for link in people_links:
        person_data = scrape_person_page(link, session)
        faculty_data.append(person_data)
        print(f"Scraped data for {person_data['name']}")
        time.sleep(random.uniform(1, 3))  # Random delay between requests
    
    with open('faculty_data_northeastern.json', 'w', encoding='utf-8') as jsonfile:
        json.dump(faculty_data, jsonfile, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()