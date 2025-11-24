"""
Download Budget Review and Recommendation Reports (BRRR) from PMG website
Focuses on key economic sectors: Energy, Labour, Finance, Sci/Tech, Infrastructure, Trade
"""

import requests
from bs4 import BeautifulSoup
import os
import time
from pathlib import Path
import re
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuration
USERNAME = "laurencew@uj.ac.za"
PASSWORD = "Maggie2025**!!"
BASE_URL = "https://pmg.org.za"
BRRR_PAGE = "https://pmg.org.za/page/BRRR"

# Priority sectors (with variations to handle name changes over time)
PRIORITY_SECTORS = {
    "energy": ["electricity and energy", "electricity & energy", "energy",
               "mineral resources and energy", "mineral and energy affairs"],
    "labour": ["employment and labour", "employment & labour", "labour"],
    "finance": ["finance", "treasury", "national treasury"],
    "science_tech": ["science and technology", "science, technology and innovation",
                     "science/technology/innovation", "science technology innovation",
                     "higher education and training", "higher education science",
                     "higher education, science and innovation"],
    "infrastructure": ["public works and infrastructure", "public works & infrastructure",
                      "public works", "infrastructure development"],
    "trade": ["trade and industry", "trade, industry and competition",
              "trade industry and competition", "trade & industry", "dti", "dtic",
              "economic development"]
}

# Years to download (last 10 years)
YEARS = list(range(2015, 2026))

# Output directory
OUTPUT_DIR = Path("brrr_reports")
OUTPUT_DIR.mkdir(exist_ok=True)

def create_session():
    """Create and authenticate session with PMG website"""
    session = requests.Session()

    # Try to find login page
    print("Attempting to authenticate with PMG website...")

    # First, get the login page to find the login form
    response = session.get("https://pmg.org.za/login/")

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the login form
        login_form = soup.find('form')
        if login_form:
            # Prepare login data
            login_data = {
                'username': USERNAME,
                'password': PASSWORD,
            }

            # Check for CSRF token
            csrf_token = soup.find('input', {'name': 'csrf_token'})
            if csrf_token:
                login_data['csrf_token'] = csrf_token.get('value')

            # Submit login
            login_url = login_form.get('action', '/login/')
            if not login_url.startswith('http'):
                login_url = BASE_URL + login_url

            login_response = session.post(login_url, data=login_data)

            if login_response.status_code == 200:
                print("✓ Authentication successful")
                return session
            else:
                print(f"✗ Login failed with status code: {login_response.status_code}")

    print("Note: Proceeding without authentication (some reports may require login)")
    return session

def matches_priority_sector(title, url):
    """Check if report matches any priority sector"""
    title_lower = title.lower()
    url_lower = url.lower()
    text = f"{title_lower} {url_lower}"

    for sector, variations in PRIORITY_SECTORS.items():
        for variation in variations:
            if variation in text:
                return sector
    return None

def download_report(session, url, filename, sector, year):
    """Download a single report"""
    try:
        if not url.startswith('http'):
            url = BASE_URL + url

        print(f"  Downloading: {filename}")
        response = session.get(url, timeout=30)

        if response.status_code == 200:
            # Create sector directory
            sector_dir = OUTPUT_DIR / sector
            sector_dir.mkdir(exist_ok=True)

            # Save file
            filepath = sector_dir / f"{year}_{filename}"

            # Determine file extension from content-type or URL
            content_type = response.headers.get('content-type', '')
            if 'pdf' in content_type or url.endswith('.pdf'):
                if not filepath.suffix == '.pdf':
                    filepath = filepath.with_suffix('.pdf')

            with open(filepath, 'wb') as f:
                f.write(response.content)

            print(f"    ✓ Saved to: {filepath}")
            return True
        else:
            print(f"    ✗ Failed (status {response.status_code})")
            return False
    except Exception as e:
        print(f"    ✗ Error: {str(e)}")
        return False

