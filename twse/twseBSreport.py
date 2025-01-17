'''

Created on Dec 18, 2016
@author: Yvictor

'''

import io
import os
import sys
import time
import random
import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup as BS
from datetime import datetime, date, timedelta
from PIL import Image
from raven import Client
import warnings
import tables
warnings.filterwarnings('ignore', category=tables.NaturalNameWarning)

from . import _get_twse_stock_id, captcha_recognize
from utils import func_logging

#FIXED_D = False

def _get_session():
    session = requests.session()
    headers = {
        "user-agent": "mozilla/5.0 (x11; linux x86_64) applewebkit/537.36 "
                      "(khtml, like gecko) "
                      "chrome/46.0.2490.86 safari/537.36"}
    session.headers.update(headers)
    return session
@func_logging(False)
def _transdate(l):
    l = l.split('/')
    return date(int(l[0]),int(l[1]),int(l[2]))
@func_logging(False)
def _transnum(l):
    return float(('').join(l.split(',')))
@func_logging(False)
def _divexpectz(a,b):
    if b == 0:
        return 0
    else:
        return round(a/b,2)
def returnstat(id0,reposttime):
    text = "\r {0}重新取得驗證碼次數:{1}".format(id0,reposttime)
    sys.stdout.write(text)
    sys.stdout.flush()



