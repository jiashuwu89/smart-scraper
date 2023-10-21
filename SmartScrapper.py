import os
import io
from googleapiclient.http import MediaIoBaseDownload
import json
import logging
from Google import Create_Service

logging.basicConfig(level=logging.INFO)

def load_config(config_path="config.json"):
    with open(config_path, "r") as f:
        return json.load(f)
    
class SmartScrapper():
    def __init__(self, service, root_folder_id):
        self.service = service
        request = self.service.files().get(fileId=root_folder_id).execute()
        os.makedirs(request['name'], exist_ok=True)
        self.root_folder_path = request['name']
        
 
    def download_file(self, file_id, outfile):
        """
        Download a file from Google Drive.

        Args:
            file_id (str): The ID of the file to download.
            outfile (str): The path to save the downloaded file.
        """
        request = self.service.files().get_media(fileId=file_id)

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fd=fh, request=request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print('Download progress {0}'.format(status.progress() * 100))
        fh.seek(0)
        with open(outfile, 'wb') as f:
            f.write(fh.read())
        f.close()


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


    def check_folder_recursive(self, file_id, file_path):
        """
        Check and process contents of a folder recursively.

        Args:
            folder_id (str): The ID of the folder to check.
            local_folder_path (str): The local path to save any files.
        """
        files = []
        query = f"'{file_id}' in parents"
        files = self.query_files(query)
    
        for file in files:
            local_path = os.path.join(file_path, file['name'])
            if file['mimeType'] == 'application/vnd.google-apps.folder': # if this is a folder
                os.makedirs(local_path, exist_ok=True)
                # recursive call for subfolder
                self.check_folder_recursive(file['id'], local_path)
            elif file['mimeType'] == 'text/plain':  # if it's a txt file
                self.download_file(file['id'], local_path)


if __name__ == "__main__":
    config = load_config()

    CLIENT_SECRET_FILE = config["CLIENT_SECRET_FILE"]
    API_NAME = config["API_NAME"]
    API_VERSION = config["API_VERSION"]
    SCOPES = config["SCOPES"]
    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

    root_folder_id = '1ax1XeSBXbKyXQKIrf2qGjw7_scvYQqBs'
    CCNV = SmartScrapper(service, root_folder_id)
    CCNV.check_folder_recursive(root_folder_id, CCNV.root_folder_path)
    

