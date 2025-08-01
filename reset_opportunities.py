# FILE: ./reset_opportunities.py

import os
import sys

# --- Dynamic Path Configuration ---
# Assumes this script is in the project's root directory.
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
OPPORTUNITIES_BASE_DIR = os.path.join(PROJECT_ROOT, '3_Opportunities')
TODO_FILE_PATH = os.path.join(PROJECT_ROOT, 'todo.txt')

def reset_all_opportunities():
    """
    Resets the entire project to a state where all opportunities can be re-processed.
    - Deletes generated files (data.txt, PDFs, HTMLs).
    - Resets status flags in jobdescription.txt.
    - Clears the todo.txt log.
    """
    print("--- Opportunity Reset Utility ---")
    print("\nThis script will perform the following actions:")
    print("  1. Iterate through all folders in '3_Opportunities'.")
    print("  2. Delete all 'data.txt' files.")
    print("  3. Delete all generated CV and CL (.pdf, .html) files.")
    print("  4. Reset 'Status' and 'Data-Status' to 'pending' in all 'jobdescription.txt' files.")
    print("  5. Clear all content from 'todo.txt'.")
    print("\nThis action is irreversible.")
    
    # --- Safety Confirmation ---
    confirm = input("Are you sure you want to continue? (y/n): ").lower()
    if confirm != 'y':
        print("Operation cancelled by user.")
        sys.exit(0)

    print("\n--- Starting Reset Process ---")

    if not os.path.isdir(OPPORTUNITIES_BASE_DIR):
        print(f"ERROR: Opportunities directory not found at '{OPPORTUNITIES_BASE_DIR}'. Aborting.")
        sys.exit(1)

    folders_processed = 0
    files_deleted = 0

    for folder_name in sorted(os.listdir(OPPORTUNITIES_BASE_DIR)):
        opportunity_path = os.path.join(OPPORTUNITIES_BASE_DIR, folder_name)
        
        if os.path.isdir(opportunity_path):
            print(f"\nProcessing folder: {folder_name}")
            folders_processed += 1
            
            files_to_delete = [
                'data.txt',
                'CL-Sebastian-Ochoa-Alvarez.html',
                'CL-Sebastian-Ochoa-Alvarez.pdf',
                'CV-Sebastian-Ochoa-Alvarez.html',
                'CV-Sebastian-Ochoa-Alvarez.pdf'
            ]

            for filename in files_to_delete:
                file_path = os.path.join(opportunity_path, filename)
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"  > Deleted: {filename}")
                        files_deleted += 1
                except OSError as e:
                    print(f"  > ERROR deleting {filename}: {e}")

            job_desc_path = os.path.join(opportunity_path, 'jobdescription.txt')
            if os.path.exists(job_desc_path):
                try:
                    with open(job_desc_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    with open(job_desc_path, 'w', encoding='utf-8') as f:
                        for line in lines:
                            if line.lower().strip().startswith("status:"):
                                f.write("Status: pending\n")
                            elif line.lower().strip().startswith("data-status:"):
                                f.write("Data-Status: pending\n")
                            else:
                                f.write(line)
                    print("  > Reset statuses in jobdescription.txt")
                except Exception as e:
                    print(f"  > ERROR updating {job_desc_path}: {e}")
            else:
                 print("  > WARNING: jobdescription.txt not found.")

    try:
        if os.path.exists(TODO_FILE_PATH):
            with open(TODO_FILE_PATH, 'w', encoding='utf-8') as f:
                pass 
            print(f"\nCleared all content from '{os.path.basename(TODO_FILE_PATH)}'.")
    except Exception as e:
        print(f"\nERROR clearing {os.path.basename(TODO_FILE_PATH)}: {e}")

    print("\n--- Reset Complete ---")
    print(f"Processed {folders_processed} folders.")
    print(f"Deleted a total of {files_deleted} generated files.")
    print("All opportunities are now ready to be re-processed by the pipeline.")


if __name__ == '__main__':
    reset_all_opportunities()