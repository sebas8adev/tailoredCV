# FILE: ./create_manual_opportunity.py

import os
import sys
import datetime

# --- Dynamic Path Configuration ---
# Assumes this script is in the project's root directory.
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
OPPORTUNITIES_BASE_DIR = os.path.join(PROJECT_ROOT, '3_Opportunities')
PROCESSED_URLS_FILE = os.path.join(PROJECT_ROOT, 'processed_urls.txt')

def load_processed_urls():
    """Loads all previously processed URLs from the log file into a set for fast lookups."""
    if not os.path.exists(PROCESSED_URLS_FILE):
        return set()
    with open(PROCESSED_URLS_FILE, 'r', encoding='utf-8') as f:
        return {line.strip() for line in f if line.strip()}

def log_processed_url(url):
    """Appends a new, successfully processed URL to the log file."""
    with open(PROCESSED_URLS_FILE, 'a', encoding='utf-8') as f:
        f.write(url + '\n')

def main():
    """Interactively prompts the user for job details and creates an opportunity folder."""
    print("--- Manual Job Opportunity Creator ---")
    print("Please provide the details for the job opportunity. Press Enter to skip optional fields.")

    # --- Step 1: Gather Essential Information ---
    company_name = input("\nCompany Name (Required): ").strip()
    role_name = input("Role Name (Required): ").strip()
    job_post_url = input("Job Post URL (Required, for duplicate checking): ").strip()

    if not all([company_name, role_name, job_post_url]):
        print("\n[ERROR] Company Name, Role Name, and Job Post URL are all required. Aborting.")
        sys.exit(1)

    # --- Step 2: Duplicate Check ---
    processed_urls = load_processed_urls()
    base_url = job_post_url.split('&')[0] # Clean the URL
    if base_url in processed_urls:
        print(f"\n[ERROR] This job URL has already been processed. Aborting to prevent a duplicate.")
        sys.exit(0)

    # --- Step 3: Gather Optional Information ---
    print("\n--- Optional Details ---")
    location = input("Location (e.g., Orlando, FL): ").strip() or "Not specified"
    job_type = input("Type (e.g., On-site, Remote, Hybrid): ").strip() or "Not specified"
    salary_range = input("Salary Range (e.g., $100K - $120K): ").strip() or "Not specified"
    hiring_team = input("Hiring Team / Contact Person: ").strip() or "Not identified"
    application_instructions = input("Application Instructions: ").strip() or "See Job Post URL"

    # --- Step 4: Gather Multi-line Job Description ---
    print("\n--- Job Description ---")
    print("Enter/Paste the job description. Type 'END' on a new line and press Enter when finished.")
    description_lines = []
    while True:
        line = input()
        if line.strip().upper() == 'END':
            break
        description_lines.append(line)
    job_description = "\n".join(description_lines)

    # --- Step 5: Create Folder and jobdescription.txt ---
    print("\n--- Processing ---")
    
    sanitized_company = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
    sanitized_role = "".join(c for c in role_name if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    folder_name = f"{sanitized_company}_{sanitized_role}_{date_str}"
    folder_path = os.path.join(OPPORTUNITIES_BASE_DIR, folder_name)

    if os.path.exists(folder_path):
        print(f"[ERROR] A folder for this job already exists for today's date: {folder_name}. Aborting.")
        sys.exit(1)

    try:
        os.makedirs(folder_path)
        job_desc_path = os.path.join(folder_path, "jobdescription.txt")
        with open(job_desc_path, 'w', encoding='utf-8') as f:
            f.write("Status: pending\n")
            f.write("Data-Status: pending\n")
            f.write(f"Job board: Manual Entry\n")
            f.write(f"Company Name: {company_name}\n")
            f.write(f"Role Name: {role_name}\n")
            f.write(f"Location: {location}\n")
            f.write(f"Type: {job_type}\n")
            f.write(f"Salary range: {salary_range}\n")
            f.write(f"Hiring Team: {hiring_team}\n")
            f.write(f"Application Instructions: {application_instructions}\n")
            f.write(f"Job post URL: {job_post_url}\n\n")
            f.write(f"Job Description:\n{job_description}\n")
        
        print(f"  > SUCCESS: Created new opportunity folder at: {folder_path}")

        # --- Step 6: Log the URL to prevent future scraping ---
        log_processed_url(base_url)
        print(f"  > SUCCESS: Added URL to '{os.path.basename(PROCESSED_URLS_FILE)}' to prevent future duplicates.")

    except OSError as e:
        print(f"  > [FATAL ERROR] Could not create directory or file: {e}")
        sys.exit(1)

    print("\nManual opportunity created successfully. It is now ready for the AI Tailoring step.")

if __name__ == '__main__':
    main()