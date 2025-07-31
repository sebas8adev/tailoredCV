# FILE: ./2_Data_Tailor/tailor_data.py

import os
import sys
import re
import google.generativeai as genai

# --- Dynamic Path Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OPPORTUNITIES_BASE_DIR = os.path.join(PROJECT_ROOT, '3_Opportunities')
PREPROMPT_PATH = os.path.join(PROJECT_ROOT, 'preprompt.txt')
PROMPT_PATH = os.path.join(PROJECT_ROOT, 'prompt.txt')

def get_specific_status(file_path, status_key):
    """Reads a file and returns the value of a specific status key."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.lower().strip().startswith(status_key.lower() + ":"):
                    # --- THIS IS THE CORRECTED LINE ---
                    return line.split(":", 1)[1].strip().lower()
    except FileNotFoundError:
        return "not_found"
    return "unknown"

def update_specific_status(file_path, status_key, new_status):
    """Reads the entire file, updates a specific status line, and writes it back."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        with open(file_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.lower().strip().startswith(status_key.lower() + ":"):
                    f.write(f"{status_key}: {new_status}\n")
                else:
                    f.write(line)
        print(f"  > {status_key} updated to '{new_status}'.")
        return True
    except Exception as e:
        print(f"  > FAILED to update {status_key} for {file_path}: {e}")
        return False

def main():
    """Finds opportunities needing data generation and uses AI to create data.txt files."""
    print("--- Phase 2: AI Data Tailoring ---")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY environment variable not found."); sys.exit(1)
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')
    print("Successfully configured Google AI with model 'gemini-2.5-pro'.")

    try:
        with open(PREPROMPT_PATH, 'r', encoding='utf-8') as f: preprompt = f.read()
        with open(PROMPT_PATH, 'r', encoding='utf-8') as f: main_prompt = f.read()
        print("Loaded prompt files.")
    except FileNotFoundError as e:
        print(f"ERROR: Could not find prompt files. {e}"); sys.exit(1)

    opportunities_to_process = 0
    if not os.path.isdir(OPPORTUNITIES_BASE_DIR):
        print(f"Error: Opportunities directory not found at '{OPPORTUNITIES_BASE_DIR}'"); return

    for folder_name in sorted(os.listdir(OPPORTUNITIES_BASE_DIR)):
        opportunity_path = os.path.join(OPPORTUNITIES_BASE_DIR, folder_name)
        if os.path.isdir(opportunity_path):
            job_desc_path = os.path.join(opportunity_path, 'jobdescription.txt')
            data_status = get_specific_status(job_desc_path, "Data-Status")
            print(f"\nChecking '{folder_name}'... Data-Status: {data_status.upper()}")

            if data_status in ['pending', 'error']:
                opportunities_to_process += 1
                print(f"  > Processing opportunity...")
                try:
                    with open(job_desc_path, 'r', encoding='utf-8') as f:
                        job_description_content = f.read()
                    
                    final_prompt = f"{preprompt}\n\n{main_prompt}\n\n--- JOB DESCRIPTION ---\n\n{job_description_content}"
                    
                    print("  > Sending prompt to Google AI...")
                    response = model.generate_content(final_prompt)
                    ai_output = re.sub(r'```(text|markdown|)?', '', response.text).strip()

                    data_txt_path = os.path.join(opportunity_path, 'data.txt')
                    with open(data_txt_path, 'w', encoding='utf-8') as f:
                        f.write(ai_output)
                    print(f"  > SUCCESS: AI-generated data.txt saved.")
                    update_specific_status(job_desc_path, "Data-Status", "complete")
                except Exception as e:
                    print(f"  > ERROR: An error occurred during AI processing for {folder_name}: {e}")
                    update_specific_status(job_desc_path, "Data-Status", "error")

    if opportunities_to_process == 0:
        print("\nScan complete. No opportunities need data.txt generation.")
    else:
        print(f"\nScan complete. Processed {opportunities_to_process} opportunities.")

if __name__ == '__main__':
    main()