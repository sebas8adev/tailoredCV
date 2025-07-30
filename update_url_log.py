# FILE: ./update_url_log.py

import os

# --- Configuration ---
# This script is designed to be run from the project's root directory.
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
OPPORTUNITIES_BASE_DIR = os.path.join(PROJECT_ROOT, '3_Opportunities')
PROCESSED_URLS_FILE = os.path.join(PROJECT_ROOT, 'processed_urls.txt')

def update_processed_urls_from_existing_folders():
    """
    Scans all existing opportunity folders, extracts the job URLs from
    jobdescription.txt, and updates the master processed_urls.txt file.
    """
    print("--- Starting URL Log Update Utility ---")

    # --- Step 1: Load URLs that are already in the log file ---
    existing_urls = set()
    if os.path.exists(PROCESSED_URLS_FILE):
        with open(PROCESSED_URLS_FILE, 'r', encoding='utf-8') as f:
            existing_urls = {line.strip() for line in f if line.strip()}
        print(f"Found {len(existing_urls)} URLs already in '{os.path.basename(PROCESSED_URLS_FILE)}'.")
    else:
        print(f"'{os.path.basename(PROCESSED_URLS_FILE)}' not found. A new one will be created.")

    # --- Step 2: Scan all existing opportunity folders ---
    found_urls = set()
    if not os.path.isdir(OPPORTUNITIES_BASE_DIR):
        print(f"ERROR: Opportunities directory not found at '{OPPORTUNITIES_BASE_DIR}'.")
        return

    print(f"Scanning folders in '{OPPORTUNITIES_BASE_DIR}'...")
    for folder_name in sorted(os.listdir(OPPORTUNITIES_BASE_DIR)):
        opportunity_path = os.path.join(OPPORTUNITIES_BASE_DIR, folder_name)
        
        if os.path.isdir(opportunity_path):
            job_desc_path = os.path.join(opportunity_path, 'jobdescription.txt')
            if os.path.exists(job_desc_path):
                try:
                    with open(job_desc_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            # Find the URL line, ignore case and whitespace
                            if line.strip().lower().startswith('job post url:'):
                                url = line.split(':', 1)[1].strip()
                                if url:
                                    # Get base URL without tracking params for better de-duplication
                                    base_url = url.split('&')[0]
                                    found_urls.add(base_url)
                                    print(f"  > Found URL in: {folder_name}")
                                break # Move to the next folder once URL is found
                except Exception as e:
                    print(f"  > Could not read file in {folder_name}: {e}")

    print(f"\nScanned all folders. Found {len(found_urls)} unique URLs in job description files.")

    # --- Step 3: Combine and write the final list ---
    final_urls = existing_urls.union(found_urls)
    
    print(f"Total unique URLs to be saved: {len(final_urls)}")
    
    try:
        with open(PROCESSED_URLS_FILE, 'w', encoding='utf-8') as f:
            for url in sorted(list(final_urls)): # Sort for consistency
                f.write(url + '\n')
        print(f"SUCCESS: '{os.path.basename(PROCESSED_URLS_FILE)}' has been updated with all found URLs.")
    except Exception as e:
        print(f"ERROR: Could not write to file: {e}")

if __name__ == '__main__':
    update_processed_urls_from_existing_folders()