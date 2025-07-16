# Import necessary libraries
import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Define the scopes required for Google Docs API access.
# 'https://www.googleapis.com/auth/documents.readonly' allows reading documents.
# 'https://www.googleapis.com/auth/drive.readonly' allows reading metadata about files (like their names).
# If you need to modify documents programmatically, you would add 'https://www.googleapis.com/auth/documents'
SCOPES = ['https://www.googleapis.com/auth/documents.readonly', 'https://www.googleapis.com/auth/drive.readonly']

def authenticate_google_api():
    """Authenticates with Google and returns credentials."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # The 'credentials.json' file is downloaded from Google Cloud Console.
            # Make sure it's in the same directory as this script.
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def download_google_doc(document_id, file_path, creds):
    """
    Downloads a Google Doc as a PDF file.

    Args:
        document_id (str): The ID of the Google Document to download.
        file_path (str): The full path where the PDF file will be saved.
        creds (google.oauth2.credentials.Credentials): Authenticated Google credentials.
    """
    try:
        # Build the Google Drive API service. We use Drive API to export documents.
        drive_service = build('drive', 'v3', credentials=creds)

        # Request to export the document as PDF
        # Changed mimeType from 'application/vnd.oasis.opendocument.text' to 'application/pdf'
        request = drive_service.files().export_media(fileId=document_id,
                                                     mimeType='application/pdf')
        
        # Execute the request and save the content to the specified file path.
        with open(file_path, 'wb') as fh:
            downloaded_file = request.execute()
            fh.write(downloaded_file)
        print(f"Document downloaded successfully to: {file_path}")

    except HttpError as error:
        print(f"An error occurred: {error}")
        print("Please ensure the Google Doc ID is correct and you have access to it.")
    except Exception as e:
        print(f"An unexpected error occurred during download: {e}")

def get_google_doc_name(document_id, creds):
    """
    Retrieves the name of a Google Document.

    Args:
        document_id (str): The ID of the Google Document.
        creds (google.oauth2.credentials.Credentials): Authenticated Google credentials.

    Returns:
        str: The name of the document, or None if an error occurs.
    """
    try:
        drive_service = build('drive', 'v3', credentials=creds)
        # Fetch only the 'name' field for efficiency
        file = drive_service.files().get(fileId=document_id, fields='name').execute()
        return file.get('name')
    except HttpError as error:
        print(f"An error occurred while fetching document name: {error}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def main():
    """Main function to run the application."""
    print("--- Cover Letter/CV Tailor - Phase 1 ---")
    print("This script will download a Google Document and save it locally.")

    # 1. Authenticate with Google
    creds = authenticate_google_api()
    if not creds:
        print("Authentication failed. Exiting.")
        return

    # 2. Get Google Doc ID from user
    google_doc_id = input("\nEnter the Google Document ID (from the URL, e.g., 1ABC...xyz): ").strip()
    if not google_doc_id:
        print("Google Document ID cannot be empty. Exiting.")
        return

    # Optional: Get document name for better user feedback
    doc_name = get_google_doc_name(google_doc_id, creds)
    if doc_name:
        print(f"Found Google Document: '{doc_name}'")
    else:
        print("Could not retrieve document name. Please ensure the ID is correct and you have access.")
        # Decide if you want to exit or proceed without the name
        # For now, we'll proceed, but the user might want to re-enter ID if name wasn't found.

    # 3. Get company name and job description from user
    company_name = input("Enter the Company Name: ").strip()
    job_description = input("Enter the Job Description (e.g., 'Software Engineer'): ").strip()

    if not company_name or not job_description:
        print("Company Name and Job Description cannot be empty. Exiting.")
        return

    # 4. Create the folder structure
    # Sanitize inputs for folder names (remove invalid characters)
    # This is a basic sanitization. For production, consider a more robust library.
    sanitized_company_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).strip()
    sanitized_job_description = "".join(c for c in job_description if c.isalnum() or c in (' ', '-', '_')).strip()

    today_date = datetime.date.today().strftime("%Y-%m-%d") # Format: YYYY-MM-DD

    # Construct the full path for the new folder
    # The base directory will be where the script is run, or you can specify a different one.
    base_save_directory = "Tailored_Documents" # Or specify a full path like "C:/Users/YourUser/Documents/Tailored_Documents"
    
    # Create the nested folder path
    save_folder_path = os.path.join(base_save_directory, sanitized_company_name, sanitized_job_description, today_date)

    try:
        os.makedirs(save_folder_path, exist_ok=True)
        print(f"Created folder structure: {save_folder_path}")
    except OSError as e:
        print(f"Error creating directory {save_folder_path}: {e}")
        print("Please check permissions or path validity. Exiting.")
        return

    # 5. Define the local file name and full path
    # Using the original document name if available, otherwise a generic one.
    # Changed file extension from .odt to .pdf
    output_filename = f"{doc_name if doc_name else 'document'}.pdf"
    output_file_path = os.path.join(save_folder_path, output_filename)

    # 6. Download the Google Doc
    print(f"Attempting to download Google Doc ID: {google_doc_id}...")
    download_google_doc(google_doc_id, output_file_path, creds)

    print("\nPhase 1 completed!")
    print(f"Your document is saved at: {output_file_path}")

if __name__ == '__main__':
    main()
