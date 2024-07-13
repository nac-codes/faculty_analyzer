import requests
from bs4 import BeautifulSoup
import re
import json

def scrape_faculty_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    people_links = []
    for link in soup.find_all('a', href=True):
        if 'people' in link['href']:
            people_links.append(f"https://history.virginia.edu{link['href']}")
    
    return people_links

def scrape_person_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    data = {}
    
    # Name
    name_elem = soup.find('div', class_='views-field-title')
    data['name'] = name_elem.find('h3').text.strip() if name_elem else "No name found"
    
    # Position
    position_elem = soup.find('div', class_='views-field-field-position')
    data['position'] = position_elem.find('h4').text.strip() if position_elem else "No position found"
    
    # Phone
    phone_elem = soup.find('div', class_='views-field-field-phone')
    data['phone'] = phone_elem.text.strip() if phone_elem else "No phone found"
    
    # Email
    email_elem = soup.find('div', class_='views-field-field-email')
    data['email'] = email_elem.find('a')['href'].replace('mailto:', '') if email_elem and email_elem.find('a') else "No email found"
    
    # CV
    cv_elem = soup.find('div', class_='views-field-field-cv')
    data['cv'] = cv_elem.find('a')['href'] if cv_elem and cv_elem.find('a') else "No CV found"
    
    # Specialties
    specialties_elem = soup.find('div', class_='views-field-field-specialties')
    data['specialties'] = specialties_elem.find('p').text.strip() if specialties_elem and specialties_elem.find('p') else "No specialties found"
    
    # Education
    education_elem = soup.find('div', class_='views-field-field-degrees')
    data['education'] = education_elem.find('div', class_='field-content').text.strip() if education_elem else "No education found"
    
    # Photo
    photo_elem = soup.find('div', class_='views-field-field-photo')
    data['photo'] = photo_elem.find('img')['src'] if photo_elem and photo_elem.find('img') else "No photo found"
    
    # Intro
    intro = soup.find('div', class_='views-field-field-intro')
    data['intro'] = intro.find('div', class_='field-content').text.strip() if intro else "No intro found"
    
    # Publications
    publications_div = soup.find('div', class_='views-field-field-publications')
    publications = []
    if publications_div:
        for p in publications_div.find_all('p'):
            # Extract only the title (assuming it's the text before the first opening parenthesis)
            title = re.split(r'\(', p.text)[0].strip()
            if title:
                publications.append(title)
    data['publications'] = '; '.join(publications)
    
    return data



def main():
    faculty_url = "https://history.virginia.edu/faculty"
    people_links = scrape_faculty_page(faculty_url)
    
    faculty_data = []
    
    for link in people_links:
        person_data = scrape_person_page(link)
        faculty_data.append(person_data)
        print(f"Scraped data for {person_data['name']}")
    
    with open('faculty_data_uva.json', 'w', encoding='utf-8') as jsonfile:
        json.dump(faculty_data, jsonfile, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()