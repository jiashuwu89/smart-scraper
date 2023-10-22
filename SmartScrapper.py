import os
import io
from googleapiclient.http import MediaIoBaseDownload
import json
import logging
from Google import Create_Service
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Format the current datetime
current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
log_filename = f"log/log_{current_time}.log"

logging.basicConfig(filename=log_filename, level=logging.INFO)

def load_config(config_path="config.json"):
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading config: {e}")
        exit(1)
    

class SmartScrapper():
    def __init__(self, service, root_folder_id, start_date=None, end_date=None):
        self.service = service
        request = self.service.files().get(fileId=root_folder_id).execute()
        os.makedirs(request['name'], exist_ok=True)
        self.root_folder_path = request['name']
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
 
    def download_file(self, file_id, outfile):
        """
        Download a file from Google Drive.

        Args:
            file_id (str): The ID of the file to download.
            outfile (str): The path to save the downloaded file.
        """
        try:
            request = self.service.files().get_media(fileId=file_id)

            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fd=fh, request=request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                #print('Download progress {0}'.format(status.progress() * 100))
            fh.seek(0)
            with open(outfile, 'wb') as f:
                f.write(fh.read())
            logging.info(f"File download: {outfile}")
            f.close()
        except Exception as e:
            logging.error(f"Error downloading file: {e}")


    def query_files(self, query):
        """
        Query files from Google Drive based on a specific query.

        Args:
            query (str): The query string for file search.

        Returns:
            list: A list of file objects.
        """
        files = []
        response = self.service.files().list(q=query).execute()
        files.extend(response.get('files'))
        nextPageToken =  response.get('nextPageToken')
        while nextPageToken:
            response = self.service.files().list(q=query, pageToken=nextPageToken).execute()
            files.extend(response.get('files'))
        return files


    def get_folder_date(self, local_path):
        """
        Extract start and end dates from a given path.

        Args:
            local_path (str): The local path containing date information.

        Returns:
            tuple: Start and end dates.
        """
        date_format_mapper = {
            2: '%Y',
            3: '%Y/%m',
            4: '%Y/%m/%d'
        }
        format_string = date_format_mapper.get(len(local_path.split('/')))
        if not format_string:
            return None, None
  
        folder_start_date = datetime.strptime(local_path.split('/', 1)[-1], format_string)
        if format_string == '%Y':
            folder_end_date = folder_start_date + relativedelta(years=1) - timedelta(seconds=1)
        elif format_string == '%Y/%m':
            folder_end_date = folder_start_date + relativedelta(months=1) - timedelta(seconds=1)
        else:
            folder_end_date = folder_start_date + relativedelta(days=1) - timedelta(seconds=1)
       
        return folder_start_date, folder_end_date
    

    def process_folder(self, file, local_path):
        """
        Process a folder based on its date.

        Args:
            file (dict): The file object from Google Drive.
            local_path (str): The local path to save any files.
        """
        try:
            if not self.start_date or not self.end_date:
                os.makedirs(local_path, exist_ok=True)
                logging.info(f"Make folder: {local_path}.")
                self.check_folder_recursive(file['id'], local_path)
                return

            folder_start_date, folder_end_date = self.get_folder_date(local_path)
            if not folder_start_date or not folder_end_date:
                return

            if self.start_date <= folder_end_date and self.end_date >= folder_start_date:
                os.makedirs(local_path, exist_ok=True)
                logging.info(f"Make folder: {local_path}.")
                self.check_folder_recursive(file['id'], local_path)
        except OSError as e:
            logging.error(f"Error creating folder {local_path}: {e}")


    def process_file(self, file, local_path):
        """
        Process a text file based on its date.

        Args:
            file (dict): The file object from Google Drive.
            local_path (str): The local path to save any files.
        """
        try:
            file_date_str = file['name'].split('_')[-1].split('.')[0]
            file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
            if not self.start_date or not self.end_date or (self.start_date <= file_date <= self.end_date):
                self.download_file(file['id'], local_path)
        except ValueError:
            logging.error(f"Error parsing date from filename: {file['name']}")


    def check_folder_recursive(self, file_id, file_path):
        """
        Check and process contents of a folder recursively.

        Args:
            folder_id (str): The ID of the folder to check.
            local_folder_path (str): The local path to save any files.
        """
        query = f"'{file_id}' in parents"
        files = self.query_files(query)
    
        for file in files:
            local_path = os.path.join(file_path, file['name'])
            if file['mimeType'] == 'application/vnd.google-apps.folder': # if this is a folder
                self.process_folder(file, local_path)
            elif file['mimeType'] == 'text/plain':  # if it's a txt file
                self.process_file(file, local_path)


if __name__ == "__main__":
    try:
        config = load_config()

        CLIENT_SECRET_FILE = config["CLIENT_SECRET_FILE"]
        API_NAME = config["API_NAME"]
        API_VERSION = config["API_VERSION"]
        SCOPES = config["SCOPES"]
        service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

        root_folder_id = '1ax1XeSBXbKyXQKIrf2qGjw7_scvYQqBs'
        CCNV = SmartScrapper(service, root_folder_id, start_date='2023-01-01', end_date='2023-01-05')
        CCNV.check_folder_recursive(root_folder_id, CCNV.root_folder_path)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        exit(1)
    

