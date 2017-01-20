'''

Created on Dec 22, 2016
@author: Yvictor

'''
import io
import os
import re
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

from . import _get_tpex_stock_id, captcha_recognize
from utils import func_logging

def _get_session():
    session = requests.session()
    headers = {
        "user-agent": "mozilla/5.0 (x11; linux x86_64) applewebkit/537.36 "
                      "(khtml, like gecko) "
                      "chrome/46.0.2490.86 safari/537.36"}
    session.headers.update(headers)
    return session

@func_logging(False)
def _getint(x):
    if type(x) == str:
        return float(('').join(x.split(',')))
    else:
        return float(x)

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


class tpexBSreport:
    def __init__(self):
        self.rs = _get_session()
        self.curpath = os.environ.get('CusPath', '')
        self.set_sleep = float(os.environ.get('SLP', 1))
        self.datenow = self.__getdate()
        self.sentry_client = Client('https://6434c22a9d784459938a63e12ff0ae93:f85135cdee9242faa7560a1e9c56ece3@sentry.io/124308')
        self.notradedata = []  # new
        self.originh5 = False
        self.sorth5 = False
        self.ori_name = 'tpex_origin_%s.h5'
        self.sort_name = 'tpex_sort.h5'
        self.stockidL = _get_tpex_stock_id()
        self.ori_file_name = self.curpath + self.ori_name % ('').join(str(self.datenow).split('-'))
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
        sleeptime = 30
        captcha = None
        while str(captcha) != '<Response [200]>':
            try:
                res = self.rs.get('http://www.tpex.org.tw/web/stock/aftertrading/broker_trading/brokerBS.php')
                res.encoding = 'utf-8'
                soup = BS(res.text, "lxml")
                enname = soup.select('.form-inline input')[0].attrs['value']
                captcha = self.rs.get('http://www.tpex.org.tw/web/inc/authnum_output.php?n=%s'%enname, verify=False)#,stream=True
            except:
                if sleeptime>300 and sleeptime< 999:
                    self.sentry_client.captureMessage("IP was baned, SLP setting: %s"%str(self.set_sleep), data={'level': 'warn'})
                time.sleep(sleeptime)
                sleeptime+=300
        return captcha.content, enname

    @func_logging(False)
    def OCR(self):
        capt = self.getCaptcha()
        captcha_img = Image.open(io.BytesIO(capt[0]))
        return captcha_img, self.captcha_rec.captcha_predict(self.captcha_rec.preprocess(captcha_img)), capt[1]

    @func_logging(False)
    def postpayload(self, stockid, captcha, urltype):
        payload = {
            'enname' : captcha[2],
            'stk_code': '%s' % str(stockid),
            'auth_num': captcha[1]
        }
        res = self.rs.post('http://www.tpex.org.tw/web/stock/aftertrading/broker_trading/brokerBS.php', data=payload)
        res.encoding = 'utf-8'
        soup = BS(res.text, "lxml")
        self.answ = soup.select('.pt10')[0].text
        if self.answ == '\n ***驗證碼錯誤，請重新查詢。*** \n':
            correctanswer = 0
            if os.path.exists('error_captcha/tpex'):
                captcha[0].save('error_captcha/tpex/%s.png'%captcha[1], format='png')
            else:
                os.makedirs('error_captcha/tpex')
                captcha[0].save('error_captcha/tpex/%s.png' % captcha[1], format='png')
        elif self.answ == '\n ***驗證碼過期，請重新查詢。*** \n':
            correctanswer = 0
        elif self.answ == '\n ***該股票該日無交易資訊*** \n':
            return 2
        elif self.answ[0:7] == '\n\n\n交易日期':
            correctanswer = 1
            self.ind = pd.read_html(str(soup.select('.table-striped')[0]))[0]
            self.dtda = re.sub('[^0-9]', '/', self.ind[1][0]).split('/')[0:3]
            stkd = ('').join(self.dtda)
            urlbig5 = 'http://www.tpex.org.tw/web/stock/aftertrading/broker_trading/download_ALLCSV.php?curstk='
            urlutf8 = 'http://www.tpex.org.tw/web/stock/aftertrading/broker_trading/download_ALLCSV_UTF-8.php?curstk='
            if urltype == 5:
                url = urlbig5 + str(stockid) + '&stk_date=' + stkd + '&auth=' + captcha[1] + '&n=' + captcha[2]
            elif urltype == 8:
                url = urlutf8 + str(stockid) + '&stk_date=' + stkd + '&auth=' + captcha[1] + '&n=' + captcha[2]
            self.csvf = self.rs.get(url, verify=False)#, stream=True
        elif self.answ == '\n ***因當日最新資訊匯入資料庫，15:30至15:35暫停券商買賣股票資訊查詢*** \n':
            time.sleep(1000)
        else:
            correctanswer = 2
            self.sentry_client.captureMessage(self.answ)
        return correctanswer

    @func_logging(False)
    def _process_ori_data(self, stockid):
        dat = date(int(self.dtda[0])+1911,int(self.dtda[1]),int(self.dtda[2]))
        tda = int(self.ind[1][1])
        ap = int(re.sub('[^0-9]','',self.ind[3][1]))
        allshare = self.ind[5][1]
        rt_ratio = self.ind[7][1]
        op = float(self.ind[1][2])
        hp = float(self.ind[3][2])
        lp = float(self.ind[5][2])
        cp = float(self.ind[7][2])
        d = {"日期":dat,
             "代號":stockid,
             "成交筆數":tda,
             "總成交金額":ap,
             "總成交股數":allshare,
             "周轉率(%)":rt_ratio,
             "開盤價":op,
             "最高價":hp,
             "最低價":lp,
             "收盤價":cp}
        ind = pd.DataFrame(d, index=[1])
        ind.index.name = '序號'
        tablens = pd.read_csv(io.StringIO(self.csvf.text.split('證券代碼')[1][7:]),encoding='utf-8')
        table00 = tablens[['序號','券商','價格','買進股數','賣出股數']]
        table01 = tablens[['序號.1','券商.1','價格.1','買進股數.1','賣出股數.1']]
        table00.columns = ['序號','證券商','成交單價','買進股數','賣出股數']
        table01.columns = ['序號','證券商','成交單價','買進股數','賣出股數']
        frame00 = [table00,table01]
        table = pd.concat(frame00)
        table = table.set_index('序號')
        table = table.dropna()
        table = table.sort_index()
        table.index.name = '序'
        table['買進股數'] = table['買進股數'].map(lambda x: _getint(x))
        table['賣出股數'] = table['賣出股數'].map(lambda x: _getint(x))
        table['成交單價'] = table['成交單價'].map(lambda x: _getint(x))
        table = table.join(ind)
        table[["日期","代號","成交筆數","總成交金額","總成交股數","周轉率(%)","開盤價","最高價","最低價","收盤價"]] = table[["日期","代號","成交筆數","總成交金額","總成交股數","周轉率(%)","開盤價","最高價","最低價","收盤價"]].fillna(method='pad')
        table = table[["日期","代號","成交筆數","總成交金額","總成交股數","周轉率(%)","開盤價","最高價","最低價","收盤價","證券商","成交單價","買進股數","賣出股數"]]
        table['日期'] = pd.to_datetime(table['日期'])
        table['證券商']=table['證券商'].map(lambda x: str(x).split(' ')[0])
        table['代號'] = table['代號'].map(lambda x:str(int(x)))

        self.ori_file_name = self.curpath+ self.ori_name %('').join(str(dat).split('-'))
        return table

    @func_logging(False)
    def _process_sort_data(self, table):
        buyp = table.apply(lambda row: row['成交單價'] * row['買進股數'], axis=1)
        table.insert(13, '買進金額', buyp)
        sellp = table.apply(lambda row: row['成交單價'] * row['賣出股數'], axis=1)
        table.insert(14, '賣出金額', sellp)
        table_sort = table.groupby(["日期", "代號", "成交筆數", "總成交金額", "總成交股數", "周轉率(%)", "開盤價", "最高價", "最低價", "收盤價", "證券商"])[
            ['買進股數', '賣出股數', '買進金額', '賣出金額']].sum()
        table_sort = table_sort.reset_index(["成交筆數", "總成交金額", "總成交股數", "周轉率(%)", "開盤價", "最高價", "最低價", "收盤價"])
        table_sort = table_sort[
            ['買進股數', '賣出股數', '買進金額', '賣出金額', "成交筆數", "總成交金額", "總成交股數", "周轉率(%)", "開盤價", "最高價", "最低價", "收盤價"]]
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
        return table_sort

    @func_logging(False)
    def processdata(self,stockid):
        table = self._process_ori_data(stockid)

        table_sort = self._process_sort_data(table).astype(np.float64)

        table.to_hdf(self.ori_file_name,
                     key = str(stockid), format = 'table',
                     append = True, complevel = 9, complib = 'zlib')

        file_path = self.curpath+ self.sort_name
        if os.path.exists(file_path):
            if self.sorth5==False:
                self.sorth5 = pd.HDFStore(file_path)
            elif not self.sorth5.is_open:
                self.sorth5 = pd.HDFStore(file_path)

            if self.sorth5.is_open and str(stockid) in self.sorth5:
                if table_sort.index.levels[0] not in self.sorth5[str(stockid)].index.levels[0]:
                    table_sort.to_hdf(file_path, key=str(stockid), format='table',
                                        append=True, complevel=9, complib='zlib')
            elif self.sorth5.is_open and str(stockid) not in self.sorth5:
                table_sort.to_hdf(file_path, key=str(stockid), format='table',
                                    append=True, complevel=9, complib='zlib')
        else:
            table_sort.to_hdf(file_path, key=str(stockid), format='table',
                                append=True, complevel=9, complib='zlib')

    @func_logging(False)
    def post_process(self, stockid, anscor=0, repostcount=0, changeurltype=0):
        while anscor == 0:
            if changeurltype == 0:
                urltype = 5
            elif changeurltype == 1:
                urltype = 8
            Capt = [None, '']
            while len(Capt[1]) != 5:
                try:
                    Capt = self.OCR()
                except Exception as e:
                    self.sentry_client.captureMessage("TPEX Captcha occur error \n %s"%str(e))
            anscor = self.postpayload(stockid, Capt, urltype)
            returnstat(stockid, repostcount)
            repostcount += 1
            if anscor == 2:
                self.notradedata.append(stockid)
                break
            if repostcount > 10:
                repostcount = 150
                time.sleep(random.choice([2.8, 3.2, 3.8, 4.1, 4.7])/self.set_sleep)
                break
            time.sleep(random.choice([1.3, 2.2 ,2.7, 3.1, 3.8])/self.set_sleep)
            while anscor == 1 and int(self.dtda[0]) < 85:
                anscor = self.postpayload(stockid, Capt, urltype)
                time.sleep(random.choice([1.3, 1.8, 1.4, 1.1, 1.5])/self.set_sleep)
            if anscor == 1 and int(self.dtda[0]) > 85:
                try:
                    self._process_ori_data(stockid)
                    changeurltype = 0
                except Exception as e:
                    changeurltype = 1
                    anscor = 0
                    self.sentry_client.captureMessage("TPEX Process Data Occur Error \n %s" % str(e))
                    continue
                self.processdata(stockid)
        return repostcount

    @func_logging(False)
    def singleprocess(self, stockid):
        filepath = self.curpath + self.ori_name % ('').join(str(self.__getdate()).split('-'))
        if os.path.exists(filepath):
            if self.originh5 == False:
                self.originh5 = pd.HDFStore(filepath)
            elif not self.originh5.is_open:
                self.originh5 = pd.HDFStore(filepath)
            if str(stockid) not in self.originh5:
                repostcount = self.post_process(stockid)
            else:
                repostcount = 100
        else:
            repostcount = self.post_process(stockid)
        return stockid, repostcount

    @func_logging(False)
    def processAll(self):
        starttime = datetime.now()
        stlen = len(self.stockidL)
        self.arrcu = []
        for i in range(stlen):
            a = self.singleprocess(self.stockidL[i])
            if a[1]==150:
                time.sleep(650)
                a = self.singleprocess(self.stockidL[i])
            ptime = datetime.now()
            text = "\r上櫃 {0}/{1} 已完成 {2}%  處理時間: {3}".format(i+1,stlen,round((i+1)/stlen,4)*100,str(ptime-starttime))
            sys.stdout.write(text)
            sys.stdout.flush()
            if i%200==0:
                self.sentry_client.captureMessage("上櫃 {0}/{1} 已完成 {2}%  處理時間: {3}".format(i+1,stlen,round((i+1)/stlen,4)*100,str(ptime-starttime)),
                                                  data = {'level': 'info'})
            self.arrcu.append(a)
            if self.arrcu[-1][1] == 0:
                time.sleep(3/self.set_sleep)
            if len(self.arrcu)>3 and self.arrcu[-1][1] <= 1 and self.arrcu[-2][1] <= 1 and self.arrcu[-3][1] <= 1:
                time.sleep(5/self.set_sleep)
        endtime = datetime.now()
        spendt = str(endtime - starttime)
        try:
            self.originh5.close()
            self.sorth5.close()
        except:
            pass
        print("上櫃股票交易日報下載完成 \n 花費時間:{0}".format(spendt))
        self.sentry_client.captureMessage("上櫃股票交易日報下載完成 \n 花費時間:{0}".format(spendt), data = {'level': 'info'})
        return self.ori_file_name

