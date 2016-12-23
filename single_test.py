'''

Created on Dec 24, 2016
@author: Yvictor

'''
import random
from twse import twseBSreport
from tpex import tpexBSreport

twsebsreport = twseBSreport()
print(twsebsreport.OCR())
twse_result = 0
while twse_result==0 or twse_result==2:
    stock_id = random.choice(twsebsreport.stockidL)
    twse_result = twsebsreport.postpayload(stock_id, twsebsreport.OCR(), sleeptime=5)
print(twsebsreport.singleprocess(stock_id))

tpexbsreport = tpexBSreport()
print(tpexbsreport.OCR())
tpex_result = 0
while tpex_result==0 or tpex_result==2:
    stock_id = random.choice(tpexbsreport.stockidL)
    tpex_result = tpexbsreport.postpayload(stock_id, tpexbsreport.OCR(), urltype=5)
print(tpexbsreport.singleprocess(stock_id))

