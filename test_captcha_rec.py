'''

Created on Dec 24, 2016
@author: Yvictor

'''
from tpex import tpexBSreport
bsreport = tpexBSreport()
img, ans = bsreport.OCR()
print(ans)