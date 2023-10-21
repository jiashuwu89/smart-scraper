import os
import io
from googleapiclient.http import MediaIoBaseDownload

from Google import Create_Service

CLIENT_SECRET_FILE =  'client_secret.json'
API_NAME = 'drive'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/drive']
OUTPUTPATH = 'output'
SERVICE = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

def download_file(file_id, outfile):
    """
    Download a file from Google Drive.

    Args:
        file_id (str): The ID of the file to download.
        outfile (str): The path to save the downloaded file.
    """
    request = SERVICE.files().get_media(fileId=file_id)

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


def query_files(query):
    """
    Query files from Google Drive based on a specific query.

    Args:
        query (str): The query string for file search.

    Returns:
        list: A list of file objects.
    """
    files = []
    response = SERVICE.files().list(q=query).execute()
    files.extend(response.get('files'))
    nextPageToken =  response.get('nextPageToken')
    while nextPageToken:
        response = SERVICE.files().list(q=query, pageToken=nextPageToken).execute()
        files.extend(response.get('files'))
    return files


def check_folder_recursive(root_folder_id, root_folder_path):
    """
    Check and process contents of a folder recursively.

    Args:
        folder_id (str): The ID of the folder to check.
        local_folder_path (str): The local path to save any files.
    """
    files = []
    query = f"'{root_folder_id}' in parents"
    files = query_files(query)
 
    for file in files:
        local_path = os.path.join(root_folder_path, file['name'])
        if file['mimeType'] == 'application/vnd.google-apps.folder': # if this is a folder
            os.makedirs(local_path, exist_ok=True)
            # recursive call for subfolder
            check_folder_recursive(file['id'], local_path)
        elif file['mimeType'] == 'text/plain':  # if it's a txt file
            download_file(file['id'], local_path)


if __name__ == "__main__":
    os.makedirs(OUTPUTPATH, exist_ok=True)
    root_folder_id = '1ax1XeSBXbKyXQKIrf2qGjw7_scvYQqBs'
    check_folder_recursive(root_folder_id, OUTPUTPATH)

