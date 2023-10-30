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
from coin_invest_backtest.main_chart import main_chart_cls
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
            minit_arr = ['1m', '5m', '15m', '1h', '4h', '1d']
            
            for minit in minit_arr :
                if os.path.isfile('D:/coinInvest/cointest/'+jongname[0:3]+'_'+minit+'.xlsx') :
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
                    elif minit == '15m' : 
                        ddtm_newstart = start_time_bf - timedelta(hours=75)
                        ddtm_newend = end_time_bf
                    elif minit == '1h' :
                        ddtm_newstart = start_time_bf - timedelta(hours=300)
                        ddtm_newend = end_time_bf
                    elif minit == '4h' :
                        ddtm_newstart = start_time_bf - timedelta(hours=1200)
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
                    dataset.to_excel('D:/coinInvest/cointest/'+jongname[0:3]+'_'+minit+'.xlsx', index=False)
            
        except Exception as e:
            print(e)
            
class MyWindow(QMainWindow, form_class):
    # 시작 시
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        # 전역변수선언
        self.df = pd.DataFrame() # 전체 데이터 저장
        self.df_sub = pd.DataFrame() # 전체 데이터 저장 서브
        self.df_1m = pd.DataFrame() # 1분 데이터 저장
        self.df_5m = pd.DataFrame() # 5분 데이터 저장
        self.df_15m = pd.DataFrame() # 15분 데이터 저장
        self.df_1h = pd.DataFrame() # 1시간 데이터 저장
        self.df_4h = pd.DataFrame() # 4시간 데이터 저장
        self.df_1d = pd.DataFrame() # 일봉 데이터 저장
        self.df2 = pd.DataFrame() # 데이터 1행씩 추가
        self.xlay = 0 # 그래프 x축 증가데이터
        self.arr_xlay = [] # 그래프 x축 데이터 배열
        self.arr_ylay = [] # 그래프 y축 데이터 배열
        self.arr_datemax = [] # 고점의 날짜를 넣음
        self.arr_max = [] # 고점의 배열
        self.arr_datemin = [] # 저점의 날짜를 넣음
        self.arr_min = [] # 저점의 배열
        self.agohigh = 0 # 전일고가
        self.agolow = 0 # 전일저가
        self.nowopen = 0 # 당일 시가
        self.agovariance = 0 # 변동폭 = (전일최고 - 전일최저) / 2
        self.nowhighex = 0 # 당일예상고가
        self.nowlowex = 0 # 당일예상저가
        self.maxdf = pd.DataFrame() # 고점 데이터프레임
        self.mindf = pd.DataFrame() # 저점 데이터프레임
        
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
        self.push_chartview.clicked.connect(self.push_chartview_click) # 차트보기버튼
        
        ##----------------------------------------------------------------------------##
        ## TableWidget에서 Cell이 클릭 되었을 때 기능 실행
        self.tableWidget_2.cellClicked.connect(self.tablewidget2_cellclicked_event)
        
    ##----------------------------------------------------------------------------##
    ## 일반 함수 모음 ## 
    # Cell 클릭 시 datetime을 lineedit에 넣기
    def tablewidget2_cellclicked_event(self):
        cur_row = self.tableWidget_2.currentRow() # 현재 선택하고 있는 항목의 행을 반환합니다.
        sel_dt = self.tableWidget_2.item(cur_row, 0) # 선택한 행의 datetime을 반환 item형식
        value = sel_dt.text() # item형식을 text로 반환
        self.lineEdit_selectrow.setText(str(value)) # 텍스트 상자에 값을 넣음
    
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
        
        # 지수이동평균을 이용한 RSI 계산
        #AU_jisu = pd.DataFrame(U).ewm(span=period, adjust=False).mean()
        #AD_jisu = pd.DataFrame(D).ewm(span=period, adjust=False).mean()
        #RSI_jisu = AU_jisu.div(AD_jisu+AU_jisu) *100
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
        # 지수이동평균을 이용한 signal 계산
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
        
    
    # 1차 신호 - 전 저점 터치
    def signal_1(self, dataset, df_low):
        for i in dataset.index:
            if dataset.iloc[i]['condition1'] == 'Y' :
                temp_df_low = df_low[df_low['datetime'] < dataset.iloc[i]['datetime']]
                for j in temp_df_low.index :
                    if dataset.iloc[i]['high'] > temp_df_low.iloc[j]['low'] > dataset.iloc[i]['low'] :
                        if dataset.iloc[i]['signal1'] != 'N':
                            dataset.loc[i, 'signal1'] += ',signal_1'
                            break
                        else :
                            dataset.loc[i, 'signal1'] = 'signal_1'
                            break
                            
    # 1차 신호 - 전일 저점 터치
    def signal_2(self, dataset, ago_lowpoint):
        for i in dataset.index:
            if dataset.iloc[i]['condition1'] == 'Y' :
                if dataset.iloc[i]['high'] > ago_lowpoint > dataset.iloc[i]['low'] :
                    if dataset.iloc[i]['signal1'] != 'N':
                        dataset.loc[i, 'signal1'] += ',signal_2'
                    else :
                        dataset.loc[i, 'signal1'] = 'signal_2'
                        
    # 1차 신호 - 당일 예상 저점 터치
    def signal_3(self, dataset, now_exlowpoint):
        for i in dataset.index:
            if dataset.iloc[i]['condition1'] == 'Y' :
                if dataset.iloc[i]['high'] > now_exlowpoint > dataset.iloc[i]['low'] :
                    if dataset.iloc[i]['signal1'] != 'N':
                        dataset.loc[i, 'signal1'] += ',signal_3'
                    else :
                        dataset.loc[i, 'signal1'] = 'signal_3'
    
    # 1차 신호 - 과이격
    def signal_4(self, dataset, separ_how):
        # 20일선 : 10이상 과열 / -10이하 침체
        # 200일선 : 20이상 과열 / -20이하 침체
        if separ_how == '20avg' :
            separ_val = -10
        elif separ_how == '200avg' :
            separ_val = -20
        for i in dataset.index:
            if dataset.iloc[i]['condition1'] == 'Y' :
                if dataset.iloc[i]['separ'] <= separ_val : 
                    if dataset.iloc[i]['signal1'] != 'N':
                        dataset.loc[i, 'signal1'] += ',signal_4'
                    else :
                        dataset.loc[i, 'signal1'] = 'signal_4'
    
    # 1차 신호 - 강도 침체
    def signal_5(self, dataset, how_st): 
        if how_st == 'RSI' :
            strength_val = 30
        
        for i in dataset.index:
            if dataset.iloc[i]['condition1'] == 'Y' :
                if dataset.iloc[i]['strength'] <= strength_val : 
                    if dataset.iloc[i]['signal1'] != 'N':
                        dataset.loc[i, 'signal1'] += ',signal_5'
                    else :
                        dataset.loc[i, 'signal1'] = 'signal_5'
    
    # 1차 신호 - 이평선 터치
    def signal_6(self, dataset, how_avg):
        for i in dataset.index:
            if dataset.iloc[i]['condition1'] == 'Y' :
                if dataset.iloc[i]['high'] > dataset.iloc[i][how_avg] > dataset.iloc[i]['low'] :
                    if dataset.iloc[i]['signal1'] != 'N':
                        dataset.loc[i, 'signal1'] += ',signal_6'
                    else :
                        dataset.loc[i, 'signal1'] = 'signal_6'
    
    # 1차 신호 - 당일 시가 터치
    def signal_7(self, dataset, now_open):
        for i in dataset.index:
            if dataset.iloc[i]['condition1'] == 'Y' :
                if dataset.iloc[i]['high'] > now_open > dataset.iloc[i]['low'] :
                    if dataset.iloc[i]['signal1'] != 'N':
                        dataset.loc[i, 'signal1'] += ',signal_7'
                    else :
                        dataset.loc[i, 'signal1'] = 'signal_7'
    
    # 1차 신호 - 전 고점 터치
    def signal_8(self, dataset, df_high):
        for i in dataset.index:
            if dataset.iloc[i]['condition1'] == 'Y' :
                temp_df_high = df_high[df_high['datetime'] < dataset.iloc[i]['datetime']]
                for j in temp_df_high.index :
                    if dataset.iloc[i]['high'] > temp_df_high.iloc[j]['high'] > dataset.iloc[i]['low'] :
                        if dataset.iloc[i]['signal1'] != 'N':
                            dataset.loc[i, 'signal1'] += ',signal_8'
                            break
                        else :
                            dataset.loc[i, 'signal1'] = 'signal_8'
                            break
    
    # 1차 신호 - 전일 고점 터치
    def signal_9(self, dataset, ago_high):
        for i in dataset.index:
            if dataset.iloc[i]['condition1'] == 'Y' :
                if dataset.iloc[i]['high'] > ago_high > dataset.iloc[i]['low'] :
                    if dataset.iloc[i]['signal1'] != 'N':
                        dataset.loc[i, 'signal1'] += ',signal_9'
                    else :
                        dataset.loc[i, 'signal1'] = 'signal_9'
    
    # 1차 신호 - 당일 예상 고점 터치
    def signal_10(self, dataset, ago_exhigh):
        for i in dataset.index:
            if dataset.iloc[i]['condition1'] == 'Y' :
                if dataset.iloc[i]['high'] > ago_exhigh > dataset.iloc[i]['low'] :
                    if dataset.iloc[i]['signal1'] != 'N':
                        dataset.loc[i, 'signal1'] += ',signal_10'
                    else :
                        dataset.loc[i, 'signal1'] = 'signal_10'
                        
    # 2차 신호 - 없음
    def signal2_1(self, dataset):
        for i in dataset.index:
            if dataset.iloc[i]['signal1'] != 'N' :
                dataset.loc[i, 'signal2'] = 'signal2_1'
    
    # 2차 신호 - 강도 안정화 시
    def signal2_2(self, dataset, how_st):
        if how_st == 'RSI' :
            strength_val = 40
            
        for i in dataset.index:
            if dataset.iloc[i]['signal1'] != 'N' :
                for j in range(i+1, len(dataset)+1) :
                    if dataset.iloc[j]['strength'] > strength_val :
                        if dataset.iloc[j]['signal2'] != 'N' and dataset.iloc[j]['signal2'] != 'signal2_2':
                            dataset.loc[j, 'signal2'] += ',signal2_2'
                            break
                        else :
                            dataset.loc[j, 'signal2'] = 'signal2_2'
                            break
    # 2차 신호 - 과이격 안정화 시
    def signal2_3(self, dataset, separ_how):
        # 20일선 : 10이상 과열 / -10이하 침체
        # 200일선 : 20이상 과열 / -20이하 침체
        if separ_how == '20avg' :
            separ_val = -5
        elif separ_how == '200avg' :
            separ_val = -10
        for i in dataset.index:
            if dataset.iloc[i]['signal1'] != 'N' :
                for j in range(i+1, len(dataset)+1) :
                    if dataset.iloc[j]['separ'] > separ_val :
                        if dataset.iloc[j]['signal2'] != 'N' and dataset.iloc[j]['signal2'] != 'signal2_3':
                            dataset.loc[j, 'signal2'] += ',signal2_3'
                            break
                        else :
                            dataset.loc[j, 'signal2'] = 'signal2_3'
                            break
                        
    # 2차 신호 - 1차 신호의 종가 돌파 시
    def signal2_4(self, dataset):
        for i in dataset.index:
            if dataset.iloc[i]['signal1'] != 'N' :
                for j in range(i+1, len(dataset)+1) :
                    if dataset.iloc[j]['close'] > dataset.iloc[i]['close'] and dataset.iloc[j]['signal2'] != 'signal2_4':
                        if dataset.iloc[j]['signal2'] != 'N':
                            dataset.loc[j, 'signal2'] += ',signal2_4'
                            break
                        else :
                            dataset.loc[j, 'signal2'] = 'signal2_4'
                            break
                        
    # 2차 신호 - 1차 신호의 고가 돌파 시
    def signal2_5(self, dataset):
        for i in dataset.index:
            if dataset.iloc[i]['signal1'] != 'N' :
                for j in range(i+1, len(dataset)+1) :
                    if dataset.iloc[j]['close'] > dataset.iloc[i]['high'] and dataset.iloc[j]['signal2'] != 'signal2_5':
                        if dataset.iloc[j]['signal2'] != 'N':
                            dataset.loc[j, 'signal2'] += ',signal2_5'
                            break
                        else :
                            dataset.loc[j, 'signal2'] = 'signal2_5'
                            break
    
    # MACD 골크 시
    def signal2_6(self, dataset):
        for i in dataset.index:
            if dataset.iloc[i]['signal1'] != 'N' :
                for j in range(i+1, len(dataset)+1) :
                    if dataset.iloc[j]['macd'] > dataset.iloc[j]['macd_signal'] :
                        if dataset.iloc[j]['signal2'] != 'N' and dataset.iloc[j]['signal2'] != 'signal2_6':
                            dataset.loc[j, 'signal2'] += ',signal2_6'
                            break
                        else :
                            dataset.loc[j, 'signal2'] = 'signal2_6'
                            break
    
    # 5이평이 10이평 골크 시
    def signal2_7(self, dataset):
        for i in dataset.index:
            if dataset.iloc[i]['signal1'] != 'N' :
                for j in range(i+1, len(dataset)+1) :
                    if dataset.iloc[j]['5avg'] > dataset.iloc[j]['10avg'] :
                        if dataset.iloc[j]['signal2'] != 'N' and dataset.iloc[j]['signal2'] != 'signal2_7':
                            dataset.loc[j, 'signal2'] += ',signal2_7'
                            break
                        else :
                            dataset.loc[j, 'signal2'] = 'signal2_7'
                            break
                            
    ##----------------------------------------------------------------------------##                        
    ## --새창 열기 함수 모음-- ##
    def open_newwindow(self, dataset, dateset_5m, dateset_15m, dateset_1h, dateset_4h, dataset_1d):
        self.hide() # 메인 윈도우 숨김
        self.second = main_second_cls(dataset, dateset_5m, dateset_15m, dateset_1h, dateset_4h, dataset_1d)
        self.second.exec()
        self.show()
        
    def open_chartwindow(self,chart_dataset, chart_viewtime):
        self.hide() # 메인 윈도우 숨김
        self.chart = main_chart_cls(chart_dataset, chart_viewtime)
        self.chart.exec()
        self.show()
    
    ##----------------------------------------------------------------------------##    
    ## --버튼클릭시 함수 모음-- ##
    # 스레드1 실행
    def actionFunction1(self): 
        h1 = Thread1(self)
        h1.start()
    
    # 차트보기버튼 클릭시
    def push_chartview_click(self): # 차트보기
        try : 
            chart_viewtime = self.lineEdit_selectrow.text() # 차트를 볼 봉의 시간
            if chart_viewtime == '':
                QMessageBox.information(self,'알림창','결과 데이터를 로딩해주세요')
            else :
                if self.comboBox_chartview.currentText() == '전체' :
                    chart_dataset = self.df
                    self.open_chartwindow(chart_dataset, chart_viewtime)
                
                elif self.comboBox_chartview.currentText() == '부분' :
                    beforebarnum = self.spinBox_beforebarnum.value() # 표시할 전 봉수
                    afterbarnum = self.spinBox_afterbarnum.value() # 표시할 후 봉수
                    chart_dataset_before = self.df[self.df['datetime'] <= chart_viewtime] # 전봉의 데이터
                    chart_dataset_after = self.df[self.df['datetime'] > chart_viewtime] # 후봉의 데이터
                    ind = self.df[self.df['datetime'] == chart_viewtime].index[0] # 해당 시간의  인덱스
                    
                    if len(chart_dataset_before) < beforebarnum :
                        chart_dataset = self.df[0:ind+afterbarnum]
                        self.open_chartwindow(chart_dataset, chart_viewtime)
                    elif len(chart_dataset_after) < afterbarnum :
                        chart_dataset = self.df[ind-beforebarnum:len(self.df)]
                        self.open_chartwindow(chart_dataset, chart_viewtime)
                    elif len(chart_dataset_before) < beforebarnum and len(chart_dataset_after) < afterbarnum :
                        chart_dataset = self.df[0:len(self.df)]
                        self.open_chartwindow(chart_dataset, chart_viewtime)
                    else :
                        chart_dataset = self.df[ind-beforebarnum:ind+afterbarnum]
                        self.open_chartwindow(chart_dataset, chart_viewtime)
                        
        except Exception as e:
            print(e)
            
    # 테스트 시작 버튼 클릭 시
    def pushButton_testStart_click(self):
        try:
            # 1분 ~ 1일 데이터를 가져와서 엑셀로 저장하기
            self.actionFunction1()
            
            # UI의 종목명, 검색시간 가져오기
            jongname = self.comboBox_jongmok2.currentText()
            ddtm = self.dateTimeEdit_searchDate.text()
            edtime = self.dateTimeEdit_searchDate_2.text()
            edtime = datetime.strptime(edtime, '%Y-%m-%d %H:%M:%S') # 문자 -> time 형식으로 바꾸기
            edtime = edtime - timedelta(minutes=1)
            
            # 쓰레드 실행이라서 동시 실행되므로 파일이 없으면 30초 정도 기다렸다 실행하기
            if os.path.isfile('D:/coinInvest/cointest/'+jongname[0:3]+'_1m.xlsx') :
                time.sleep(3)
            else : 
                time.sleep(10)
                
            # 데이터 조회
            dataset_1m = pd.read_excel('D:/coinInvest/cointest/'+jongname[0:3]+'_1m.xlsx', engine='openpyxl')
            dataset_1d = pd.read_excel('D:/coinInvest/cointest/'+jongname[0:3]+'_1d.xlsx', engine='openpyxl')
            dataset_5m = pd.read_excel('D:/coinInvest/cointest/'+jongname[0:3]+'_5m.xlsx', engine='openpyxl')
            dataset_15m = pd.read_excel('D:/coinInvest/cointest/'+jongname[0:3]+'_15m.xlsx', engine='openpyxl')
            dataset_1h = pd.read_excel('D:/coinInvest/cointest/'+jongname[0:3]+'_1h.xlsx', engine='openpyxl')
            dataset_4h = pd.read_excel('D:/coinInvest/cointest/'+jongname[0:3]+'_4h.xlsx', engine='openpyxl')
            self.df_1m = dataset_1m
            self.df_1d = dataset_1d
            self.df_5m = dataset_5m   
            self.df_15m = dataset_15m
            self.df_1h = dataset_1h
            self.df_4h = dataset_4h

            # 1일봉 데이터에 보조지표 추가하기(5,10일이동평균선)
            self.df_1m['60avg'],self.df_1m['120avg'],self.df_1m['120avg'] = self.make_avgline(self.df_1m,'sub')
            self.df_5m['60avg'],self.df_5m['120avg'],self.df_5m['120avg'] = self.make_avgline(self.df_5m,'sub')
            self.df_15m['60avg'],self.df_15m['120avg'],self.df_15m['120avg'] = self.make_avgline(self.df_15m,'sub')
            self.df_1h['60avg'],self.df_1h['120avg'],self.df_1h['120avg'] = self.make_avgline(self.df_1h,'sub')
            self.df_4h['60avg'],self.df_4h['120avg'],self.df_4h['120avg'] = self.make_avgline(self.df_4h,'sub')
            self.df_1d['60avg'],self.df_1d['120avg'],self.df_1d['120avg'] = self.make_avgline(self.df_1d,'sub')
            
            # 데이터에 보조지표 추가하기(지수 200일 이동평균선)
            self.df_1m['200avg'] = self.make_avgline2(self.df_1m, 'sub') # 이평 추가
            self.df_5m['200avg'] = self.make_avgline2(self.df_5m, 'sub') # 이평 추가
            self.df_15m['200avg'] = self.make_avgline2(self.df_15m, 'sub') #이평 추가
            self.df_1h['200avg'] = self.make_avgline2(self.df_1h, 'sub') # 이평 추가
            self.df_4h['200avg'] = self.make_avgline2(self.df_4h, 'sub') # 이평 추가
            self.df_1d['200avg'] = self.make_avgline2(self.df_1d, 'sub') # 이평 추가
            
            # 데이터에 보조지표 추가하기(볼린저밴드)
            self.df_1m['bb_up'], self.df_1m['20avg'], self.df_1m['bb_down'] = self.make_BB(self.df_1m)
            self.df_5m['bb_up'], self.df_5m['20avg'], self.df_5m['bb_down'] = self.make_BB(self.df_5m)
            self.df_15m['bb_up'], self.df_15m['20avg'], self.df_15m['bb_down'] = self.make_BB(self.df_15m)
            self.df_1h['bb_up'], self.df_1h['20avg'], self.df_1h['bb_down'] = self.make_BB(self.df_1h)
            self.df_4h['bb_up'], self.df_4h['20avg'], self.df_4h['bb_down'] = self.make_BB(self.df_4h)
            self.df_1d['bb_up'], self.df_1d['20avg'], self.df_1d['bb_down'] = self.make_BB(self.df_1d)
            
            # 데이터에 보조지표 추가하기(200 지수이동평균의 이격도)
            self.df_1m['separ'] = self.make_separ(self.df_1m, 'close', '200avg')
            self.df_5m['separ'] = self.make_separ(self.df_5m, 'close', '200avg')
            self.df_15m['separ'] = self.make_separ(self.df_15m, 'close', '200avg')
            self.df_1h['separ'] = self.make_separ(self.df_1h, 'close', '200avg')
            self.df_4h['separ'] = self.make_separ(self.df_4h, 'close', '200avg')
            self.df_1d['separ'] = self.make_separ(self.df_1d, 'close', '200avg')
            
            # 데이터에 보조지표 추가하기(상대강도)
            self.df_1m['strength'] = self.make_rsi(self.df_1m, 9)
            self.df_5m['strength'] = self.make_rsi(self.df_5m, 9)
            self.df_15m['strength'] = self.make_rsi(self.df_15m, 9)
            self.df_1h['strength'] = self.make_rsi(self.df_1h, 9)
            self.df_4h['strength'] = self.make_rsi(self.df_4h, 9)
            self.df_1d['strength'] = self.make_rsi(self.df_1d, 9)
            
            # 1분봉에는 MACD도 추가하기
            self.df_1m['macd'] = self.make_macd(self.df_1m, 12, 26)
            self.df_1m['macd_signal'] = self.make_macd_signal(self.df_1m, 9)
            
            # 당일, 전일 시간 구하기
            ddtm = datetime.strptime(ddtm, '%Y-%m-%d %H:%M:%S')
            ddtm_oneago = ddtm - timedelta(days=1)
            
            # 전일 고,저 | 당일 시가, 예상 고,저 변수구하기
            self.agohigh = round(dataset_1d[dataset_1d['datetime']== ddtm_oneago]['high'].iloc[-1], 2) # 전일고가
            self.agolow = round(dataset_1d[dataset_1d['datetime']== ddtm_oneago]['low'].iloc[-1], 2) # 전일저가
            self.nowopen = round(dataset_1d[dataset_1d['datetime']== ddtm]['open'].iloc[-1], 2) # 당일 시가
            self.agovariance = round((self.agohigh - self.agolow) / 2, 2) # 변동폭 = (전일최고 - 전일최저) / 2
            self.nowhighex = round(self.nowopen + self.agovariance, 2) # 당일예상고가
            self.nowlowex = round(self.nowopen - self.agovariance, 2) # 당일예상저가
            
            # 인덱스 구하기
            stdd_ind = dataset_1m[dataset_1m['datetime'] == ddtm].index[0] # 시작일 인덱스
            eddd_ind = dataset_1m[dataset_1m['datetime'] == edtime].index[0] # 종료일 인덱스
            new_dataset_1m = dataset_1m[stdd_ind:eddd_ind] # 시작일~종료일 새로운 데이터프레임
            new_dataset_1m = new_dataset_1m.reset_index(drop=True) # 인덱스 초기화
            self.df_sub = new_dataset_1m # 메인에서 쓸 1분데이터
            
            # main_second 에서 쓸 1분데이터 만들기
            self.df_1m = self.df_1m[stdd_ind:eddd_ind] 
            self.df_1m = self.df_1m.reset_index(drop=True)
            
            # 완료 알림
            QMessageBox.information(self,'알림창','테스트 데이터 로딩 완료!')
            
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            
    ## --시작 버튼 클릭 시 함수-- ##
    def push_start_click(self):
        try:
            #### 전체 데이터 초기화 ####
            self.df = self.df_sub
            
            #### 결과테이블 초기화 ####
            self.tableWidget_2.clear() # 테이블 아이템 초기화
            self.tableWidget_2.setRowCount(0)
            self.tableWidget_2.setColumnCount(13)
            self.tableWidget_2.setHorizontalHeaderLabels(["datetime", "open", "high", "low", "close", "volume","condition1","signal1","condition2","signal2","손익가","손절가","결과"])
            
            if self.combo_all.currentText() == '자동' :
                #### df에 데이터 넣기 ####
                # 이동평균선 데이터 추가
                if self.combo_avgline.currentText() == '단순' :
                    self.df['5avg'], self.df['10avg'], self.df['20avg'], self.df['60avg'], self.df['120avg'], self.df['200avg'], self.df['240avg'] = self.make_avgline(self.df, 'main') # 5,10,20,60,120,200,240 이평 추가
                elif self.combo_avgline.currentText() == '지수' :
                    self.df['5avg'], self.df['10avg'], self.df['20avg'], self.df['60avg'], self.df['120avg'], self.df['200avg'], self.df['240avg'] = self.make_avgline2(self.df, 'main') # 5,10,20,60,120,200,240 이평 추가
                
                # 강도 지표 추가
                if self.combo_strength.currentText() == 'RSI' :
                    self.df['strength'] = self.make_rsi(self.df, 9)
                
                # 이격도 지표 추가
                if self.combo_separ.currentText() == '20avg' :
                    self.df['separ'] = self.make_separ(self.df, 'close', '20avg')
                elif self.combo_separ.currentText() == '60avg' :
                    self.df['separ'] = self.make_separ(self.df, 'close', '60avg')
                elif self.combo_separ.currentText() == '120avg' :
                    self.df['separ'] = self.make_separ(self.df, 'close', '120avg')
                elif self.combo_separ.currentText() == '200avg' :
                    self.df['separ'] = self.make_separ(self.df, 'close', '200avg')
                elif self.combo_separ.currentText() == '240avg' :
                    self.df['separ'] = self.make_separ(self.df, 'close', '240avg')
                    
                # MACD 지표 추가
                self.df['macd'] = self.make_macd(self.df, 12, 26)
                self.df['macd_signal'] = self.make_macd_signal(self.df, 9)
                
                # 저점, 고점 데이터 추가
                long = int(self.spinBox_bar.value())
                self.maxdf = maxLine_cls.exe_maxLine(self, self.df, long)
                self.mindf = minLine_cls.exe_minLine(self, self.df, long)
                
                #### 1차 신호 조건 ####
                # 봉조건
                self.df['condition1'] = 'N' # self.df에 '1차 조건' 컬럼에 Y or N을 추가하자
                self.df['signal1'] = 'N' # self.df에 '1차 신호' 컬럼에 Y or N을 추가하자
                self.df['condition2'] = 'N' # self.df에 '2차 조건' 컬럼에 Y or N을 추가하자
                self.df['signal2'] = 'N' # self.df에 '2차 신호' 컬럼에 Y or N을 추가하자
                if self.checkBox_2_1.isChecked(): # 없음
                    self.df['condition1'] = 'Y'
                if self.checkBox_2_2.isChecked(): # 양봉
                    for i in self.df.index:
                        if self.df.iloc[i]['close'] >= self.df.iloc[i]['open']:
                            self.df.loc[i, 'condition1'] = 'Y'
                if self.checkBox_2_3.isChecked(): # 음봉
                    for i in self.df.index:
                        if self.df.iloc[i]['close'] < self.df.iloc[i]['open']:
                            self.df.loc[i, 'condition1'] = 'Y'
                if self.checkBox_2_4.isChecked(): # 십자가봉 제외
                    for i in self.df.index:
                        if self.df.iloc[i]['close'] == self.df.iloc[i]['open']:
                            self.df.loc[i, 'condition1'] = 'N'
                
                # 거래량 조건
                if self.checkBox_3_1.isChecked(): # 없음
                    pass    
                
                # 강도 이격도 조건
                if self.checkBox_4_1.isChecked():
                    pass
                if self.checkBox_4_2.isChecked(): # 강도가 n이하여야 한다 (-> n초과면 N).
                    strenth_name = self.combo_strength.currentText()
                    stranth_value = self.doubleSpinBox_4_1.value()
                    for i in self.df.index:
                        if self.df.iloc[i][strenth_name] > stranth_value : 
                            self.df.loc[i, 'condition1'] = 'N'
                if self.checkBox_4_3.isChecked(): # 이격도가 n이상이여야 한다 (-> n미만이면 N).
                    separ_value = self.doubleSpinBox_4_2.value()
                    for i in self.df.index:
                        if self.df.iloc[i]['separ'] < separ_value :
                            self.df.loc[i, 'condition1'] = 'N'
                
                # 추세 조건
                if self.checkBox_5_1.isChecked(): # 없음
                    pass
                if self.checkBox_5_2.isChecked(): # 이평선 정배열 역배열 조건
                    avg_name1 = self.comboBox_5_1.currentText()
                    avg_name2 = self.comboBox_5_2.currentText()
                    avg_arr = self.comboBox_5_3.currentText()
                    if avg_name1 == avg_name2 :
                        QMessageBox.information(self, '알림창', '이평선이 같습니다. 다시 선택해주세요.')
                    else :
                        if avg_arr == '정배열' :
                            for i in self.df.index:
                                if self.df.iloc[i][avg_name1] < self.df.iloc[i][avg_name2] :
                                    self.df.loc[i, 'condition1'] = 'N'
                        elif avg_arr == '역배열' :
                            for i in self.df.index:
                                if self.df.iloc[i][avg_name1] > self.df.iloc[i][avg_name2] :
                                    self.df.loc[i, 'condition1'] = 'N'
                
                #### 1차 신호 발생 ####
                # 전 저점 터치
                if self.checkBox1.isChecked():
                    self.signal_1(self.df, self.mindf)
                
                # 전일 저점 터치
                if self.checkBox2.isChecked():
                    self.signal_2(self.df, self.agolow)
                
                # 당일 예상 저점 터치
                if self.checkBox3.isChecked():
                    self.signal_3(self.df, self.nowlowex)
                
                # 과이격
                if self.checkBox4.isChecked():
                    self.signal_4(self.df, self.combo_separ.currentText())
                
                # 강도 침체
                if self.checkBox5.isChecked():
                    self.signal_5(self.df, self.combo_strength.currentText())
                    
                # 이평선 터치
                if self.checkBox6.isChecked():
                    self.signal_6(self.df, self.combo_separ.currentText())
                
                # 당일 시가 터치
                if self.checkBox7.isChecked():
                    self.signal_7(self.df, self.nowopen)
                
                # 전 고점 터치
                if self.checkBox8.isChecked():
                    self.signal_8(self.df, self.maxdf)
                
                # 전일 고점 터치
                if self.checkBox9.isChecked():
                    self.signal_9(self.df, self.agohigh)
                
                # 당일 예상 고점 터치
                if self.checkBox10.isChecked():
                    self.signal_10(self.df, self.nowhighex)
                
                
                #### 2차 신호 조건  ####
                # 현재 없음 : 테스트 하면서 구해보기
                
                
                #### 2차 신호 발생 ####
                if self.checkBox_6_1.isChecked():
                    self.signal2_1(self.df)
                
                # 전일 저점 터치
                if self.checkBox_6_2.isChecked():
                    self.signal2_2(self.df, self.combo_strength.currentText())
                
                # 당일 예상 저점 터치
                if self.checkBox_6_3.isChecked():
                    self.signal2_3(self.df)
                
                # 과이격
                if self.checkBox_6_4.isChecked():
                    self.signal2_4(self.df, self.combo_separ.currentText())
                
                # 강도 침체
                if self.checkBox_6_5.isChecked():
                    self.signal2_5(self.df)
                    
                # 이평선 터치
                if self.checkBox_6_6.isChecked():
                    self.signal2_6(self.df)
                
                # 당일 시가 터치
                if self.checkBox_6_7.isChecked():
                    self.signal2_7(self.df)
                
                #### 손익 손절 파악 ####
                self.df['손익가'] = 0 # 손익가격넣기
                self.df['손절가'] = 0 # 손절가격넣기
                self.df['결과'] = 'N' # 수익,손절 결과 넣기
                # 고정 비율
                if self.checkBox_8_1.isChecked():
                    revenue_ratio = self.doubleSpinBox_7.value()
                    for i in self.df.index:
                        if self.df.iloc[i]['signal2'] != 'N' :
                            self.df.loc[i, '손익가'] = round(self.df.iloc[i]['close'] * ((100 + revenue_ratio) / 100),2)
                            self.df.loc[i, '손절가'] = round(self.df.iloc[i]['close'] * ((100 - revenue_ratio) / 100),2)
                            
                            for j in range(i, len(self.df)) :
                                if self.df.iloc[j]['close'] >= self.df.iloc[i]['손익가'] :
                                    self.df.loc[i, '결과'] = '수익'
                                    break
                                elif self.df.iloc[j]['close'] <= self.df.iloc[i]['손절가'] :
                                    self.df.loc[i, '결과'] = '손절'
                                    break
                
                #### 테이블에 결과 표시 하기 ####
                # 테이블에 값 넣기
                for i in self.df.index:
                    if self.df.iloc[i]['signal2'] != 'N' :
                        row = self.tableWidget_2.rowCount()
                        self.tableWidget_2.insertRow(row)
                        self.tableWidget_2.setItem(row , 0, QTableWidgetItem(str(self.df.iloc[i]['datetime'])))
                        self.tableWidget_2.setItem(row , 1, QTableWidgetItem(str(self.df.iloc[i]['open'])))
                        self.tableWidget_2.setItem(row , 2, QTableWidgetItem(str(self.df.iloc[i]['high'])))
                        self.tableWidget_2.setItem(row , 3, QTableWidgetItem(str(self.df.iloc[i]['low'])))
                        self.tableWidget_2.setItem(row , 4, QTableWidgetItem(str(self.df.iloc[i]['close'])))
                        self.tableWidget_2.setItem(row , 5, QTableWidgetItem(str(self.df.iloc[i]['volume'])))
                        self.tableWidget_2.setItem(row , 6, QTableWidgetItem(str(self.df.iloc[i]['condition1'])))
                        self.tableWidget_2.setItem(row , 7, QTableWidgetItem(str(self.df.iloc[i]['signal1'])))
                        self.tableWidget_2.setItem(row , 8, QTableWidgetItem(str(self.df.iloc[i]['condition2'])))
                        self.tableWidget_2.setItem(row , 9, QTableWidgetItem(str(self.df.iloc[i]['signal2'])))
                        self.tableWidget_2.setItem(row , 10, QTableWidgetItem(str(self.df.iloc[i]['손익가'])))
                        self.tableWidget_2.setItem(row , 11, QTableWidgetItem(str(self.df.iloc[i]['손절가'])))
                        self.tableWidget_2.setItem(row , 12, QTableWidgetItem(str(self.df.iloc[i]['결과'])))
                
                #### 완료 알림 ####
                QMessageBox.information(self,'알림창','로딩 완료!')
            
            # 수동이라면    
            else :
                self.open_newwindow(self.df_1m, self.df_5m, self.df_15m, self.df_1h, self.df_4h, self.df_1d)
            
        except Exception as e:
            print(e)
            print(traceback.format_exc())
    
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()