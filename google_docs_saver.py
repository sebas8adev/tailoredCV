import os
import datetime
import re
import shutil
from weasyprint import HTML # Import WeasyPrint

# --- User Configuration ---
# Paths to your HTML template files
CV_TEMPLATE_HTML_PATH = 'cv_template.html'
CL_TEMPLATE_HTML_PATH = 'cl_template.html'
# Paths to source data files to be copied
DATA_FILE_PATH = 'data.txt'
JOB_DESCRIPTION_FILE_PATH = 'jobdescription.txt' # Assuming this file exists in the same directory

# --- Data Reading Function (Same as before) ---
def read_data_from_file(file_path):
    """
    Reads data from a text file, parsing key-value pairs and multi-line sections.
    Special handling for SKILLS_LIST and CERTIFICATIONS_LIST to parse into subtitle/description.
    """
    data = {}
    current_key = None
    current_value_lines = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): # Skip empty lines and comments
                    continue
                
                if line == '---END_SECTION---':
                    if current_key:
                        if current_key in ["SKILLS_LIST", "CERTIFICATIONS_LIST"]: # Handle both lists similarly
                            # Process lists specifically: parse into list of dicts
                            parsed_list = []
                            for item_line in current_value_lines:
                                # Regex to capture - **Subtitle**: Description
                                match = re.match(r'^- \*\*(.*?)\*\*:(.*)', item_line)
                                if match:
                                    subtitle = match.group(1).strip()
                                    description = match.group(2).strip()
                                    parsed_list.append({"subtitle": subtitle, "description": description})
                                else:
                                    print(f"Warning: {current_key} line format mismatch: '{item_line}'. Skipping this line.")
                            data[current_key] = parsed_list
                        else:
                            data[current_key] = "\n".join(current_value_lines).strip()
                        current_key = None
                        current_value_lines = []
                    continue

                if ':' in line and current_key is None:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    if value: # If value is not empty, it's a single-line entry
                        data[key] = value
                    else: # If value is empty, it's the start of a multi-line entry
                        current_key = key
                        current_value_lines = []
                elif current_key: # Continue collecting lines for a multi-line entry
                    current_value_lines.append(line)
                else:
                    print(f"Warning: Skipping unparseable line in {file_path}: {line}")
    except FileNotFoundError:
        print(f"Error: Data file not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error reading data file: {e}")
        return None
    
    # Add any remaining multi-line section if file ends without ---END_SECTION---
    if current_key and current_value_lines:
        if current_key in ["SKILLS_LIST", "CERTIFICATIONS_LIST"]:
            parsed_list = []
            for item_line in current_value_lines:
                match = re.match(r'^- \*\*(.*?)\*\*:(.*)', item_line)
                if match:
                    subtitle = match.group(1).strip()
                    description = match.group(2).strip()
                    parsed_list.append({"subtitle": subtitle, "description": description})
                else:
                    print(f"Warning: {current_key} line format mismatch: '{item_line}'. Skipping this line.")
            data[current_key] = parsed_list
        else:
            data[current_key] = "\n".join(current_value_lines).strip()

    return data


