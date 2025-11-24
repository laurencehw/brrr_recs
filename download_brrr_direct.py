"""
Direct download of priority BRRR reports from PMG using discovered URL patterns
Focuses on: Energy, Labour, Finance, Sci/Tech, Infrastructure, Trade
"""

import requests
from bs4 import BeautifulSoup
import time
from pathlib import Path
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuration
BASE_URL = "https://pmg.org.za"
BRRR_PAGE = "https://pmg.org.za/page/BRRR"

# Priority sectors with their committee URL keywords
PRIORITY_COMMITTEES = {
    "energy": ["pcmineralenergyreport", "pcenergyreport", "pcmineralreport"],
    "labour": ["pclabourreport", "pcemploymentreport"],
    "finance": ["pcfinancereport"],
    "science_tech": ["pcsciencereport", "pchigherreport"],
    "infrastructure": ["pcpinfrastructurereport", "pcpworksreport", "pcpublicworksreport"],
    "trade": ["pctradereport", "pcdtireport", "pcdticreport"]
}

# Years to download
YEARS = list(range(2015, 2026))

# Output directory
OUTPUT_DIR = Path("brrr_reports")
OUTPUT_DIR.mkdir(exist_ok=True)

def get_committee_sector(url_or_text):
    """Determine which priority sector a URL/text belongs to"""
    text_lower = url_or_text.lower()

    for sector, keywords in PRIORITY_COMMITTEES.items():
        for keyword in keywords:
            if keyword in text_lower:
                return sector

    # Also check text content
    text_checks = {
        "energy": ["electricity and energy", "electricity & energy", "mineral resources and energy",
                   "mineral and energy", "energy affairs"],
        "labour": ["employment and labour", "employment & labour"],
        "finance": ["finance", "standing committee on finance"],
        "science_tech": ["science, technology and innovation", "science/technology/innovation",
                         "higher education, science", "higher education and training"],
        "infrastructure": ["public works and infrastructure", "public works & infrastructure"],
        "trade": ["trade, industry and competition", "trade industry and competition",
                 "trade and industry", "dtic"]
    }

    for sector, terms in text_checks.items():
        for term in terms:
            if term in text_lower:
                return sector

    return None

def download_file(session, url, filepath):
    """Download a file from URL"""
    try:
        # Handle relative URLs
        if not url.startswith('http'):
            if url.startswith('//'):
                url = 'https:' + url
            else:
                url = BASE_URL + url

        # Also try static subdomain
        urls_to_try = [url]
        if 'pmg.org.za/files/' in url and not 'static.pmg.org.za' in url:
            urls_to_try.append(url.replace('pmg.org.za/files/', 'static.pmg.org.za/'))
        elif 'static.pmg.org.za' in url:
            urls_to_try.append(url.replace('static.pmg.org.za/', 'pmg.org.za/files/'))

        for try_url in urls_to_try:
            try:
                print(f"    Trying: {try_url}")
                response = session.get(try_url, timeout=30, allow_redirects=True)

                if response.status_code == 200 and 'application/pdf' in response.headers.get('content-type', ''):
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    print(f"    ✓ Downloaded: {filepath.name} ({len(response.content)} bytes)")
                    return True
            except Exception as e:
                print(f"    ✗ Failed: {str(e)}")
                continue

        print(f"    ✗ Could not download from any URL")
        return False

    except Exception as e:
        print(f"    ✗ Error: {str(e)}")
        return False

def extract_year_reports(session, year):
    """Extract all priority committee reports for a given year"""
    print(f"\n{'='*70}")
    print(f"Processing Year: {year}")
    print(f"{'='*70}")

    try:
        response = session.get(BRRR_PAGE, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')

        downloaded = 0
        found_reports = {}

        # Find all PDF links
        all_links = soup.find_all('a', href=True)

        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)

            # Check if this link is relevant to our year and priority sectors
            if (str(year) in href or str(year)[-2:] in href) and \
               '.pdf' in href.lower():

                sector = get_committee_sector(href + " " + text)

                if sector:
                    # Avoid duplicates
                    report_key = f"{sector}_{year}"
                    if report_key not in found_reports:
                        found_reports[report_key] = {
                            'url': href,
                            'text': text,
                            'sector': sector
                        }

        if found_reports:
            print(f"Found {len(found_reports)} priority sector reports:")

            for report_key, report_info in found_reports.items():
                sector = report_info['sector']
                url = report_info['url']

                # Create sector directory
                sector_dir = OUTPUT_DIR / sector
                sector_dir.mkdir(exist_ok=True)

                # Create filename
                filename = f"{year}_{sector}_BRRR.pdf"
                filepath = sector_dir / filename

                # Skip if already exists
                if filepath.exists():
                    print(f"  [{sector.upper()}] Already exists: {filename}")
                    continue

                print(f"  [{sector.upper()}] Downloading: {filename}")
                if download_file(session, url, filepath):
                    downloaded += 1

                time.sleep(0.5)  # Be respectful

        else:
            print(f"No priority sector reports found for {year}")

        print(f"\n  Downloaded {downloaded} new reports for {year}")
        return downloaded

    except Exception as e:
        print(f"Error processing year {year}: {str(e)}")
        return 0

def main():
    print("="*70)
    print("BRRR Reports Direct Downloader - Priority Economic Sectors")
    print("="*70)
    print(f"Target years: {YEARS[0]}-{YEARS[-1]}")
    print(f"Priority sectors: {', '.join(PRIORITY_COMMITTEES.keys())}")
    print(f"Output directory: {OUTPUT_DIR.absolute()}")
    print("="*70)

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })

    total_downloaded = 0

    for year in YEARS:
        total_downloaded += extract_year_reports(session, year)
        time.sleep(1)

    print("\n" + "="*70)
    print(f"Download Complete! Total new downloads: {total_downloaded}")
    print("="*70)

    # Summary
    print("\nFinal Report Count by Sector:")
    for sector in PRIORITY_COMMITTEES.keys():
        sector_dir = OUTPUT_DIR / sector
        if sector_dir.exists():
            files = list(sector_dir.glob('*.pdf'))
            print(f"  {sector.upper():20s}: {len(files):2d} reports")
        else:
            print(f"  {sector.upper():20s}:  0 reports")

if __name__ == "__main__":
    main()
