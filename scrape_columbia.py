import requests
from bs4 import BeautifulSoup
import json

def scrape_faculty_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    people_links = []
    for li in soup.find_all('li', class_='cmed_list_view_item'):
        link = li.find('a', href=True)
        if link:
            people_links.append(link['href'])
    
    return people_links

def scrape_person_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    data = {}
    
    # Name
    name_elem = soup.find('h1', class_='expert-title')
    data['name'] = name_elem.text.strip() if name_elem else "No name found"
    
    # Position
    position_elem = soup.find('div', class_='cmed_position')
    data['position'] = position_elem.text.strip() if position_elem else "No position found"
    
    # Phone
    phone_elem = soup.find('div', class_='cmed-info-box-phone')
    data['phone'] = phone_elem.text.strip() if phone_elem else "No phone found"
    
    # Email
    email_elem = soup.find('a', class_='cmed-info-box-link')
    data['email'] = email_elem['href'].replace('mailto:', '') if email_elem else "No email found"
    
    # CV (not available on this site)
    data['cv'] = "No CV found"
    
    # Specialties (not directly available, using Interests and Research instead)
    interests_elem = soup.find('h2', string='Interests and Research')
    if interests_elem:
        specialties = interests_elem.find_next('p')
        data['specialties'] = specialties.text.strip() if specialties else "No specialties found"
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
    photo_elem = soup.find('img', class_='attachment-cmed_image_big')
    data['photo'] = photo_elem['src'] if photo_elem else "No photo found"


    
    # Intro (not directly available, using first paragraph of Interests and Research)
    intro = soup.find('div', class_='cmed_content_box')
    if intro:
        # find all spans and concatenate
        intro = intro.find_all('span')
        intro = ' '.join([i.text.strip() for i in intro])
        data['intro'] = intro.strip() if intro else "No intro found"
    else:
        data['intro'] = "No intro found"
        
    
    # Publications
    publications_elem = soup.find('p', string=lambda text: text and text.startswith("Besides a variety of articles"))
    if publications_elem:
        publications = publications_elem.find_next_siblings('p')
        data['publications'] = [p.text.strip() for p in publications]
    else:
        data['publications'] = []
    
    return data

def main():
    faculty_url = "https://history.columbia.edu/faculty-main/columbia-history/"
    people_links = scrape_faculty_page(faculty_url)
    
    faculty_data = []
    
    for link in people_links:
        person_data = scrape_person_page(link)
        faculty_data.append(person_data)
        print(f"Scraped data for {person_data['name']}")
    
    with open('faculty_data_columbia.json', 'w', encoding='utf-8') as jsonfile:
        json.dump(faculty_data, jsonfile, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()