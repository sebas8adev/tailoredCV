import os
import sys
import shutil
import re
from weasyprint import HTML

# --- Configuration ---
# Define paths relative to this script's location
CV_TEMPLATE_HTML_PATH = 'cv_template.html'
CL_TEMPLATE_HTML_PATH = 'cl_template.html'
DATA_TEMPLATE_PATH = 'data_template.txt'
OPPORTUNITIES_BASE_DIR = '../3_Opportunities' # The folder containing all job opportunities

def get_opportunity_status(job_desc_path):
    """Reads the job description file and returns the status as a string."""
    try:
        with open(job_desc_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.lower().strip().startswith("status:"):
                    return line.split(":", 1)[1].strip().lower()
    except FileNotFoundError:
        return "not_found"
    except Exception as e:
        print(f"  > Error reading status from {job_desc_path}: {e}")
        return "error"
    return "unknown"

def update_status_to_processed(job_desc_path):
    """Reads the entire file, updates the status line, and writes it back."""
    try:
        with open(job_desc_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        with open(job_desc_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.lower().strip().startswith("status:"):
                    f.write("Status: processed\n")
                else:
                    f.write(line)
        print("  > Status updated to 'processed'.")
        return True
    except Exception as e:
        print(f"  > FAILED to update status for {job_desc_path}: {e}")
        return False

def process_opportunity_folder(folder_path):
    """Runs the full document generation process for a single opportunity folder."""
    print(f"--- Starting Document Generation for: {folder_path} ---")
    
    # Auto-copy the data template for this run
    data_file_path = os.path.join(folder_path, 'data.txt')
    job_description_path = os.path.join(folder_path, 'jobdescription.txt')
    
    try:
        shutil.copy2(DATA_TEMPLATE_PATH, data_file_path)
        print(f"  > Copied data template for processing.")
    except Exception as e:
        print(f"  > ERROR: Could not copy data template: {e}. Aborting this folder.")
        return False

    # Read data from both the job description and the newly copied data file
    job_data = read_data_from_file(job_description_path)
    cv_data = read_data_from_file(data_file_path)
    if not job_data or not cv_data:
        print("  > ERROR: Failed to load data from jobdescription.txt or data.txt. Aborting.")
        return False

    # Combine data - job-specific data will override the template data
    document_data = {**cv_data, **job_data}
    fixed_output_name = "Sebastian-Ochoa-Alvarez"

    # Process CV
    print("\n--- Processing CV ---")
    cv_html_content = generate_html_content(CV_TEMPLATE_HTML_PATH, document_data, "CV")
    if cv_html_content:
        output_html = os.path.join(folder_path, f"CV-{fixed_output_name}.html")
        output_pdf = os.path.join(folder_path, f"CV-{fixed_output_name}.pdf")
        with open(output_html, 'w', encoding='utf-8') as f: f.write(cv_html_content)
        print(f"  > Generated HTML: {output_html}")
        if not convert_html_to_pdf(cv_html_content, output_pdf): return False
    else: return False

    # Process CL
    print("\n--- Processing CL ---")
    cl_html_content = generate_html_content(CL_TEMPLATE_HTML_PATH, document_data, "CL")
    if cl_html_content:
        output_html = os.path.join(folder_path, f"CL-{fixed_output_name}.html")
        output_pdf = os.path.join(folder_path, f"CL-{fixed_output_name}.pdf")
        with open(output_html, 'w', encoding='utf-8') as f: f.write(cl_html_content)
        print(f"  > Generated HTML: {output_html}")
        if not convert_html_to_pdf(cl_html_content, output_pdf): return False
    else: return False
    
    return True # Return True on full success

def main():
    """Main function to find and process all pending opportunities."""
    print("--- Starting Automated Document Generation ---")
    print(f"Scanning for opportunities in: {OPPORTUNITIES_BASE_DIR}")

    if not os.path.isdir(OPPORTUNITIES_BASE_DIR):
        print(f"Error: Opportunities directory not found at '{OPPORTUNITIES_BASE_DIR}'")
        return

    pending_found = 0
    # Iterate through all items in the opportunities directory
    for folder_name in sorted(os.listdir(OPPORTUNITIES_BASE_DIR)):
        opportunity_path = os.path.join(OPPORTUNITIES_BASE_DIR, folder_name)
        
        # Ensure it's a directory
        if os.path.isdir(opportunity_path):
            job_desc_path = os.path.join(opportunity_path, 'jobdescription.txt')
            status = get_opportunity_status(job_desc_path)
            
            print(f"\nChecking '{folder_name}'... Status: {status.upper()}")
            
            if status == 'pending':
                pending_found += 1
                # Process the folder
                success = process_opportunity_folder(opportunity_path)
                
                if success:
                    print(f"--- Successfully processed {folder_name} ---")
                    update_status_to_processed(job_desc_path)
                else:
                    print(f"--- FAILED to process {folder_name}. Leaving status as 'pending' for review. ---")

    if pending_found == 0:
        print("\nScan complete. No pending opportunities found.")
    else:
        print(f"\nScan complete. Processed {pending_found} pending opportunities.")


# Helper functions (read_data_from_file, etc.) remain the same
def read_data_from_file(file_path):
    data = {}
    current_key = None
    current_value_lines = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                if line.lower().strip().startswith("status:"): continue # Ignore status line for data parsing
                if ':' in line and current_key is None:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    if value: data[key] = value
                    else: current_key = key
                elif current_key:
                    current_value_lines.append(line)
                    if line == '---END_SECTION---':
                        data[current_key] = "\n".join(current_value_lines[:-1]).strip()
                        current_key = None
                        current_value_lines = []
    except Exception as e:
        print(f"Error reading data file {file_path}: {e}")
        return None
    if current_key: data[current_key] = "\n".join(current_value_lines).strip()
    return data

def generate_html_content(template_path, data, doc_type):
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        for key, value in data.items():
            html_content = html_content.replace(f"{{{{{key}}}}}", str(value))
        if doc_type == "CL":
            subject_template = data.get("SUBJECT", "")
            final_subject = subject_template.replace("{{JOB_ROLE}}", data.get("Role Name", "")).replace("{{COMPANY_NAME}}", data.get("Company Name", ""))
            html_content = html_content.replace("{{SUBJECT}}", final_subject)
        elif doc_type == "CV":
             companies = ["GLOBANT", "MANGOSOFT", "TIPI", "ITBIGBOSS", "BODYTECH", "INTERSOFT"]
             for company in companies:
                 for i in range(1, 4):
                     bullet_key = f"COMPANY_BULLET_{i}_{company}"
                     bullet_value = data.get(bullet_key, "").strip().lstrip('- •').strip()
                     html_content = html_content.replace(f"{{{{{bullet_key}}}}}", bullet_value)
        return html_content
    except Exception as e:
        print(f"Error generating HTML: {e}")
        return None

def convert_html_to_pdf(html_content, output_pdf_path):
    print(f"  > Attempting to convert HTML to PDF: {output_pdf_path}")
    try:
        HTML(string=html_content).write_pdf(output_pdf_path)
        print(f"  > Successfully created PDF.")
        return True
    except Exception as e:
        print(f"  > Error during PDF conversion: {e}")
        return False


if __name__ == '__main__':
    main()