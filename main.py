import sys
import numpy as np
import pandas as pd
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QAxContainer import *
from datetime import datetime, timedelta
import ccxt # pip install ccxt # 가상화폐 거래소 모듈, 바이낸스 api 등 125개 거래소 지원
import math
import time
import os
from coin_invest.scalping_trading import scalping_trading_cls
from coin_invest_backtest.maxLine import maxLine_cls
from coin_invest_backtest.minLine import minLine_cls
from coin_invest_backtest.main_second import main_second_cls
from coin_invest_backtest.main_auto import main_auto_cls
import traceback

form_class = uic.loadUiType("coinbacktest.ui")[0]

class Thread1(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self): # 과거 기간별 데이터 가져오기
        try: 
            # 전역 변수 선언
            jongname = self.parent.comboBox_jongmok2.currentText()
            minit_arr = ['1m', '5m', '1h', '1d']
            
            for minit in minit_arr :
                if os.path.isfile('cointest/'+jongname[0:3]+'_'+minit+'.xlsx') :
                    print('이미 '+minit+' 데이터가 있습니다.')
                else :
                    # 코인시간 = 우리나라시간 - 9시 -> 아래 시간으로 조회시 9시간을 뺀시간으로 조회가 됨
                    start_time_bf = self.parent.dateTimeEdit_searchDate.text() # UI에서 시작시간 가져오기
                    end_time_bf = self.parent.dateTimeEdit_searchDate_2.text() # UI에서 끝시간 가져오기
                    ddtm_start = datetime.strptime(start_time_bf, '%Y-%m-%d %H:%M:%S') # 문자 -> time 형식으로 바꾸기
                    ddtm_end = datetime.strptime(end_time_bf, '%Y-%m-%d %H:%M:%S') # 문자 -> time 형식으로 바꾸기
                    start_time_bf = ddtm_start + timedelta(hours=9) # 코인시간으로 맞추기 위해 9시간 빼기
                    end_time_bf = ddtm_end + timedelta(hours=9) # 코인시간으로 맞추기 위해 9시간 빼기
                    
                    # 전부 시작일 전으로 300봉을 추가해주기
                    if minit == '1m' : 
                        ddtm_newstart = start_time_bf - timedelta(hours=5)
                        ddtm_newend = end_time_bf
                    elif minit == '5m' : 
                        ddtm_newstart = start_time_bf - timedelta(hours=25)
                        ddtm_newend = end_time_bf
                    elif minit == '1h' :
                        ddtm_newstart = start_time_bf - timedelta(hours=300)
                        ddtm_newend = end_time_bf
                    elif minit == '1d' :
                        ddtm_newstart = start_time_bf - timedelta(days=300)
                        ddtm_newend = end_time_bf
                    start_time = self.parent.to_mstimestamp(ddtm_newstart) # 가져올 데이터 시작일
                    end_time = self.parent.to_mstimestamp(ddtm_newend) # 가져올 데이터 종료일
                    
                    # 과거 ~ 현재일까지 데이터 가져오기
                    dataset = pd.DataFrame()
                    start_time_dd = ""
                    while True:
                        data = self.parent.data_ago(jongname, minit, start_time, end_time)
                        # 데이터 append 하기
                        dataset = dataset.append(data, sort=False)
                        # 중복 제거
                        dataset = dataset.drop_duplicates(['datetime'])
                        # 인덱스 초기화하기    
                        dataset = dataset.reset_index(drop=True)
                        # 오름차순 정렬하기
                        dataset = dataset.sort_values('datetime', ascending=True)
                        
                        if str(start_time_dd) == str(dataset.iloc[-1]['datetime']) :
                            break
                        
                        # 시작일자 변경
                        start_time_dd = dataset.iloc[-1]['datetime']
                        
                        start_time = self.parent.to_mstimestamp(str(start_time_dd))
                        
                        time.sleep(0.1)
                    
                    # 마지막행 -> 다음날 00:00:00 제거하기
                    dataset = dataset.drop(len(dataset)-1,axis=0)
                    
                    # 과거 데이터 저장하기
                    dataset.to_excel('cointest/'+jongname[0:3]+'_'+minit+'.xlsx', index=False)
            
        except Exception as e:
            print(e)
            
