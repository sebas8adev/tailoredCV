import os
import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options # Import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- Configuration ---
SEARCH_URL = "https://www.linkedin.com/jobs/search/?currentJobId=4273237463&distance=25&f_TPR=r1800&geoId=105142029&keywords=it%20project%20manager&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&refresh=true"
OPPORTUNITIES_BASE_DIR = "../3_Opportunities"

def scrape_linkedin_jobs():
    """
    Connects to an existing Chrome instance to scrape job postings.
    """
    print("Connecting to the existing Chrome browser on port 9222...")
    
    # --- MODIFICATION START ---
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    # Pass the options when creating the driver instance
    driver = webdriver.Chrome(options=chrome_options)
    # --- MODIFICATION END ---

    print("Successfully connected to the browser.")
    
    # Navigate to the search URL in the existing browser window
    driver.get(SEARCH_URL)

    # The rest of the script remains largely the same, but we remove the manual login pause.
    job_postings = []
    
    try:
        print("Waiting for job list to load...")
        job_list_items = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.jobs-search__results-list > li"))
        )
        print(f"Found {len(job_list_items)} job listings.")

        for index, job_item in enumerate(job_list_items):
            print(f"\n--- Processing job {index + 1} of {len(job_list_items)} ---")
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", job_item)
                time.sleep(1)
                job_item.click()
                time.sleep(2)

                details_panel = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "jobs-search__job-details-container-content"))
                )

                def get_element_text(element, by, value):
                    try:
                        return element.find_element(by, value).text.strip()
                    except NoSuchElementException:
                        return "Not found"

                company_name = get_element_text(details_panel, By.CSS_SELECTOR, ".jobs-unified-top-card__company-name")
                role_name = get_element_text(details_panel, By.CSS_SELECTOR, ".jobs-unified-top-card__job-title")
                location = get_element_text(details_panel, By.CSS_SELECTOR, ".jobs-unified-top-card__bullet")
                job_description = get_element_text(details_panel, By.CLASS_NAME, "jobs-box__html-content")
                
                job_info = {
                    "job_board": "LinkedIn",
                    "company_name": company_name,
                    "role_name": role_name,
                    "location": location,
                    "type": "On-site/Remote/Hybrid (check description)",
                    "salary_range": "Not specified (check description)",
                    "hiring_team": "Not identified",
                    "job_post_url": driver.current_url,
                    "job_description": job_description
                }
                job_postings.append(job_info)
                print(f"  > Scraped: {role_name} at {company_name}")

            except (TimeoutException, NoSuchElementException) as e:
                print(f"  > Could not process a job posting, skipping. Error: {e}")
                continue

    finally:
        # We don't call driver.quit() because we don't want to close our manual browser window.
        # The script will simply disconnect.
        print("\nScript finished. Browser connection released.")

    return job_postings

# The create_opportunity_folder and main functions remain exactly the same as before.
def create_opportunity_folder(job_data):
    sanitized_company = "".join(c for c in job_data['company_name'] if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
    sanitized_role = "".join(c for c in job_data['role_name'] if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    folder_name = f"{sanitized_company}_{sanitized_role}_{date_str}"
    folder_path = os.path.join(OPPORTUNITIES_BASE_DIR, folder_name)

    if os.path.exists(folder_path):
        return None

    try:
        os.makedirs(folder_path)
        job_desc_path = os.path.join(folder_path, "job_description.txt")
        with open(job_desc_path, 'w', encoding='utf-8') as f:
            f.write("Status: pending\n")
            f.write(f"Job board: {job_data['job_board']}\n")
            f.write(f"Company Name: {job_data['company_name']}\n")
            f.write(f"Role Name: {job_data['role_name']}\n")
            f.write(f"Location: {job_data['location']}\n")
            f.write(f"Type: {job_data['type']}\n")
            f.write(f"Salary range: {job_data['salary_range']}\n")
            f.write(f"Hiring Team: {job_data['hiring_team']}\n")
            f.write(f"Job post URL: {job_data['job_post_url']}\n\n")
            f.write(f"Job Description:\n{job_data['job_description']}\n")
        return folder_path
    except OSError as e:
        print(f"  > Error creating directory {folder_path}: {e}")
        return None

def main():
    print("--- Phase 1: LinkedIn Job Scraper ---")
    if not os.path.exists(OPPORTUNITIES_BASE_DIR):
        os.makedirs(OPPORTUNITIES_BASE_DIR)

    scraped_jobs = scrape_linkedin_jobs()

    if not scraped_jobs:
        print("No jobs were scraped. Exiting.")
        return

    new_opportunities_count = 0
    for job in scraped_jobs:
        folder_path = create_opportunity_folder(job)
        if folder_path:
            print(f"  -> SUCCESS: Created new opportunity folder at: {folder_path}")
            new_opportunities_count += 1
        else:
            print(f"  -> INFO: Skipping duplicate opportunity for {job['role_name']} at {job['company_name']}.")

    print(f"\nScraping complete. Found and created {new_opportunities_count} new opportunities.")

if __name__ == '__main__':
    main()