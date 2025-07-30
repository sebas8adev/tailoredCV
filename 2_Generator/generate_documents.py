# FILE: ./2_Generator/generate_documents.py

import os
import sys
import shutil
import re
from datetime import datetime
from weasyprint import HTML

# --- Dynamic Path Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OPPORTUNITIES_BASE_DIR = os.path.join(PROJECT_ROOT, '3_Opportunities')
TODO_FILE_PATH = os.path.join(PROJECT_ROOT, 'todo.txt') # Path for the new to-do file
# Template paths are relative to this script's location
CV_TEMPLATE_HTML_PATH = os.path.join(SCRIPT_DIR, 'cv_template.html')
CL_TEMPLATE_HTML_PATH = os.path.join(SCRIPT_DIR, 'cl_template.html')

def get_specific_status(file_path, status_key):
    """Reads a file and returns the value of a specific status key."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.lower().strip().startswith(status_key.lower() + ":"):
                    return line.split(":", 1)[1].strip().lower()
    except FileNotFoundError:
        return "not_found"
    return "unknown"

def update_specific_status(file_path, status_key, new_status):
    """Reads the entire file, updates a specific status line, and writes it back."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f: lines = f.readlines()
        with open(file_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.lower().strip().startswith(status_key.lower() + ":"):
                    f.write(f"{status_key}: {new_status}\n")
                else: f.write(line)
        print(f"  > {status_key} updated to '{new_status}'.")
        return True
    except Exception as e:
        print(f"  > FAILED to update {status_key} for {file_path}: {e}")
        return False

def log_to_todo_file(opportunity_path, job_data):
    """Appends a new entry to the master todo.txt file."""
    try:
        url = job_data.get('Job post URL', 'URL not found')
        company = job_data.get('Company Name', 'Unknown Company')
        role = job_data.get('Role Name', 'Unknown Role')
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        log_entry = (
            f"---------------------------------------------------\n"
            f"Generated on: {timestamp}\n"
            f"Company: {company}\n"
            f"Role: {role}\n"
            f"\n"
            f"  > Application URL:\n"
            f"    {url}\n"
            f"\n"
            f"  > Generated Documents Path:\n"
            f"    {os.path.abspath(opportunity_path)}\n"
            f"---------------------------------------------------\n\n"
        )

        with open(TODO_FILE_PATH, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(f"  > Successfully logged to '{os.path.basename(TODO_FILE_PATH)}'.")
        return True
    except Exception as e:
        print(f"  > WARNING: Could not write to {os.path.basename(TODO_FILE_PATH)}: {e}")
        return False

def process_opportunity_folder(folder_path):
    """Runs the full document generation process for a single opportunity folder."""
    print(f"--- Starting Document Generation for: {folder_path} ---")
    
    data_file_path = os.path.join(folder_path, 'data.txt')
    job_desc_path = os.path.join(folder_path, 'jobdescription.txt')

    if not os.path.exists(data_file_path):
        print(f"  > ERROR: data.txt not found in this folder. Skipping."); return False, None

    # We need data from both files for logging and generation
    ai_generated_data = read_data_from_file(data_file_path)
    job_description_data = read_data_from_file(job_desc_path)
    
    if not ai_generated_data or not job_description_data:
        print("  > ERROR: Failed to load data from required files. Aborting."); return False, None
    
    # Combine all data for the templates
    document_data = {**ai_generated_data, **job_description_data}
    fixed_output_name = "Sebastian-Ochoa-Alvarez"

    print("\n--- Processing CV ---")
    cv_html_content = generate_html_content(CV_TEMPLATE_HTML_PATH, document_data, "CV")
    if cv_html_content:
        output_html = os.path.join(folder_path, f"CV-{fixed_output_name}.html")
        output_pdf = os.path.join(folder_path, f"CV-{fixed_output_name}.pdf")
        with open(output_html, 'w', encoding='utf-8') as f: f.write(cv_html_content)
        print(f"  > Generated HTML: {output_html}")
        if not convert_html_to_pdf(cv_html_content, output_pdf): return False, None
    else: return False, None

    print("\n--- Processing CL ---")
    cl_html_content = generate_html_content(CL_TEMPLATE_HTML_PATH, document_data, "CL")
    if cl_html_content:
        output_html = os.path.join(folder_path, f"CL-{fixed_output_name}.html")
        output_pdf = os.path.join(folder_path, f"CL-{fixed_output_name}.pdf")
        with open(output_html, 'w', encoding='utf-8') as f: f.write(cl_html_content)
        print(f"  > Generated HTML: {output_html}")
        if not convert_html_to_pdf(cl_html_content, output_pdf): return False, None
    else: return False, None
    
    return True, job_description_data # Return success and the data needed for logging

def main():
    """Main function to find and process all pending opportunities."""
    print("--- Phase 3: Final Document Generation ---")
    print(f"Scanning for opportunities in: {OPPORTUNITIES_BASE_DIR}")

    if not os.path.isdir(OPPORTUNITIES_BASE_DIR):
        print(f"Error: Opportunities directory not found at '{OPPORTUNITIES_BASE_DIR}'"); return

    pending_docs_found = 0
    for folder_name in sorted(os.listdir(OPPORTUNITIES_BASE_DIR)):
        opportunity_path = os.path.join(OPPORTUNITIES_BASE_DIR, folder_name)
        
        if os.path.isdir(opportunity_path):
            job_desc_path = os.path.join(opportunity_path, 'jobdescription.txt')
            
            overall_status = get_specific_status(job_desc_path, "Status")
            data_status = get_specific_status(job_desc_path, "Data-Status")
            
            print(f"\nChecking '{folder_name}'... Status: {overall_status.upper()}, Data-Status: {data_status.upper()}")
            
            if overall_status == 'pending' and data_status == 'complete':
                pending_docs_found += 1
                success, job_data_for_log = process_opportunity_folder(opportunity_path)
                
                if success:
                    print(f"--- Successfully processed {folder_name} ---")
                    # Log to the to-do file first
                    log_to_todo_file(opportunity_path, job_data_for_log)
                    # Then update the status
                    update_specific_status(job_desc_path, "Status", "processed")
                else:
                    print(f"--- FAILED to process {folder_name}. Leaving status as 'pending' for review. ---")

    if pending_docs_found == 0:
        print("\nScan complete. No pending opportunities with complete data were found.")
    else:
        print(f"\nScan complete. Generated documents for {pending_docs_found} opportunities.")

def read_data_from_file(file_path):
    data = {}
    current_key = None
    current_value_lines = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                # Skip status lines, but read other data
                if any(line.lower().strip().startswith(s) for s in ["status:", "data-status:"]) and current_key is None: continue
                
                if '---END_SECTION---' in line:
                    if current_key:
                        data[current_key] = "\n".join(current_value_lines).strip()
                        current_key = None; current_value_lines = []
                    continue
                if ':' in line and current_key is None:
                    key, value = line.split(':', 1)
                    key = key.strip(); value = value.strip()
                    if value: data[key] = value
                    else: current_key = key
                elif current_key:
                    current_value_lines.append(line)
    except Exception as e:
        print(f"Error reading data file {file_path}: {e}"); return None
    if current_key: data[current_key] = "\n".join(current_value_lines).strip()
    return data

def generate_html_content(template_path, data, doc_type):
    try:
        with open(template_path, 'r', encoding='utf-8') as f: html_content = f.read()
        for key, value in data.items():
            html_content = html_content.replace(f"{{{{{key}}}}}", str(value))
        if doc_type == "CL":
            subject = data.get("SUBJECT", "").replace("{{JOB_ROLE}}", data.get("Role Name", "")).replace("{{COMPANY_NAME}}", data.get("Company Name", ""))
            html_content = html_content.replace("{{SUBJECT}}", subject)
        return html_content
    except Exception as e:
        print(f"Error generating HTML: {e}"); return None

def convert_html_to_pdf(html_content, output_pdf_path):
    print(f"  > Attempting to convert HTML to PDF: {output_pdf_path}")
    try:
        HTML(string=html_content).write_pdf(output_pdf_path)
        print(f"  > Successfully created PDF.")
        return True
    except Exception as e:
        print(f"  > Error during PDF conversion: {e}"); return False

if __name__ == '__main__':
    main()