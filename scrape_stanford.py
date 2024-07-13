import requests
from bs4 import BeautifulSoup
import sys
import json


def scrape_faculty_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        faculty_links = []
        faculty_cards = soup.find_all('div', class_='hb-card__content')
        
        for card in faculty_cards:
            link = card.find('a', href=True)
            if link and '/people/' in link['href']:
                faculty_links.append(f"https://history.stanford.edu{link['href']}")
        
        return faculty_links
    except requests.RequestException as e:
        print(f"Warning: Error fetching faculty page: {e}", file=sys.stderr)
        return []

def scrape_person_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        data = {}
        
        # Name
        name_elem = soup.find('div', class_='title')
        data['name'] = name_elem.find('h1').text.strip() if name_elem and name_elem.find('h1') else "No name found"
        
        # Position
        position_elem = soup.find('div', class_='field-hs-person-title')
        data['position'] = position_elem.text.strip() if position_elem else "No position found"
        
        # Phone
        phone_elem = soup.find('div', class_='field-hs-person-telephone')
        data['phone'] = phone_elem.find('div', class_='field-item').text.strip() if phone_elem and phone_elem.find('div', class_='field-item') else "No phone found"
        
        # Email
        email_elem = soup.find('div', class_='field-hs-person-email')
        data['email'] = email_elem.find('div', class_='field-item').text.strip() if email_elem and email_elem.find('div', class_='field-item') else "No email found"
        
        # CV
        cv_elem = soup.find('div', class_='field-hs-person-cv-link')
        data['cv'] = cv_elem.find('a')['href'] if cv_elem and cv_elem.find('a') else "No CV found"
        
        # Fields (Research)
        fields_elem = soup.find('div', class_='field-hs-person-research')
        fields_string = ""
        if fields_elem:
            fields = [a.text.strip() for a in fields_elem.find_all('a')]
            fields_string = '; '.join(fields) if fields else "No fields found"
        else:
            fields_string = "No fields found"
        
        # Subfields
        subfields_elem = soup.find('div', class_='hb-categories custm-subfield')
        subfields_string = ""
        if subfields_elem:
            subfields = [div.text.strip() for div in subfields_elem.find_all('div') if not div.has_attr('class')]
            subfields_string = '; '.join(subfields) if subfields else "No subfields found"
        else:
            subfields_string = "No subfields found"
        
        data['specialties'] = fields_string + '; ' + subfields_string

        # Education
        education_elem = soup.find('div', class_='field-hs-person-education')
        data['education'] = '; '.join([div.text.strip() for div in education_elem.find_all('div')]) if education_elem else "No education found"
        
        # Photo
        photo_elem = soup.find('div', class_='field-hs-person-image')
        data['photo'] = photo_elem.find('img')['src'] if photo_elem and photo_elem.find('img') else "No photo found"
        
        # Bio
        bio_elem = soup.find('div', class_='body')
        data['intro'] = bio_elem.text.strip() if bio_elem else "No bio found"
        
        # Publications
        publications = []
        books_elem = soup.find('div', class_='views-element-container', id=lambda x: x and x.startswith('block-views-block-hs-publications-block'))
        if books_elem:
            for book in books_elem.find_all('h2', class_='field-content'):
                publications.append(book.text.strip())
        data['publications'] = '; '.join(publications)
        
        return data
    except requests.RequestException as e:
        print(f"Warning: Error fetching person page {url}: {e}", file=sys.stderr)
        return None



def main():
    faculty_url = "https://history.stanford.edu/people/faculty"
    people_links = scrape_faculty_page(faculty_url)
    
    if not people_links:
        print("Error: No faculty links found. Exiting.", file=sys.stderr)
        return
    
    faculty_data = []
    
    for link in people_links:
        person_data = scrape_person_page(link)
        if person_data:
            faculty_data.append(person_data)
            print(f"Scraped data for {person_data['name']}")
        else:
            print(f"Warning: Failed to scrape data for {link}", file=sys.stderr)
    
    with open('faculty_data_stanford.json', 'w', encoding='utf-8') as jsonfile:
        json.dump(faculty_data, jsonfile, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()