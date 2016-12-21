'''

Created on Dec 18, 2016
@author: Yvictor

'''
import sys
import httplib2
from mimetypes import guess_type
import os

from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from apiclient.errors import ResumableUploadError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage

from utils import func_logging

class gdrive:
    def __init__(self):
        self.token_file = sys.path[0] + 'auth_token.h5'
        self.CLIENT_ID = os.environ.get('CLIENT_ID','927735876995-rumfh557885us86uln2oap916r9cbpe0.apps.googleusercontent.com')
        self.CLIENT_SECRET = os.environ.get('CLIENT_SECRET','aHqC0LnYwJl9Fwm6uMshJ88W')
        self.OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive.file'
        self.REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
        self.storage = None
        try:
            with open(self.token_file) as f: pass
            self.http = self._authorize()
        except IOError:
            self.storage = self._create_token_file()
            self.http = self._authorize()

    @func_logging(False)
    def _create_token_file(self):
        flow = OAuth2WebServerFlow(
            self.CLIENT_ID,
            self.CLIENT_SECRET,
            self.OAUTH_SCOPE,
            redirect_uri=self.REDIRECT_URI
            )
        authorize_url = flow.step1_get_authorize_url()
        print('Go to the following link in your browser: ' + authorize_url)
        code = input('Enter verification code: ').strip()
        credentials = flow.step2_exchange(code)
        storage = Storage(self.token_file)
        storage.put(credentials)
        return storage

    @func_logging(False)
    def _authorize(self):
        if self.storage is None:
            self.storage = Storage(self.token_file)
        credentials = self.storage.get()
        http = httplib2.Http()
        credentials.refresh(http)
        http = credentials.authorize(http)
        return http

    @func_logging(False)
    def _file_ops(self, file_path):
        mime_type = guess_type(file_path)[0]
        mime_type = mime_type if mime_type else 'text/plain'
        file_name = file_path.split('/')[-1]
        return file_name, mime_type

    @func_logging(False)
    def _upload_file(self, file_path, folder_id=''):
        drive_service = build('drive', 'v2', http=self.http)
        file_name, mime_type = self.file_ops(file_path)
        media_body = MediaFileUpload(file_path,
                                     mimetype=mime_type,
                                     resumable=True)
        body = {
            'title': file_name,
            'description': 'backup',
            'mimeType': mime_type,
        }
        if folder_id != '':
            body['parents'] = [{'id': folder_id}]
        file = drive_service.files().insert(body=body, media_body=media_body).execute()
        return file['id']

    @func_logging(False)
    def upload_file(self, file_path, folder_id=''):
        try:
            file_id = self._upload_file(file_path, folder_id)
            print('file id : %s'%file_id)
        except ResumableUploadError as e:
            print("Error occured while first upload try:", e)

    def upload_remove_file(self):
        pass

    def download_file(self):
        pass

    def sync_file(self):
        pass

    def remove_file(self):
        pass

