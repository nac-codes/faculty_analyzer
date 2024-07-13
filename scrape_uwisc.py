import requests
from bs4 import BeautifulSoup
import json
import time

def scrape_faculty_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    people_links = []
    faculty_list = soup.find('div', class_='faculty-list')
    if faculty_list:
        for member in faculty_list.find_all('div', class_='faculty-member'):
            link = member.find('a', href=True)
            if link:
                people_links.append(link['href'])
    
    return people_links

def scrape_person_page(url):
    response = requests.get(url)
    if response.status_code != 200:
        return {}
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    data = {}
    
    # Name
    name_elem = soup.find('h1', class_='page-title')
    data['name'] = name_elem.text.strip() if name_elem else "No name found"
    
    # Position
    position_elem = soup.find('p', class_='position-title')
    data['position'] = position_elem.text.strip().replace("Position title: ", "") if position_elem else "No position found"
    
    # Email
    email_elem = soup.find('a', href=lambda href: href and href.startswith('mailto:'))
    data['email'] = email_elem.text.strip() if email_elem else "No email found"
    
    # Phone
    phone_elem = soup.find('p', string=lambda text: text and 'Phone:' in text)
    data['phone'] = phone_elem.text.strip().replace("Phone: ", "") if phone_elem else "No phone found"
    
    # CV
    cv_link = soup.find('a', href=lambda href: href and href.endswith('.pdf'))
    data['cv'] = cv_link['href'] if cv_link else "No CV found"
    
    # Education
    education_header = soup.find('h3', string='Education')
    if education_header:
        education_elem = education_header.find_next('p')
        data['education'] = education_elem.text.strip() if education_elem else "No education found"
    else:
        data['education'] = "No education found"
    
    # Photo
    photo_elem = soup.find('div', class_='faculty-headshot')
    if photo_elem:
        img = photo_elem.find('img')
        data['photo'] = img['src'] if img else "No photo found"
    else:
        data['photo'] = "No photo found"
    
    # Biography
    bio_header = soup.find('h3', string='Biography')
    if bio_header:
        bio_elem = bio_header.find_next('p')
        data['intro'] = bio_elem.text.strip() if bio_elem else "No biography found"
    else:
        data['intro'] = "No biography found"
    
    # Publications
    publications_header = soup.find('h3', string='Selected Publications')
    if publications_header:
        publications_list = publications_header.find_next('ul')
        data['publications'] = [li.text.strip() for li in publications_list.find_all('li')] if publications_list else []
    else:
        data['publications'] = []
    
    return data

def main():
    faculty_url = "https://history.wisc.edu/people-main/faculty-listed-alphabetically/"
    people_links = scrape_faculty_page(faculty_url)
    
    faculty_data = []
    
    for link in people_links:
        try:
            person_data = scrape_person_page(link)
            faculty_data.append(person_data)
            print(f"Scraped data for {person_data['name']}")
        except Exception as e:
            print(f"Error scraping {link}: {str(e)}")
            # Optionally, add a placeholder entry for failed scrapes
            faculty_data.append({"name": "Scraping failed", "url": link})
        time.sleep(1)  # Add a 1-second delay between requests
    
    with open('faculty_data_wisconsin.json', 'w', encoding='utf-8') as jsonfile:
        json.dump(faculty_data, jsonfile, ensure_ascii=False, indent=4)

    print(f"Scraped {len(faculty_data)} faculty members. Check faculty_data_wisconsin.json for results.")

if __name__ == "__main__":
    main()