class twseBSreport:
    def __init__(self):
        self.urltwse = 'http://bsr.twse.com.tw/bshtm/'
        self.rs = _get_session()
        self.curpath = os.environ.get('CusPath', '')
        self.set_sleep = float(os.environ.get('SLP', 1))
        self.datenow = self.__getdate()
        self.sentry_client = Client('https://6db9585c13094fe0a6daf59ba35bf0f1:398fc0f8893c41f2829102661ddc00f6@sentry.io/123315')
        self.notradedata = []  # new
        self.originh5 = False
        self.sorth5 = False
        self.ori_file_name = self.curpath + 'twse_origin_%s.h5' % ('').join(str(self.datenow).split('-'))
        self.stockidL = _get_twse_stock_id()
        self.captcha_rec = captcha_recognize()

    def __getdate(self):
        d = datetime.now()
        if d.hour < 16:
            d = d.date() - timedelta(1)
        if type(d) != type(date.today()):
            d = d.date()
        if d.isoweekday() == 7:
            d = d - timedelta(2)
        elif d.isoweekday() == 6:
            if os.environ.get('FIXED_D', False)==False:
                d = d - timedelta(1)
        return d

    @func_logging(False)
    def getCaptcha(self):
        r1 = self.rs.get('http://bsr.twse.com.tw/bshtm/bsMenu.aspx')
        r1.encoding = 'utf-8'
        soup = BS(r1.text, 'lxml')
        guid = soup.findAll('img')[1].attrs['src']
        self.VIEWSTATE = soup.select('#__VIEWSTATE')[0].attrs['value']
        self.EVENTVALIDATION = soup.select('#__EVENTVALIDATION')[0].attrs['value']
        captcha = self.rs.get('http://bsr.twse.com.tw/bshtm/%s' % guid, stream=True, verify=False)
        return captcha.content

    @func_logging(False)
    def OCR(self):
        image_array = Image.open(io.BytesIO(self.getCaptcha()))
        return self.captcha_rec.captcha_predict(self.captcha_rec.preprocess(image_array))

    @func_logging(False)
    def postpayload(self, stock_id, captcha, sleeptime):
        payload = {'__EVENTTARGET': '',
                   '__EVENTARGUMENT': '',
                   '__LASTFOCUS': '',
                   '__VIEWSTATE': '%s' % self.VIEWSTATE,
                   '__EVENTVALIDATION': '%s' % self.EVENTVALIDATION,
                   'RadioButton_Normal': 'RadioButton_Normal',
                   'TextBox_Stkno': '%s' % str(stock_id),
                   'CaptchaControl1': '%s' % captcha,
                   'btnOK': '查詢'}
        resp = self.rs.post('http://bsr.twse.com.tw/bshtm/bsMenu.aspx', data=payload)
        checkans = BS(resp.text, 'lxml')
        self.answ = checkans.select('.radio')[3].text
        correctanswer = 0
        if self.answ == '':
            correctanswer = 1
            resq = self.rs.get('http://bsr.twse.com.tw/bshtm/bsContent.aspx?v=t')
            self.soupdata = BS(resq.text, "lxml")
        elif self.answ == '驗證碼錯誤!' or self.answ == '驗證碼已逾期.':
            correctanswer = 0
            time.sleep(sleeptime/self.set_sleep)
        elif self.answ == '查無資料':
            correctanswer = 2
        else:
            correctanswer = 2
            time.sleep(sleeptime/self.set_sleep)
            self.sentry_client.captureMessage(str(checkans))
        return correctanswer

    @func_logging(False)
    def _process_ori(self, stock_id):
        dat = _transdate(self.soupdata.select('#receive_date')[0].text.strip('\r\n '))
        tda = _transnum(self.soupdata.select('#trade_rec')[0].text.strip('\r\n '))
        ap = _transnum(self.soupdata.select('#trade_amt')[0].text.strip('\r\n '))
        allshare = _transnum(self.soupdata.select('#trade_qty')[0].text.strip('\r\n '))
        op = _transnum(self.soupdata.select('#open_price')[0].text.strip('\r\n '))
        hp = _transnum(self.soupdata.select('#high_price')[0].text.strip('\r\n '))
        lp = _transnum(self.soupdata.select('#low_price')[0].text.strip('\r\n '))
        cp = _transnum(self.soupdata.select('#last_price')[0].text.strip('\r\n '))
        d = {"日期":dat,"代號":stock_id,"成交筆數":tda,"總成交金額":ap,"總成交股數":allshare,
            "開盤價":op,"最高價":hp,"最低價":lp,"收盤價":cp}
        ind = pd.DataFrame(d, index=[1])
        ind.index.name = '序'
        dlist = pd.read_html(str(self.soupdata.select('#table2 table')), header=0, index_col=0)
        table = pd.concat(dlist)
        table = table.dropna()
        table = table.join(ind)
        table[["日期","代號","成交筆數","總成交金額","總成交股數","開盤價","最高價","最低價","收盤價"]] = table[["日期","代號","成交筆數","總成交金額","總成交股數","開盤價","最高價","最低價","收盤價"]].fillna(method='pad')
        table = table[["日期","代號","成交筆數","總成交金額","總成交股數","開盤價","最高價","最低價","收盤價","證券商","成交單價","買進股數","賣出股數"]]
        table = table.sort_index()
        table['證券商']=table['證券商'].map(lambda x: str(x)[0:4])
        table['代號'] = table['代號'].map(lambda x:str(int(x)))
        table['日期'] = pd.to_datetime(table['日期'])
        self.ori_file_name = self.curpath+'twse_origin_%s.h5'%('').join(str(dat).split('-'))
        table.to_hdf(self.ori_file_name,
                     key = str(stock_id), format = 'table',
                     append = True, complevel = 9, complib = 'zlib')
        return table

    @func_logging(False)
    def processdata(self, stock_id):
        table = self._process_ori(stock_id)

        buyp = table.apply(lambda row: row['成交單價'] * row['買進股數'], axis=1)
        table.insert(13, '買進金額', buyp)
        sellp = table.apply(lambda row: row['成交單價'] * row['賣出股數'], axis=1)
        table.insert(14, '賣出金額', sellp)
        table_sort = table.groupby(["日期", "代號", "成交筆數", "總成交金額", "總成交股數", "開盤價", "最高價", "最低價", "收盤價", "證券商"])[
            ['買進股數', '賣出股數', '買進金額', '賣出金額']].sum()
        table_sort = table_sort.reset_index(["成交筆數", "總成交金額", "總成交股數", "開盤價", "最高價", "最低價", "收盤價"])
        table_sort = table_sort[['買進股數', '賣出股數', '買進金額', '賣出金額', "成交筆數", "總成交金額", "總成交股數", "開盤價", "最高價", "最低價", "收盤價"]]
        b_avg_p = table_sort.apply(lambda row: _divexpectz(row['買進金額'], row['買進股數']), axis=1)
        s_avg_p = table_sort.apply(lambda row: _divexpectz(row['賣出金額'], row['賣出股數']), axis=1)

        b_ratio = table_sort.apply(lambda row: _divexpectz(row['買進股數'], row['總成交股數']) * 100, axis=1)
        s_ratio = table_sort.apply(lambda row: _divexpectz(row['賣出股數'], row['總成交股數']) * 100, axis=1)

        bs_share_net = table_sort.apply(lambda row: row['買進股數'] - row['賣出股數'], axis=1)
        bs_price_net = table_sort.apply(lambda row: row['買進金額'] - row['賣出金額'], axis=1)
        table_sort.insert(2, '買賣超股數', bs_share_net)
        table_sort.insert(5, '買賣超金額', bs_price_net)
        table_sort.insert(6, '買進均價', b_avg_p)
        table_sort.insert(7, '賣出均價', s_avg_p)
        table_sort.insert(8, '買進比重', b_ratio)
        table_sort.insert(9, '賣出比重', s_ratio)
        table_sort = table_sort.astype(np.float64)
        file_path = self.curpath+'sort.h5'
        if os.path.exists(file_path):
            if self.sorth5==False:
                self.sorth5 = pd.HDFStore(file_path)
            elif not self.sorth5.is_open:
                self.sorth5 = pd.HDFStore(file_path)

            if self.sorth5.is_open and str(stock_id) in self.sorth5:
                if table_sort.index.levels[0] not in pd.read_hdf(file_path, key=str(stock_id)).index.levels[0]:
                    table_sort.to_hdf(file_path, key=str(stock_id), format='table',
                                        append=True, complevel=9, complib='zlib')
            elif self.sorth5.is_open and str(stock_id) not in self.sorth5:
                table_sort.to_hdf(file_path, key=str(stock_id), format='table',
                                    append=True, complevel=9, complib='zlib')
        else:
            table_sort.to_hdf(file_path, key=str(stock_id), format='table',
                                append=True, complevel=9, complib='zlib')

    @func_logging(False)
    def post_process(self, stockid, anscor, repostcount):
        while anscor == 0:
            Capt = ''
            while len(Capt) != 5:
                try:
                    Capt = self.OCR()
                except Exception as e:
                    self.sentry_client.captureMessage("TWSE Captcha occur error \n %s" % str(e))
            anscor = self.postpayload(stockid, Capt, sleeptime=5)
            returnstat(stockid, repostcount)
            repostcount += 1
            if anscor == 2:
                self.notradedata.append(stockid)
                break
            if repostcount > 150:
                repostcount = 150
                break
            time.sleep(random.choice([2.8, 3.2, 3.8, 4.1, 4.7])/self.set_sleep)
            if anscor == 1:
                self.processdata(stockid)
        return anscor, repostcount

    @func_logging(False)
    def singleprocess(self, stockid):
        anscor = 0
        repostcount = 0
        filepath = self.curpath+'twse_origin_%s.h5'%('').join(str(self.__getdate()).split('-'))
        if os.path.exists(filepath):
            if self.originh5==False:
                self.originh5 = pd.HDFStore(filepath)
            elif not self.originh5.is_open:
                self.originh5 = pd.HDFStore(filepath)
            if str(stockid) not in self.originh5:
                anscor, repostcount = self.post_process(stockid, anscor, repostcount)
            else:
                repostcount = 100
        else:
            anscor, repostcount = self.post_process(stockid, anscor, repostcount)
        return stockid, repostcount

    @func_logging(False)
    def processAll(self):
        starttime = datetime.now()
        stlen = len(self.stockidL)
        self.arrcu = []
        for i in range(stlen):
            a = self.singleprocess(self.stockidL[i])
            if a[1]==150:
                a = self.singleprocess(self.stockidL[i])
            ptime = datetime.now()
            text = "\r上市 {0}/{1} 已完成 {2}%  處理時間: {3}".format(i+1,stlen,round((i+1)/stlen,4)*100,str(ptime-starttime))
            sys.stdout.write(text)
            sys.stdout.flush()
            if i%200==0:
                self.sentry_client.captureMessage("上市 {0}/{1} 已完成 {2}%  處理時間: {3}".format(i+1,stlen,round((i+1)/stlen,4)*100,str(ptime-starttime)),
                                                  data={'level': 'info'})
            self.arrcu.append(a)
            if self.arrcu[-1][1] == 0:
                time.sleep(3/self.set_sleep)
            if len(self.arrcu)>3 and self.arrcu[-1][1] == 1 and self.arrcu[-2][1] == 1 and self.arrcu[-3][1] == 1:
                time.sleep(5/self.set_sleep)
        endtime = datetime.now()
        spendt = str(endtime - starttime)
        try:
            self.sorth5.close()
            self.originh5.close()
        except:
            pass
        print("上市股票交易日報下載完成 \n 花費時間:{0}".format(spendt))
        self.sentry_client.captureMessage("上市股票交易日報下載完成 \n 花費時間:{0}".format(spendt), data = {'level': 'info'})
        return self.ori_file_name