class MyWindow(QMainWindow, form_class):
    # 시작 시
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        # 전역변수선언
        self.df = pd.DataFrame() # 당일 5분 데이터 저장
        self.df_1m = pd.DataFrame() # 1분 데이터 저장
        self.df_5m = pd.DataFrame() # 5분 데이터 저장
        self.df_1h = pd.DataFrame() # 1시간 데이터 저장
        self.df_1d = pd.DataFrame() # 일봉 데이터 저장
        
        # 공식 문서 참고 : https://binance-docs.github.io/apidocs/spot/en/#change-log
        self.api_key = "KtWYCLBnXlBaebaVgpjWxQkOWNLiELFx1uVfX9zGdauCUjLrDvMvGYHcIkRyoBPp"
        self.secret  = "DHDGNE17mjL9gBKlKZyP5JOzoGr8u049BKYn8YjlauIeNsw23RmFMuIoHxCGf0JH"
        self.binance = ccxt.binance(config={
            'apiKey': self.api_key, 
            'secret': self.secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future'
            }
        })
        
        # 종목 콤보박스에 종목넣기
        self.comboBox_jongmok2.addItem('ETH/USDT')
        self.comboBox_jongmok2.addItem('BCH/USDT')
        self.comboBox_jongmok2.addItem('ETC/USDT')
        self.comboBox_jongmok2.addItem('EOS/USDT')
        self.comboBox_jongmok2.addItem('ADA/USDT')
        
        ##----------------------------------------------------------------------------##
        ## 버튼 클릭 시 함수와 연결 모음 ##
        self.pushButton_testStart.clicked.connect(self.pushButton_testStart_click) # 테스트시작 버튼
        self.push_start.clicked.connect(self.push_start_click) # 시작버튼
        
    ##----------------------------------------------------------------------------##                        
    ## --새창 열기 함수 모음-- ##
    # 수동일때 새창띄우기
    def open_newwindow(self, dataset, dateset_5m, dateset_1h, dateset_1m, dataset_1d):
        self.hide() # 메인 윈도우 숨김
        self.second = main_second_cls(dataset, dateset_5m, dateset_1h, dateset_1m, dataset_1d)
        self.second.exec()
        self.show()
    
    # 자동일때 새창띄우기
    def open_newwindow2(self, dataset, dateset_5m, dateset_1h, dateset_1m, dataset_1d):
        self.hide() # 메인 윈도우 숨김
        self.auto = main_auto_cls(dataset, dateset_5m, dateset_1h, dateset_1m, dataset_1d)
        self.auto.exec()
        self.show()
        
    ##----------------------------------------------------------------------------##
    ## 일반 함수 모음 ## 
    # 과거 데이터 조회
    def data_ago(self,jong,timef,start_time,end_time): 
        btc_ago = self.binance.fetch_ohlcv(
            symbol=jong, 
            timeframe=timef, 
            since=start_time, # 시작기간 = timestamp로 전달 
            params = {"endTime" : end_time},
            limit=1500)
        df = pd.DataFrame(btc_ago, columns=['datetime', 'open', 'high', 'low', 'close', 'volume']) # timestamp는 밀리초단위 시간임
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        return df
        
    # timestamp 만들기
    def to_mstimestamp(self, dd): 
        if type(dd) is str :
            trans_dd = datetime.strptime(dd, "%Y-%m-%d %H:%M:%S")
        else:
            trans_dd = dd
        trans_dd = datetime.timestamp(trans_dd)
        trans_dd = int(trans_dd) * 1000
        return trans_dd
    
    # 단순이동평균 구하기
    def make_avgline(self, df, send):
        if send == 'main' :
            avg_5 = df['close'].rolling(window=5).mean()
            avg_10 = df['close'].rolling(window=10).mean()
            avg_20 = df['close'].rolling(window=20).mean()
            avg_60 = df['close'].rolling(window=60).mean()
            avg_120 = df['close'].rolling(window=120).mean()
            avg_200 = df['close'].rolling(window=200).mean()
            avg_240 = df['close'].rolling(window=240).mean()
            return avg_5, avg_10, avg_20, avg_60, avg_120, avg_200, avg_240
        elif send == 'sub' :
            avg_60 = df['close'].rolling(window=60).mean()
            avg_120 = df['close'].rolling(window=120).mean()
            avg_240 = df['close'].rolling(window=240).mean()
            return avg_60, avg_120, avg_240
        
    # 지수이동평균 구하기
    def make_avgline2(self, df, send):
        if send == 'main' :
            avg_5 = df['close'].ewm(span=5, adjust=False).mean()
            avg_10 = df['close'].ewm(span=10, adjust=False).mean()
            avg_20 = df['close'].ewm(span=20, adjust=False).mean()
            avg_60 = df['close'].ewm(span=60, adjust=False).mean()
            avg_120 = df['close'].ewm(span=120, adjust=False).mean()
            avg_200 = df['close'].ewm(span=200, adjust=False).mean()
            avg_240 = df['close'].ewm(span=240, adjust=False).mean()
            return avg_5, avg_10, avg_20, avg_60, avg_120, avg_200, avg_240
        elif send == 'sub' : # 200일 이동평균선만
            avg_200 = df['close'].ewm(span=200, adjust=False).mean()
            return round(avg_200,2)
        
    # RSI 구하기
    def make_rsi(self, data1, period):
        U = np.where(data1['close'].diff(1) > 0, data1['close'].diff(1), 0)
        D = np.where(data1['close'].diff(1) < 0, data1['close'].diff(1)*(-1), 0)
        
        # 이동평균을 이용한 RSI 계산
        AU = pd.DataFrame(U).rolling(window=period).mean()
        AD = pd.DataFrame(D).rolling(window=period).mean()
        RSI = AU.div(AD+AU) *100
        
        return round(RSI,2)
    
    # MACD 구하기
    def make_macd(self, data1, f_period, s_period):
        # 지수이동평균을 이용한 macd 계산
        macd_fast = data1['close'].ewm(span=f_period, adjust=False).mean()
        macd_slow = data1['close'].ewm(span=s_period, adjust=False).mean()
        macd = macd_fast - macd_slow
        return round(macd,2)
    
    # macd_signal 구하기
    def make_macd_signal(self, data1, period):
        macd_signal = data1['macd'].ewm(span=period, adjust=False).mean()
        return round(macd_signal, 2)
    
    # ATR 추가하기
    def make_atr(self, dataset):
        # ATR 구하기
        atr_arr = []
        for j in dataset.index:
            if j == 0:
                atr_max = abs(dataset.iloc[j]['high'] - dataset.iloc[j]['low'])
                atr_arr.append(atr_max)
            if j > 0:
                atr_pr1 = abs(dataset.iloc[j]['high'] - dataset.iloc[j]['low'])
                atr_pr2 = abs(dataset.iloc[j-1]['close'] - dataset.iloc[j]['high'])
                atr_pr3 = abs(dataset.iloc[j-1]['close'] - dataset.iloc[j]['low'])            
                atr_list = [atr_pr1, atr_pr2, atr_pr3]
                atr_max = max(atr_list)
                atr_arr.append(atr_max)
        return atr_arr
    
    # 이격도 추가하기
    def make_separ(self, dataset, price, avgline):
        return round((dataset[price] / dataset[avgline]) * 100, 2) 
    
    # 볼린저밴드 추가하기(95.4%가 해당 범위 안에 존재)
    def make_BB(self, dataset):
        # 20일 이동평균
        ma20 = dataset['close'].rolling(window=20).mean()
        # 20일 이동평균 + (20일 표준편차 * 2)
        bol_up = ma20 + (2 * dataset['close'].rolling(window=20).std())
        # 20일 이동평균 - (20일 표준편차 * 2)
        bol_down = ma20 - (2 * dataset['close'].rolling(window=20).std())
        return round(bol_up,2), round(ma20,2), round(bol_down,2)
        
    ##----------------------------------------------------------------------------##    
    ## --버튼클릭시 함수 모음-- ##
    # 스레드1 실행
    def actionFunction1(self): 
        h1 = Thread1(self)
        h1.start()
    
    # 데이터 로드 버튼 클릭 시
    def pushButton_testStart_click(self):
        try:
            # 데이터를 가져와서 엑셀로 저장하기
            self.actionFunction1()
            
            # UI의 종목명, 검색시간 가져오기
            jongname = self.comboBox_jongmok2.currentText()
            ddtm = self.dateTimeEdit_searchDate.text()
            edtime = self.dateTimeEdit_searchDate_2.text()
            edtime = datetime.strptime(edtime, '%Y-%m-%d %H:%M:%S') # 문자 -> time 형식으로 바꾸기
            edtime = edtime - timedelta(minutes=5)
            
            # 쓰레드 실행이라서 동시 실행되므로 파일이 없으면 10초 정도 기다렸다 실행하기
            if os.path.isfile('cointest/'+jongname[0:3]+'_1m.xlsx') :
                time.sleep(3)
            else : 
                time.sleep(10)
                
            # 데이터 조회
            dataset_1d = pd.read_excel('cointest/'+jongname[0:3]+'_1d.xlsx', engine='openpyxl')
            dataset_5m = pd.read_excel('cointest/'+jongname[0:3]+'_5m.xlsx', engine='openpyxl')
            dataset_1h = pd.read_excel('cointest/'+jongname[0:3]+'_1h.xlsx', engine='openpyxl')
            dataset_1m = pd.read_excel('cointest/'+jongname[0:3]+'_1m.xlsx', engine='openpyxl')
            self.df_1d = dataset_1d
            self.df_5m = dataset_5m   
            self.df_1h = dataset_1h
            self.df_1m = dataset_1m

            # 단순이동평균선 추가
            self.df_5m['60avg'],self.df_5m['120avg'],self.df_5m['120avg'] = self.make_avgline(self.df_5m,'sub')
            self.df_1h['60avg'],self.df_1h['120avg'],self.df_1h['120avg'] = self.make_avgline(self.df_1h,'sub')
            self.df_1m['60avg'],self.df_1m['120avg'],self.df_1m['120avg'] = self.make_avgline(self.df_1m,'sub')
            self.df_1d['60avg'],self.df_1d['120avg'],self.df_1d['120avg'] = self.make_avgline(self.df_1d,'sub')
            
            # 지수 200일 이동평균선 추가
            self.df_5m['200avg'] = self.make_avgline2(self.df_5m, 'sub') # 이평 추가
            self.df_1h['200avg'] = self.make_avgline2(self.df_1h, 'sub') # 이평 추가
            self.df_1m['200avg'] = self.make_avgline2(self.df_1m, 'sub') # 이평 추가
            self.df_1d['200avg'] = self.make_avgline2(self.df_1d, 'sub') # 이평 추가
            
            # 볼린저밴드 추가
            self.df_5m['bb_up'], self.df_5m['20avg'], self.df_5m['bb_down'] = self.make_BB(self.df_5m)
            self.df_1h['bb_up'], self.df_1h['20avg'], self.df_1h['bb_down'] = self.make_BB(self.df_1h)
            self.df_1m['bb_up'], self.df_1m['20avg'], self.df_1m['bb_down'] = self.make_BB(self.df_1m)
            self.df_1d['bb_up'], self.df_1d['20avg'], self.df_1d['bb_down'] = self.make_BB(self.df_1d)
            
            # 데이터에 보조지표 추가하기(200 지수이동평균의 이격도)
            self.df_5m['separ'] = self.make_separ(self.df_5m, 'close', '200avg')
            self.df_1h['separ'] = self.make_separ(self.df_1h, 'close', '200avg')
            self.df_1m['separ'] = self.make_separ(self.df_1m, 'close', '200avg')
            self.df_1d['separ'] = self.make_separ(self.df_1d, 'close', '200avg')
            
            # 데이터에 보조지표 추가하기(상대강도)
            self.df_5m['strength'] = self.make_rsi(self.df_5m, 14)
            self.df_1h['strength'] = self.make_rsi(self.df_1h, 14)
            self.df_1m['strength'] = self.make_rsi(self.df_1m, 14)
            self.df_1d['strength'] = self.make_rsi(self.df_1d, 14)
            
            # MACD도 추가
            self.df_5m['macd'] = self.make_macd(self.df_5m, 12, 26)
            self.df_5m['macd_signal'] = self.make_macd_signal(self.df_5m, 9)
            
            # 당일, 전일 시간 구하기
            ddtm = datetime.strptime(ddtm, '%Y-%m-%d %H:%M:%S')
            ddtm_oneago = ddtm - timedelta(days=1)
            
            # 인덱스 구하기
            stdd_ind = dataset_5m[dataset_5m['datetime'] == ddtm].index[0] # 시작일 인덱스
            eddd_ind = dataset_5m[dataset_5m['datetime'] == edtime].index[0] # 종료일 인덱스
            new_dataset_5m = dataset_5m[stdd_ind:eddd_ind] # 시작일~종료일 새로운 데이터프레임
            new_dataset_5m = new_dataset_5m.reset_index(drop=True) # 인덱스 초기화
            self.df = new_dataset_5m # 당일 5분 데이터
            
            # 완료 알림
            QMessageBox.information(self,'알림창','테스트 데이터 로딩 완료!')
            
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            
    ## --시작 버튼 클릭 시 함수-- ##
    def push_start_click(self):
        try:
            # 자동이라면
            if self.combo_all.currentText() == '자동' :
                self.open_newwindow2(self.df, self.df_5m, self.df_1h, self.df_1m, self.df_1d)
            # 수동이라면    
            else :
                self.open_newwindow(self.df, self.df_5m, self.df_1h, self.df_1m, self.df_1d)
            
        except Exception as e:
            print(e)
            print(traceback.format_exc())
    
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()