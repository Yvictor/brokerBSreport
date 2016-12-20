'''
Created on Dec 18, 2016
@author: Yvictor
'''

import requests
import pandas as pd


def _get_twse_stock_id():
    print('Get StockId List')
    res = requests.get('http://isin.twse.com.tw/isin/C_public.jsp?strMode=2')
    twse_no = pd.read_html(res.text, header=0)[0]
    twse_no = twse_no[twse_no['CFICode']=='ESVUFR']
    return twse_no.iloc[:, 0].map(lambda x: x.split(' ')[0].split('\u3000')[0]).tolist()

if __name__ == '__main__':
    _get_twse_stock_id()