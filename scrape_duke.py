import requests
from bs4 import BeautifulSoup
import json
import time

def scrape_faculty_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    people_links = []
    faculty_list = soup.find_all('article')
    for item in faculty_list:
        link = item.find('a')
        if link and link.get('href'):
            people_links.append(link['href'])
    
    return people_links

def scrape_person_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    data = {}
    
    # Name and CV
    name_elem = soup.find('h1', class_='w-full')
    if name_elem:
        name_span = name_elem.find('span', class_='pr-3')
        data['name'] = name_span.text.strip() if name_span else "No name found"
        
        cv_link = name_elem.find('a', title="Curriculum vitae")
        if cv_link:
            data['cv'] = cv_link['href']
        else:
            data['cv'] = "No CV found"
    else:
        data['name'] = "No name found"
        data['cv'] = "No CV found"
    
    # Position
    position_elem = soup.find('div', class_='sub-h1')
    data['position'] = position_elem.text.strip() if position_elem else "No position found"
    
    # Email
    email_elem = soup.find('a', href=lambda href: href and href.startswith('mailto:'))
    data['email'] = email_elem.text.strip() if email_elem else "No email found"
    
    # Phone (not directly available on the page)
    data['phone'] = "No phone found"
    
    # Office
    office_elem = soup.find('span', class_='prof-contact-info', string=lambda text: 'Drive' in text if text else False)
    data['office'] = office_elem.text.strip() if office_elem else "No office found"
    
    # Specialties
    specialties_elem = soup.find('div', class_='field-specialties-and-regions')
    data['specialties'] = specialties_elem.text.strip() if specialties_elem else "No specialties found"
    
    # Education
    education_elem = soup.find('div', class_='field-education')
    data['education'] = education_elem.text.strip() if education_elem else "No education found"
    
    # Photo
    photo_elem = soup.find('img', class_='img')
    data['photo'] = photo_elem['src'] if photo_elem else "No photo found"
    
    # Intro
    intro_elem = soup.find('div', class_='excerpt')
    data['intro'] = intro_elem.text.strip() if intro_elem else "No intro found"
    
    # Publications (not directly available on the page)
    data['publications'] = "No publications information found"
    
    return data

def main():
    faculty_url = "https://history.duke.edu/people/appointed-faculty/primary-faculty"
    people_links = scrape_faculty_page(faculty_url)
    
    faculty_data = []
    
    for link in people_links:
        try:
            person_data = scrape_person_page(link)
            faculty_data.append(person_data)
            print(f"Scraped data for {person_data['name']}")
        except Exception as e:
            print(f"Error scraping {link}: {str(e)}")
        time.sleep(1)  # Add a 1-second delay between requests
    
    with open('faculty_data_duke.json', 'w', encoding='utf-8') as jsonfile:
        json.dump(faculty_data, jsonfile, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()