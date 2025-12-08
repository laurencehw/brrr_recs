"""
Download 2025 MTBPS documents from National Treasury
"""

import requests
from pathlib import Path
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "https://www.treasury.gov.za/documents/mtbps/2025/"
OUTPUT_DIR = Path("mtbps_2025")
OUTPUT_DIR.mkdir(exist_ok=True)

DOCUMENTS = {
    "Full_MTBPS.pdf": "mtbps/FullMTBPS.pdf",
    "Full_AENE.pdf": "aene/FullAENE.pdf",
    "Ministers_Speech.pdf": "speech/speech.pdf",
    "MTBPS_Presentation.pdf": "2025 MTBPS presentation.pdf",
}

def download_file(url, filename):
    """Download a file from URL"""
    try:
        print(f"Downloading: {filename}")
        response = requests.get(url, timeout=60)

        if response.status_code == 200:
            filepath = OUTPUT_DIR / filename
            with open(filepath, 'wb') as f:
                f.write(response.content)
            size_mb = len(response.content) / (1024 * 1024)
            print(f"  ✓ Saved: {filename} ({size_mb:.1f} MB)")
            return True
        else:
            print(f"  ✗ Failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False

def main():
    print("="*70)
    print("Downloading 2025 MTBPS Documents")
    print("="*70)

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })

    success_count = 0

    for filename, path in DOCUMENTS.items():
        url = BASE_URL + path
        if download_file(url, filename):
            success_count += 1
        print()

    print("="*70)
    print(f"Download complete: {success_count}/{len(DOCUMENTS)} files downloaded")
    print(f"Saved to: {OUTPUT_DIR.absolute()}")
    print("="*70)

if __name__ == "__main__":
    main()
