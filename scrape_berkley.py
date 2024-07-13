import requests
from bs4 import BeautifulSoup
import json

def scrape_faculty_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    people_links = []
    faculty_list = soup.find('div', class_='field-name-field-openberkeley-widgets-thumb')
    if faculty_list:
        for item in faculty_list.find_all('div', class_='field-item'):
            link = item.find('a', class_='openberkeley-widgets-thumbnail-link')
            if link and link.get('href'):
                # Use urljoin to correctly handle relative URLs
                full_url = requests.compat.urljoin(url, link['href'])
                people_links.append(full_url)
    
    return people_links

def scrape_person_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    data = {}
    
    # Name
    name_elem = soup.find('h1', class_='title')
    data['name'] = name_elem.text.strip() if name_elem else "No name found"
    
    # Position
    position_elem = soup.find('h2')
    data['position'] = position_elem.text.strip() if position_elem else "No position found"
    
    # Phone (not directly available on the page)
    data['phone'] = "No phone found"
    
    # Email
    email_elem = soup.find('a', href=lambda href: href and href.startswith('mailto:'))
    data['email'] = email_elem['href'].replace('mailto:', '') if email_elem else "No email found"
    
    # CV (not directly available on the page)
    data['cv'] = "No CV found"
    
    # Specialties
    specialties_elem = soup.find('h3', string='Research Interests')
    if specialties_elem:
        specialties = specialties_elem.find_next('ul').find_all('li')
        data['specialties'] = '; '.join([s.text.strip() for s in specialties])
    else:
        data['specialties'] = "No specialties found"
    
    # Education
    education_elem = soup.find('h3', string='Education')
    if education_elem:
        education = education_elem.find_next('p')
        data['education'] = education.text.strip() if education else "No education found"
    else:
        data['education'] = "No education found"
    
    # Photo
    photo_elem = soup.find('img', class_='openberkeley-image-full')
    data['photo'] = 'https://history.berkeley.edu' + photo_elem['src'] if photo_elem else "No photo found"
    
    # Intro
    intro_elem = soup.find('div', class_='field-name-body')
    if intro_elem:
        paragraphs = intro_elem.find_all('p')
        data['intro'] = ' '.join([p.text.strip() for p in paragraphs])
    else:
        data['intro'] = "No intro found"
    
    # Publications (not directly available on the page)
    data['publications'] = "No publications found"
    
    return data

def main():
    faculty_url = "https://history.berkeley.edu/people/faculty"
    people_links = scrape_faculty_page(faculty_url)
    
    faculty_data = []
    
    for link in people_links:
        person_data = scrape_person_page(link)
        faculty_data.append(person_data)
        print(f"Scraped data for {person_data['name']}")
    
    with open('faculty_data_berkeley.json', 'w', encoding='utf-8') as jsonfile:
        json.dump(faculty_data, jsonfile, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()