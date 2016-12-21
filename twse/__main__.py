'''

Created on Dec 18, 2016
@author: Yvictor

'''
import os
from twse import twseBSreport
from utils import gdrive

bsreporter = twseBSreport()
file_name = bsreporter.processAll()

backup = gdrive()
origin_folder_id = os.environ.get("TWSE_ORIGIN_FOLDER", '0Bxlih4lHCRlmeTRCUkFpd2hkcm8')
gdrive.upload_file(file_path=file_name, folder_id=origin_folder_id)
