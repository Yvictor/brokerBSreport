'''

Created on Dec 22, 2016
@author: Yvictor

'''
import os
from tpex import tpexBSreport
from utils import gdrive

bsreporter = tpexBSreport()
file_name = bsreporter.processAll()

backup = gdrive()
origin_folder_id = os.environ.get("TPEX_ORIGIN_FOLDER", '0Bxlih4lHCRlmd0hFVktsY0lrRzg')
backup.upload_file(file_path=file_name, folder_id=origin_folder_id)
