import requests
from bs4 import BeautifulSoup
import json

def scrape_faculty_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    people_links = []
    faculty_table = soup.find('table')
    if faculty_table:
        for row in faculty_table.find_all('tr'):
            link = row.find('a')
            if link and link.get('href'):
                people_links.append(link['href'])
    
    return people_links

def scrape_person_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    data = {}
    
    # Name
    name_elem = soup.find('h1', class_='entry-title')
    data['name'] = name_elem.text.strip() if name_elem else "No name found"
    
    # Position
    position_elem = soup.find('table').find('tr')
    if position_elem:
        data['position'] = position_elem.text.strip().split('\n')[0]
    else:
        data['position'] = "No position found"
    
    # Contact info
    contact_elem = soup.find('table').find('tr')
    if contact_elem:
        contact_info = contact_elem.text.strip().split('\n')
        data['phone'] = next((info for info in contact_info if 'Hall' in info), "No phone found")
        data['email'] = next((info for info in contact_info if '@' in info), "No email found")
    else:
        data['phone'] = "No phone found"
        data['email'] = "No email found"
    
    # CV
    cv_elem = soup.find('a', title='Curriculum Vitae')
    data['cv'] = cv_elem['href'] if cv_elem else "No CV found"
    
    # Specialties (Research Interests)
    specialties_elem = soup.find('h3', string='Research Interests')
    if specialties_elem and specialties_elem.find_next('p'):
        data['specialties'] = specialties_elem.find_next('p').text.strip()
    else:
        data['specialties'] = "No specialties found"
    
    # Education
    education_elem = soup.find('h3', string='Education')
    if education_elem and education_elem.find_next('p'):
        data['education'] = education_elem.find_next('p').text.strip()
    else:
        data['education'] = "No education found"
    
    # Photo
    photo_elem = soup.find('img', class_='attachment-thumbnail')
    data['photo'] = photo_elem['src'] if photo_elem else "No photo found"
    
    # Intro (using Research Interests as intro)
    intro_elem = soup.find('h3', string='Research Interests')
    if intro_elem and intro_elem.find_next('p'):
        data['intro'] = intro_elem.find_next('p').text.strip()
    else:
        data['intro'] = "No intro found"
    
    # Publications
    publications_elem = soup.find('h3', string='Some Notable Publications')
    if publications_elem and publications_elem.find_next('p'):
        data['publications'] = publications_elem.find_next('p').text.strip()
    else:
        data['publications'] = "No publications found"
    
    return data

def main():
    faculty_url = "https://history.unc.edu/faculty/"
    people_links = scrape_faculty_page(faculty_url)
    
    faculty_data = []
    
    for link in people_links:
        try:
            person_data = scrape_person_page(link)
            faculty_data.append(person_data)
            print(f"Scraped data for {person_data['name']}")
        except Exception as e:
            print(f"Error scraping {link}: {str(e)}")
    
    with open('faculty_data_unc.json', 'w', encoding='utf-8') as jsonfile:
        json.dump(faculty_data, jsonfile, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()