def find_year_section_links(session, year):
    """Find links to year-specific BRRR pages"""
    try:
        response = session.get(BRRR_PAGE, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Look for headings or sections for this year
        year_links = []

        # Find all headings that mention the year
        for heading in soup.find_all(['h2', 'h3', 'h4']):
            if str(year) in heading.get_text():
                # Find all links following this heading until next heading
                current = heading.find_next()
                while current and current.name not in ['h2', 'h3', 'h4']:
                    if current.name == 'a' and current.get('href'):
                        href = current.get('href')
                        text = current.get_text(strip=True)

                        # Check if it's a PDF or committee meeting link
                        if '.pdf' in href.lower() or '/files/' in href or '/committee-meeting/' in href:
                            sector = matches_priority_sector(text, href)
                            if sector:
                                year_links.append({
                                    'url': href,
                                    'title': text,
                                    'sector': sector
                                })

                    # Also check for links within list items
                    if current.name in ['ul', 'ol', 'li']:
                        for link in current.find_all('a', href=True):
                            href = link.get('href')
                            text = link.get_text(strip=True)

                            if '.pdf' in href.lower() or '/files/' in href or '/committee-meeting/' in href:
                                sector = matches_priority_sector(text, href)
                                if sector:
                                    year_links.append({
                                        'url': href,
                                        'title': text,
                                        'sector': sector
                                    })

                    current = current.find_next()

        return year_links
    except Exception as e:
        print(f"Error finding links for {year}: {str(e)}")
        return []

def extract_report_links(session, year):
    """Extract report links for a specific year from BRRR page"""
    print(f"\n{'='*60}")
    print(f"Processing year: {year}")
    print(f"{'='*60}")

    try:
        # Find all report links for this year
        found_reports = find_year_section_links(session, year)

        # Also do a broad search across the entire page
        response = session.get(BRRR_PAGE, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')

        all_links = soup.find_all('a', href=True)

        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)

            # Look for PDFs or committee pages that mention the year
            if (str(year) in href or str(year) in text) and \
               ('.pdf' in href.lower() or '/files/' in href or '/committee-meeting/' in href):
                sector = matches_priority_sector(text, href)
                if sector:
                    # Check if not already in list
                    if not any(r['url'] == href for r in found_reports):
                        found_reports.append({
                            'url': href,
                            'title': text,
                            'sector': sector,
                            'year': year
                        })

        if found_reports:
            print(f"Found {len(found_reports)} priority sector reports for {year}")

            # Remove duplicates
            seen_urls = set()
            unique_reports = []
            for report in found_reports:
                if report['url'] not in seen_urls:
                    seen_urls.add(report['url'])
                    unique_reports.append(report)

            for report in unique_reports:
                # Create safe filename
                safe_title = re.sub(r'[^\w\s-]', '', report['title'])
                safe_title = re.sub(r'[-\s]+', '_', safe_title)
                safe_title = safe_title[:100]  # Limit length

                # If title is empty or too short, use sector name
                if len(safe_title) < 5:
                    safe_title = f"{report['sector']}_report"

                filename = f"{safe_title}.pdf"

                download_report(session, report['url'], filename,
                              report['sector'], report['year'])
                time.sleep(1)  # Be respectful to the server
        else:
            print(f"No priority sector reports found for {year}")

    except Exception as e:
        print(f"Error processing year {year}: {str(e)}")

def main():
    print("="*60)
    print("BRRR Report Downloader - Priority Economic Sectors")
    print("="*60)
    print(f"Target years: {YEARS[0]}-{YEARS[-1]}")
    print(f"Priority sectors: {', '.join(PRIORITY_SECTORS.keys())}")
    print(f"Output directory: {OUTPUT_DIR.absolute()}")
    print("="*60)

    # Create authenticated session
    session = create_session()

    # Process each year
    for year in YEARS:
        extract_report_links(session, year)
        time.sleep(2)  # Pause between years

    print("\n" + "="*60)
    print("Download complete!")
    print(f"Reports saved to: {OUTPUT_DIR.absolute()}")
    print("="*60)

    # Summary
    print("\nDirectory structure:")
    for sector in PRIORITY_SECTORS.keys():
        sector_dir = OUTPUT_DIR / sector
        if sector_dir.exists():
            files = list(sector_dir.glob('*'))
            print(f"  {sector}: {len(files)} files")

if __name__ == "__main__":
    main()