class convert_data:

    def sort_origin_table(self, table):
        buyp = table.apply(lambda row: row['成交單價'] * row['買進股數'], axis=1)
        table.insert(13, '買進金額', buyp)
        sellp = table.apply(lambda row: row['成交單價'] * row['賣出股數'], axis=1)
        table.insert(14, '賣出金額', sellp)
        table_sort = table.groupby(["日期", "代號", "成交筆數", "總成交金額", "總成交股數", "開盤價", "最高價", "最低價", "收盤價", "證券商"])[
            ['買進股數', '賣出股數', '買進金額', '賣出金額']].sum()
        table_sort = table_sort.reset_index(["成交筆數", "總成交金額", "總成交股數", "開盤價", "最高價", "最低價", "收盤價"])
        table_sort = table_sort[['買進股數', '賣出股數', '買進金額', '賣出金額', "成交筆數", "總成交金額", "總成交股數", "開盤價", "最高價", "最低價", "收盤價"]]
        b_avg_p = table_sort.apply(lambda row: _divexpectz(row['買進金額'], row['買進股數']), axis=1)
        s_avg_p = table_sort.apply(lambda row: _divexpectz(row['賣出金額'], row['賣出股數']), axis=1)

        b_ratio = table_sort.apply(lambda row: _divexpectz(row['買進股數'], row['總成交股數']) * 100, axis=1)
        s_ratio = table_sort.apply(lambda row: _divexpectz(row['賣出股數'], row['總成交股數']) * 100, axis=1)

        bs_share_net = table_sort.apply(lambda row: row['買進股數'] - row['賣出股數'], axis=1)
        bs_price_net = table_sort.apply(lambda row: row['買進金額'] - row['賣出金額'], axis=1)
        table_sort.insert(2, '買賣超股數', bs_share_net)
        table_sort.insert(5, '買賣超金額', bs_price_net)
        table_sort.insert(6, '買進均價', b_avg_p)
        table_sort.insert(7, '賣出均價', s_avg_p)
        table_sort.insert(8, '買進比重', b_ratio)
        table_sort.insert(9, '賣出比重', s_ratio)
        table_sort = table_sort.astype(np.float64)
        table_sort = table_sort.reset_index(['日期', '證券商', '代號'])
        table_sort['代號'] = table_sort['代號'].map(lambda x: str(int(x)))
        table_sort = table_sort.set_index(['日期','代號','證券商'])
        table_sort = table_sort.astype(np.float64)
        return table_sort






