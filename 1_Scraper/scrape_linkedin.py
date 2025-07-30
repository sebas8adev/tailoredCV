# FILE: ./1_Scraper/scrape_linkedin.py

import os
import re
import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

# --- Dynamic Path Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OPPORTUNITIES_BASE_DIR = os.path.join(PROJECT_ROOT, '3_Opportunities')
PROCESSED_URLS_FILE = os.path.join(PROJECT_ROOT, 'processed_urls.txt') # --- NEW: Master URL log file
SEARCH_URL = "https://www.linkedin.com/jobs/search/?currentJobId=4274325450&distance=25&f_TPR=r10500&geoId=90000596&keywords=Scrum%20master&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true"

def load_processed_urls():
    """Loads all previously processed URLs from the log file into a set for fast lookups."""
    if not os.path.exists(PROCESSED_URLS_FILE):
        return set() # Return an empty set if the file doesn't exist
    with open(PROCESSED_URLS_FILE, 'r', encoding='utf-8') as f:
        # Read lines and strip any whitespace
        return {line.strip() for line in f if line.strip()}

def log_processed_url(url):
    """Appends a new, successfully processed URL to the log file."""
    with open(PROCESSED_URLS_FILE, 'a', encoding='utf-8') as f:
        f.write(url + '\n')

def scrape_linkedin_jobs(driver):
    """Scrapes job postings from the current page."""
    job_postings = []
    try:
        print("Waiting for job list items to load...")
        job_list_selector = (By.CSS_SELECTOR, 'li.occludable-update')
        WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located(job_list_selector))
        
        num_jobs = len(driver.find_elements(*job_list_selector))
        print(f"Found {num_jobs} job listings.")

        for index in range(num_jobs):
            job_item = driver.find_elements(*job_list_selector)[index]
            print(f"\n--- Processing job {index + 1} of {num_jobs} ---")
            
            try:
                left_panel_title_element = job_item.find_element(By.CSS_SELECTOR, 'a[aria-label]')
                left_panel_title = left_panel_title_element.get_attribute('aria-label').replace(" with verification", "").strip()
                print(f"  > Job on left: '{left_panel_title}'")
                
                driver.execute_script("arguments[0].scrollIntoView(true);", job_item)
                time.sleep(0.5)
                job_item.click()

                right_panel_title_selector = (By.CSS_SELECTOR, "div.job-details-jobs-unified-top-card__job-title > h1")
                WebDriverWait(driver, 15).until(EC.text_to_be_present_in_element(right_panel_title_selector, left_panel_title))
                
                details_panel = driver.find_element(By.CLASS_NAME, "jobs-details__main-content")

                def get_element_text(parent_element, by, value):
                    try: return parent_element.find_element(by, value).text.strip()
                    except NoSuchElementException: return ""

                role_name = get_element_text(details_panel, *right_panel_title_selector)
                company_name = get_element_text(details_panel, By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__company-name a")
                job_description = get_element_text(details_panel, By.ID, "job-details")
                
                raw_location_text = get_element_text(details_panel, By.CLASS_NAME, "job-details-jobs-unified-top-card__tertiary-description-container")
                location = raw_location_text.split('·')[0].strip() if raw_location_text else "Not specified"
                hiring_team = get_element_text(details_panel, By.CSS_SELECTOR, "span.jobs-poster__name") or "Not identified"
                
                application_instructions = "See Job Post URL"
                try:
                    details_panel.find_element(By.CSS_SELECTOR, "button.jobs-apply-button[aria-label*='Apply on company website']")
                    application_instructions = "Apply on company website (button in job post)"
                except NoSuchElementException:
                    try:
                        details_panel.find_element(By.CSS_SELECTOR, "button.jobs-apply-button[aria-label*='Easy Apply']")
                        application_instructions = "LinkedIn Easy Apply"
                    except NoSuchElementException:
                        if emails := re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', job_description):
                            application_instructions = f"Apply by emailing: {', '.join(emails)}"
                
                desc_lower = job_description.lower()
                job_type = 'Remote' if 'remote' in desc_lower else 'On-site' if 'on-site' in desc_lower or 'onsite' in desc_lower else 'Hybrid' if 'hybrid' in desc_lower else 'Not specified'
                salary_range = "Not specified"
                if salaries := re.findall(r'\$[0-9,.]+[Kk]?\s*[-–to]+\s*\$[0-9,.]+[Kk]?', job_description): salary_range = salaries[0]

                job_info = {
                    "job_board": "LinkedIn", "company_name": company_name, "role_name": role_name,
                    "location": location, "type": job_type, "salary_range": salary_range,
                    "hiring_team": hiring_team, "application_instructions": application_instructions,
                    "job_post_url": driver.current_url, "job_description": job_description
                }
                job_postings.append(job_info)
                print(f"  > SUCCESS: Scraped '{role_name}' at '{company_name}'")

            except Exception as e:
                print(f"  > An unexpected error occurred while scraping: {e}. Skipping.")
                continue
    except TimeoutException:
        print("\nFATAL: The main job list did not load. The primary script selector is likely wrong.")
    return job_postings

def create_opportunity_folder(job_data):
    """Creates the folder and the detailed jobdescription.txt file."""
    sanitized_company = "".join(c for c in job_data.get('company_name', 'Unknown_Company') if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
    sanitized_role = "".join(c for c in job_data.get('role_name', 'Unknown_Role') if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    folder_name = f"{sanitized_company}_{sanitized_role}_{date_str}"
    folder_path = os.path.join(OPPORTUNITIES_BASE_DIR, folder_name)

    # Secondary check to prevent folder collision, though the URL check is primary.
    if os.path.exists(folder_path): return None
    try:
        os.makedirs(folder_path)
        job_desc_path = os.path.join(folder_path, "jobdescription.txt")
        with open(job_desc_path, 'w', encoding='utf-8') as f:
            f.write("Status: pending\n")
            f.write("Data-Status: pending\n")
            f.write(f"Job board: {job_data.get('job_board', 'N/A')}\n")
            f.write(f"Company Name: {job_data.get('company_name', 'N/A')}\n")
            f.write(f"Role Name: {job_data.get('role_name', 'N/A')}\n")
            f.write(f"Location: {job_data.get('location', 'N/A')}\n")
            f.write(f"Type: {job_data.get('type', 'N/A')}\n")
            f.write(f"Salary range: {job_data.get('salary_range', 'N/A')}\n")
            f.write(f"Hiring Team: {job_data.get('hiring_team', 'N/A')}\n")
            f.write(f"Application Instructions: {job_data.get('application_instructions', 'N/A')}\n")
            f.write(f"Job post URL: {job_data.get('job_post_url', 'N/A')}\n\n")
            f.write(f"Job Description:\n{job_data.get('job_description', 'N/A')}\n")
        return folder_path
    except OSError as e:
        print(f"  > Error creating directory {folder_path}: {e}")
        return None

def main():
    """Main function to run the scraper and create opportunity folders."""
    print("--- Phase 1: LinkedIn Job Scraper ---")
    
    if not os.path.exists(OPPORTUNITIES_BASE_DIR):
        os.makedirs(OPPORTUNITIES_BASE_DIR)
        
    # --- NEW: Load already processed URLs ---
    processed_urls = load_processed_urls()
    print(f"Loaded {len(processed_urls)} previously processed URLs.")
    
    # --- Connect to browser ---
    print("Connecting to the existing Chrome browser on port 9222...")
    try:
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=chrome_options)
        print("Successfully connected to the browser.")
        driver.get(SEARCH_URL)
    except Exception as e:
        print(f"FATAL: Could not connect to Chrome. Is it running with --remote-debugging-port=9222? Error: {e}")
        return

    # --- Scrape and process ---
    scraped_jobs = scrape_linkedin_jobs(driver)
    
    if not scraped_jobs:
        print("No jobs were scraped from the page.")
    
    new_opportunities_count = 0
    for job in scraped_jobs:
        job_url = job.get('job_post_url', '').split('&')[0] # Get base URL without tracking params

        # --- THE NEW DUPLICATE CHECK ---
        if job_url in processed_urls:
            print(f"  -> INFO: Skipping duplicate job (URL already processed): {job.get('role_name', 'N/A')}")
            continue

        folder_path = create_opportunity_folder(job)
        if folder_path:
            print(f"  -> SUCCESS: Created new opportunity folder at: {folder_path}")
            new_opportunities_count += 1
            # --- NEW: Log the URL so we don't process it again ---
            log_processed_url(job_url)
            processed_urls.add(job_url) # Add to the in-memory set as well
        else:
            print(f"  -> INFO: Skipping opportunity (folder may already exist for today): {job.get('role_name', 'N/A')}")
            
    print(f"\nScraping complete. Found and created {new_opportunities_count} new opportunities.")
    print("Script finished. Browser connection released.")

if __name__ == '__main__':
    main()