def generate_html_content(template_html_path, data, doc_type):
    """
    Reads an HTML template, replaces placeholders with data, and returns the full HTML string.
    """
    try:
        with open(template_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Prepare replacements
        replacements = {}

        # Global Information
        replacements["{{APPLICATION_DATE}}"] = datetime.date.today().strftime("%Y-%m-%d")
        replacements["{{HIRING_MANAGER}}"] = data.get("HIRING_MANAGER", "")
        replacements["{{COMPANY_NAME}}"] = data.get("COMPANY_NAME", "")
        replacements["{{JOB_ROLE}}"] = data.get("JOB_ROLE", "")

        # Cover Letter Specific Content
        if doc_type == "CL":
            subject_template = data.get("SUBJECT", "")
            final_subject = subject_template.replace("{{JOB_ROLE}}", replacements["{{JOB_ROLE}}"]).replace("{{COMPANY_NAME}}", replacements["{{COMPANY_NAME}}"])
            replacements["{{SUBJECT}}"] = final_subject
            replacements["{{CONTENT}}"] = data.get("CONTENT", "")

        # CV Specific Content
        if doc_type == "CV":
            replacements["{{CAREER_SUMMARY}}"] = data.get("CAREER_SUMMARY", "")

            # SKILLS_TITLE and SKILLS_DESC
            for i in range(1, 5): # Assuming SKILLS_TITLE_1 to SKILLS_TITLE_4
                replacements[f"{{{{SKILLS_TITLE_{i}}}}}"] = data.get(f"SKILLS_TITLE_{i}", "")
                replacements[f"{{{{SKILLS_DESC_{i}}}}}"] = data.get(f"SKILLS_DESC_{i}", "")

            # Company Summaries and Bullet Points
            companies = ["GLOBANT", "MANGOSOFT", "TIPI", "ITBIGBOSS", "BODYTECH", "INTERSOFT"] # Added INTERSOFT
            for company in companies:
                # Add JOB_TITLE for each company
                replacements[f"{{{{JOB_TITLE_{company}}}}}"] = data.get(f"JOB_TITLE_{company}", "")
                
                replacements[f"{{{{COMPANY_SUMMARY_{company}}}}}"] = data.get(f"COMPANY_SUMMARY_{company}", "")
                
                # For company bullet points, we need to format them as HTML <li> items
                # Note: The HTML template uses {{COMPANY_BULLET_1_GLOBANT}} directly inside <li> tags.
                # We will replace these individually in a loop below.
                # If the template uses a single {{BULLET_POINTS_COMPANY}} placeholder, then the above logic would be used.
                # Given the template, we'll process each bullet point placeholder individually.
                replacements[f"{{{{COMPANY_BULLET_1_{company}}}}}"] = data.get(f"COMPANY_BULLET_1_{company}", "").strip().lstrip('- •').strip()
                replacements[f"{{{{COMPANY_BULLET_2_{company}}}}}"] = data.get(f"COMPANY_BULLET_2_{company}", "").strip().lstrip('- •').strip()
                replacements[f"{{{{COMPANY_BULLET_3_{company}}}}}"] = data.get(f"COMPANY_BULLET_3_{company}", "").strip().lstrip('- •').strip()


            # Certifications and Education are hardcoded in the HTML template,
            # so we don't need to replace them from data.txt unless they were placeholders.
            # Based on the provided HTML template, they are static.
            # If they were placeholders like {{CERTIFICATIONS_LIST}}, we'd process them here.
            # For now, I will assume the provided HTML template is the source of truth for structure,
            # and only replace the placeholders that exist in it.

        # Perform the actual replacements
        for placeholder, value in replacements.items():
            html_content = html_content.replace(placeholder, value)

        return html_content

    except FileNotFoundError:
        print(f"Error: HTML template not found at {template_html_path}")
        return None
    except Exception as e:
        print(f"Error generating HTML content: {e}")
        return None


def convert_html_to_pdf(html_content, output_pdf_path):
    """
    Converts an HTML string to a PDF file using WeasyPrint.
    """
    print(f"  Attempting to convert HTML to PDF: {output_pdf_path}")
    try:
        HTML(string=html_content).write_pdf(output_pdf_path)
        print(f"  Successfully created PDF: {output_pdf_path}")
        return True
    except Exception as e:
        print(f"  Error during HTML to PDF conversion: {e}")
        print("  Please ensure WeasyPrint and its system dependencies (like GTK+ on Windows, Pango/Cairo/GDK-Pixbuf on Linux/macOS) are correctly installed.")
        return False


def main():
    """Main function to run the application."""
    print("--- Cover Letter/CV Tailor - Phase 2 (HTML & PDF Processing) ---")
    print("This script will generate tailored HTML documents and convert them to PDF.")

    # 1. Read data from data.txt
    document_data = read_data_from_file(DATA_FILE_PATH)
    if not document_data:
        print("Failed to load data from data.txt. Exiting.")
        return

    # --- DEBUGGING STEP: Print the loaded data ---
    print("\n--- Contents of document_data after reading data.txt ---")
    for key, value in document_data.items():
        if "JOB_TITLE_" in key or "COMPANY_SUMMARY_" in key or "COMPANY_BULLET_" in key:
            print(f"{key}: {value}")
    print("-----------------------------------------------------")
    # --- END DEBUGGING STEP ---


    # Extract company name and job role from data.txt
    company_name_from_file = document_data.get("COMPANY_NAME", "Unknown Company")
    job_role_from_file = document_data.get("JOB_ROLE", "Unknown Role")

    print(f"\nUsing Company Name from data.txt: {company_name_from_file}")
    print(f"Using Job Role from data.txt: {job_role_from_file}")

    # 2. Create the folder structure
    sanitized_company_name = "".join(c for c in company_name_from_file if c.isalnum() or c in (' ', '-', '_')).strip()
    sanitized_job_description = "".join(c for c in job_role_from_file if c.isalnum() or c in (' ', '-', '_')).strip()

    today_date = datetime.date.today().strftime("%Y-%m-%d")

    base_save_directory = "Tailored_Documents_HTML_PDF"
    save_folder_path = os.path.join(base_save_directory, sanitized_company_name, sanitized_job_description, today_date)

    try:
        os.makedirs(save_folder_path, exist_ok=True)
        print(f"\nCreated folder structure: {save_folder_path}")
    except OSError as e:
        print(f"Error creating directory {save_folder_path}: {e}")
        print("Please check permissions or path validity. Exiting.")
        return

    # Fixed name part for the output files as requested
    fixed_output_name = "Sebastian-Ochoa-Alvarez"

    # 3. Process CV
    print(f"\n--- Processing CV ---")
    cv_html_content = generate_html_content(CV_TEMPLATE_HTML_PATH, document_data, "CV")
    if cv_html_content:
        output_cv_html_path = os.path.join(save_folder_path, f"CV-{fixed_output_name}.html")
        output_cv_pdf_path = os.path.join(save_folder_path, f"CV-{fixed_output_name}.pdf")
        
        with open(output_cv_html_path, 'w', encoding='utf-8') as f:
            f.write(cv_html_content)
        print(f"  Generated HTML file: {output_cv_html_path}")

        convert_html_to_pdf(cv_html_content, output_cv_pdf_path)

    # 4. Process CL
    print(f"\n--- Processing CL ---")
    cl_html_content = generate_html_content(CL_TEMPLATE_HTML_PATH, document_data, "CL")
    if cl_html_content:
        output_cl_html_path = os.path.join(save_folder_path, f"CL-{fixed_output_name}.html")
        output_cl_pdf_path = os.path.join(save_folder_path, f"CL-{fixed_output_name}.pdf")
        
        with open(output_cl_html_path, 'w', encoding='utf-8') as f:
            f.write(cl_html_content)
        print(f"  Generated HTML file: {output_cl_html_path}")

        convert_html_to_pdf(cl_html_content, output_cl_pdf_path)

    # 5. Copy source files to the output folder
    print(f"\n--- Copying source files to output folder ---")
    # Copy data.txt
    try:
        shutil.copy2(DATA_FILE_PATH, save_folder_path)
        print(f"  Copied {DATA_FILE_PATH} to {save_folder_path}")
    except FileNotFoundError:
        print(f"  Warning: {DATA_FILE_PATH} not found. Skipping copy.")
    except Exception as e:
        print(f"  Error copying {DATA_FILE_PATH}: {e}")

    # Copy jobdescription.txt
    try:
        shutil.copy2(JOB_DESCRIPTION_FILE_PATH, save_folder_path)
        print(f"  Copied {JOB_DESCRIPTION_FILE_PATH} to {save_folder_path}")
    except FileNotFoundError:
        print(f"  Warning: {JOB_DESCRIPTION_FILE_PATH} not found. Skipping copy.")
    except Exception as e:
        print(f"  Error copying {JOB_DESCRIPTION_FILE_PATH}: {e}")

    print("\nPhase 2 (HTML & PDF) completed!")
    print(f"Tailored .html and .pdf documents are generated in: {save_folder_path}")
    print(f"Source files copied to: {save_folder_path}")

if __name__ == '__main__':
    main()

