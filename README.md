# Faculty Data Scraping and Analysis Project

## Overview
This project consists of tools for scraping faculty data from university history department websites and analyzing faculty profiles based on their research interests and publications. The main components include:

1. Web scraping scripts to collect faculty information
2. Structured data storage in JSON format
3. Faculty profile analysis capabilities

## Web Scraping Component
The project includes a Python scraper for each deparment page (see `scrape_uva.py` as an exam,ple) that extracts detailed faculty information including:

- Name and position
- Contact information (email, phone)
- Educational background
- Research interests and introductions
- Publications
- CV links and photos


```6:69:scrape_uva.py
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
    
```


## Data Structure
Faculty data is stored in JSON format with a consistent schema. Each faculty member's record includes:

```json
{
  "name": "String",
  "position": "String",
  "email": "String",
  "phone": "String",
  "cv": "URL String",
  "education": "String",
  "photo": "URL String",
  "intro": "String",
  "publications": ["Array of Strings"]
}
```

## Key Features

### Web Scraping
- Automated collection of faculty data from department websites
- Handles multiple page types and data formats
- Error handling for missing or incomplete data
- Consistent data formatting and cleaning

### Data Processing
- Standardized JSON output format
- Structured storage of faculty information
- Support for multiple institutions (currently includes UVA and Wisconsin)

## Usage

### Running the Scraper
```python
python scrape_uva.py
```

The script will:
1. Fetch faculty listing pages
2. Extract individual faculty profile URLs
3. Scrape detailed information from each profile
4. Save the collected data to a JSON file

## Data Files
- `faculty_data_uva.json`: University of Virginia faculty data
- `faculty_data_wisconsin.json`: University of Wisconsin faculty data

## Future Enhancements
- Add support for more universities
- Implement embedding-based similarity analysis
- Create visualization tools for faculty research networks
- Add automated updates and data validation

## Requirements
- Python 3.x
- BeautifulSoup4
- Requests
- JSON

## License
This project is licensed under the MIT License - see the LICENSE file for details.
