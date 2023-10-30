import sys
import numpy as np
import pandas as pd
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QAxContainer import *
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from mpl_toolkits.mplot3d import Axes3D
import ccxt # pip install ccxt # 가상화폐 거래소 모듈, 바이낸스 api 등 125개 거래소 지원
import math
import time
import os
from coin_invest.scalping_trading import scalping_trading_cls
from coin_invest_backtest.maxLine import maxLine_cls
from coin_invest_backtest.minLine import minLine_cls


form_class = uic.loadUiType("coinbacktest.ui")[0]

class Thread1(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self): # 과거 기간별 데이터 가져오기
        # 전역 변수 선언
        jongname = self.parent.comboBox_jongmok.currentText()
        minit = self.parent.comboBox_minit.currentText()
        print(jongname)
        
        if os.path.isfile('D:/coinInvest/cointest/'+jongname[0:3]+'_'+minit+'.xlsx') :
            print('이미 데이터가 있습니다.')
        else :
            # 코인시간 = 우리나라시간 - 9시
            start_time_bf = self.parent.dateTimeEdit_start.text()
            start_time = self.parent.to_mstimestamp(start_time_bf) # 가져올 데이터 시작일
            end_time_bf = self.parent.dateTimeEdit_end.text()
            end_time = self.parent.to_mstimestamp(end_time_bf) # 가져올 데이터 종료일

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
            
            # 과거 데이터 저장하기
            dataset.to_excel('D:/coinInvest/cointest/'+jongname[0:3]+'_'+minit+'.xlsx', index=False)
            
class MyWindow(QMainWindow, form_class):
    # 시작 시
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        # 전역변수선언
        self.df = pd.DataFrame() # 전체 데이터 저장
        self.df2 = pd.DataFrame() # 데이터 1행씩 추가
        self.xlay = 0 # 그래프 x축 증가데이터
        self.arr_xlay = [] # 그래프 x축 데이터 배열
        self.arr_ylay = [] # 그래프 y축 데이터 배열
        self.arr_datemax = [] # 고점의 날짜를 넣음
        self.arr_max = [] # 고점의 배열
        self.arr_datemin = [] # 저점의 날짜를 넣음
        self.arr_min = [] # 저점의 배열
        
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
        
        # 그래프 그리기
        self.fig = plt.Figure()
        self.canvas = FigureCanvas(self.fig)
        self.graph_verticalLayout.addWidget(self.canvas)
        
        # 종목 콤보박스에 종목넣기
        self.comboBox_jongmok.addItem('ETH/USDT')
        self.comboBox_jongmok.addItem('BCH/USDT')
        self.comboBox_jongmok.addItem('ETC/USDT')
        self.comboBox_jongmok.addItem('EOS/USDT')
        self.comboBox_jongmok.addItem('ADA/USDT')
        
        self.comboBox_jongmok2.addItem('ETH/USDT')
        self.comboBox_jongmok2.addItem('BCH/USDT')
        self.comboBox_jongmok2.addItem('ETC/USDT')
        self.comboBox_jongmok2.addItem('EOS/USDT')
        self.comboBox_jongmok2.addItem('ADA/USDT')
        
        self.comboBox_minit.addItem('1m')
        self.comboBox_minit.addItem('3m')
        self.comboBox_minit.addItem('5m')
        self.comboBox_minit.addItem('1d')
        
        ##----------------------------------------------------------------------------##
        ## 버튼 클릭 시 함수와 연결 모음 ##
        self.pushButton_datasave.clicked.connect(self.actionFunction1)
        self.pushButton_testStart.clicked.connect(self.pushButton_testStart_click) # 테스트시작 버튼
        self.pushButton_8.clicked.connect(self.pushButton_8_click) # 다음 버튼
        self.pushButton_4.clicked.connect(self.pushButton_4_click) # 매수진입버튼
        self.pushButton_5.clicked.connect(self.pushButton_5_click) # 매도진입버튼
        
        ##----------------------------------------------------------------------------##
        ## 테이블안의 셀 조작 ##
        # 테이블에서 셀의 내용 더블 클릭 시 함수와 연결 
        #self.테이블명.cellDoubleClicked.connect(self.함수명) 
        
        ##----------------------------------------------------------------------------##
        ## 버튼 기능 활성화
        #self.버튼명.setEnabled(False)
        
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
        str = datetime.strptime(dd, "%Y-%m-%d %H:%M:%S")
        str = datetime.timestamp(str)
        str = int(str) * 1000
        return str
    
    # 이동평균 구하기
    def make_avgline(self, df):
        avg_20 = df['close'].rolling(window=20).mean()
        avg_60 = df['close'].rolling(window=60).mean()
        avg_120 = df['close'].rolling(window=120).mean()
        return avg_20, avg_60, avg_120
    
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
        return RSI
    
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
    
    ##----------------------------------------------------------------------------##    
    ## 버튼클릭시 함수 모음 ##
    def actionFunction1(self): # 스레드1 실행
        h1 = Thread1(self)
        h1.start()
        
    def pushButton_testStart_click(self):
        jongname = self.comboBox_jongmok2.currentText()
        ddtm = self.dateTimeEdit_searchDate.text()
        edtime = self.dateTimeEdit_searchDate_2.text()
        
        ddtm = datetime.strptime(ddtm, '%Y-%m-%d %H:%M:%S')
        ddtime = ddtm - timedelta(days=1)
        
        # 1일, 1분 데이터 조회
        dataset_1m = pd.read_excel('D:/coinInvest/cointest/'+jongname[0:3]+'_1m.xlsx', engine='openpyxl')
        dataset_1d = pd.read_excel('D:/coinInvest/cointest/'+jongname[0:3]+'_1d.xlsx', engine='openpyxl')
        
        # 변수(1)
        agohigh = round(dataset_1d[dataset_1d['datetime']== ddtime]['high'].iloc[-1], 2) # 전일고가
        agolow = round(dataset_1d[dataset_1d['datetime']== ddtime]['low'].iloc[-1], 2) # 전일저가
        nowopen = round(dataset_1d[dataset_1d['datetime']== ddtm]['open'].iloc[-1], 2) # 당일 시가
        agovariance = round((agohigh - agolow) / 2, 2) # 변동폭 = (전일최고 - 전일최저) / 2
        nowhighex = round(nowopen + agovariance, 2) # 당일예상고가
        nowlowex = round(nowopen - agovariance, 2) # 당일예상저가
        
        # 변수(2)
        stdd_ind = dataset_1m[dataset_1m['datetime'] == ddtime].index[0] # 시작일 인덱스
        eddd_ind = dataset_1m[dataset_1m['datetime'] == edtime].index[0] # 종료일 인덱스
        new_dataset_1m = dataset_1m[stdd_ind:eddd_ind] # 시작일~종료일 새로운 데이터프레임
        new_dataset_1m = new_dataset_1m.reset_index(drop=True) # 인덱스 초기화
        agovolmax = round(new_dataset_1m['volume'].max(), 2) # 전일 거래량 최대
        agovolmin = round(new_dataset_1m['volume'].min(), 2) # 전일 거래량 최소
        volavg = round(new_dataset_1m['volume'].mean(), 2) # 거래량 평균
        
        # 변동폭 텍스트 상자에 값넣기
        self.lineEdit_agohigh.setText(str(agohigh))
        self.lineEdit_agolow.setText(str(agolow))
        self.lineEdit_nowopen.setText(str(nowopen))
        self.lineEdit_agovariance.setText(str(agovariance))
        self.lineEdit_nowhighex.setText(str(nowhighex))  
        self.lineEdit_nowlowex.setText(str(nowlowex))  
        self.lineEdit_5.setText(str(agovolmax))
        self.lineEdit_6.setText(str(agovolmin))
        self.lineEdit_7.setText(str(volavg))
        
        # 테스트 시작 버튼 클릭 시 초기화 되어야 하는 변수들 정리
        self.spinBox.setValue(0) # 스핀박스 0으로 초기화하기 
        self.tableWidget.clear() # 테이블 아이템 초기화
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(6)
        self.tableWidget.setHorizontalHeaderLabels(["datetime", "open", "high", "low", "close", "volume"])
        
        # 테스트 데이터에 보조 지표값 추가하기
        stdd_ind2 = dataset_1m[dataset_1m['datetime'] == ddtm].index[0] # 시작일 인덱스
        test_df = dataset_1m[stdd_ind2:eddd_ind] # 시작일~종료일 새로운 데이터프레임 
        test_df = test_df.reset_index(drop=True) # 인덱스 초기화
        test_df['20avg'], test_df['60avg'], test_df['120avg'] = self.make_avgline(test_df) # 20, 60, 120 이평선 추가
        test_df['rsi'] = self.make_rsi(test_df, 14)
        test_df['macd'] = self.make_macd(test_df, 12, 26)
        test_df['macdsig'] = self.make_macd_signal(test_df, 9)
        test_df['atr'] = self.make_atr(test_df)
        self.df = test_df
        
        # 완료 알림
        QMessageBox.information(self,'알림창','테스트 데이터 로딩 완료!')
        
    def pushButton_4_click(self): 
        # 스핀박스 숫자를 인덱스로 값 추출하기
        spinnum = self.spinBox.value()
    
        dt = self.df.iloc[spinnum]['datetime']
        cl_ago = self.df.iloc[spinnum-1]['close']
        position = "매수"
        goal_price = round(cl_ago * 1.01, 2)
        loss_price = round(cl_ago * 0.99, 2)
        profit = 0
        gubun = "보유"
        
        # 테이블에 값 넣기
        row = self.tableWidget_2.rowCount()
        self.tableWidget_2.insertRow(row)
        self.tableWidget_2.setItem(row , 0, QTableWidgetItem(str(dt)))
        self.tableWidget_2.setItem(row , 1, QTableWidgetItem(position))
        self.tableWidget_2.setItem(row , 2, QTableWidgetItem(str(cl_ago)))
        self.tableWidget_2.setItem(row , 3, QTableWidgetItem(str(goal_price)))
        self.tableWidget_2.setItem(row , 4, QTableWidgetItem(str(loss_price)))
        self.tableWidget_2.setItem(row , 5, QTableWidgetItem(str(profit)))
        self.tableWidget_2.setItem(row , 6, QTableWidgetItem(gubun))
        self.tableWidget_2.scrollToBottom() # 스크롤을 제일 아래로 내린다
            
    def pushButton_5_click(self): 
        # 스핀박스 숫자를 인덱스로 값 추출하기
        spinnum = self.spinBox.value()
    
        dt = self.df.iloc[spinnum]['datetime']
        cl_ago = self.df.iloc[spinnum-1]['close']
        position = "매도"
        goal_price = round(cl_ago * 0.99, 2)
        loss_price = round(cl_ago * 1.01, 2)
        profit = 0
        gubun = "보유"
        
        # 테이블에 값 넣기
        row = self.tableWidget_2.rowCount()
        self.tableWidget_2.insertRow(row)
        self.tableWidget_2.setItem(row , 0, QTableWidgetItem(str(dt)))
        self.tableWidget_2.setItem(row , 1, QTableWidgetItem(position))
        self.tableWidget_2.setItem(row , 2, QTableWidgetItem(str(cl_ago)))
        self.tableWidget_2.setItem(row , 3, QTableWidgetItem(str(goal_price)))
        self.tableWidget_2.setItem(row , 4, QTableWidgetItem(str(loss_price)))
        self.tableWidget_2.setItem(row , 5, QTableWidgetItem(str(profit)))
        self.tableWidget_2.setItem(row , 6, QTableWidgetItem(gubun))
        self.tableWidget_2.scrollToBottom() # 스크롤을 제일 아래로 내린다
    
    def pushButton_8_click(self):
        # 스핀박스 숫자를 인덱스로 값 추출하기
        spinnum = self.spinBox.value()
        
        if len(self.df) == 0:
            QMessageBox.information(self,'알림창','테스트 시작 버튼을 먼저 눌러주세요.')
        else :
            dt = self.df.iloc[spinnum]['datetime']
            op = self.df.iloc[spinnum]['open']
            hi = self.df.iloc[spinnum]['high']
            lw = self.df.iloc[spinnum]['low']
            cl = self.df.iloc[spinnum]['close']
            vo = self.df.iloc[spinnum]['volume']
            avg20val = self.df.iloc[spinnum]['20avg']
            avg60val = self.df.iloc[spinnum]['60avg']
            avg120val = self.df.iloc[spinnum]['120avg']
            rsival = self.df.iloc[spinnum]['rsi']
            macdval = self.df.iloc[spinnum]['macd']
            macdsigval = self.df.iloc[spinnum]['macdsig']
            atrval = self.df.iloc[spinnum]['atr']
            
            ### Ui에 값 입력 ###
            self.lineEdit_32.setText(str(rsival))
            self.lineEdit_38.setText(str(atrval))
            
            # 이격도 구하기
            ju20 = round((cl / avg20val) * 100,2)# 주가 20일선 이격도
            ju60 = round((cl / avg60val) * 100,2) # 주가 60일선 이격도
            ju120 = round((cl / avg120val) * 100,2) # 주가 120일선 이격도
            mo2060 = round((avg20val / avg60val) * 100,2) # 20일선 60일선 이격도
            mo20120 = round((avg20val / avg120val) * 100,2) # 20일선 120일선 이격도
            
            ### Ui에 값 입력 ###
            self.lineEdit_11.setText(str(ju20))
            self.lineEdit_12.setText(str(ju60))
            self.lineEdit_13.setText(str(ju120))
            self.lineEdit_17.setText(str(mo2060))
            self.lineEdit_18.setText(str(mo20120))
            
            # 스핀박스 숫자 up
            self.spinBox.setValue(spinnum + 1)
            
            # 테이블에 값 넣기
            row = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)
            self.tableWidget.setItem(row , 0, QTableWidgetItem(str(dt)))
            self.tableWidget.setItem(row , 1, QTableWidgetItem(str(op)))
            self.tableWidget.setItem(row , 2, QTableWidgetItem(str(hi)))
            self.tableWidget.setItem(row , 3, QTableWidgetItem(str(lw)))
            self.tableWidget.setItem(row , 4, QTableWidgetItem(str(cl)))
            self.tableWidget.setItem(row , 5, QTableWidgetItem(str(vo)))
            self.tableWidget.scrollToBottom() # 스크롤을 제일 아래로 내린다
            
            # 데이터 한행 씩 추가하기
            self.df2 = self.df2.append(self.df.iloc[spinnum], sort=False) # 전체 데이터에 하나의 데이터 추가
            
            # 저점 고점 구하기
            aa = maxLine_cls.exe_maxLine(self, dt, self.df2, 20) # 구간 고점
            bb = minLine_cls.exe_minLine(self, dt, self.df2, 20) # 구간 저점
            if aa != 0 :
                self.arr_max.append(self.df.iloc[aa]['high'])
                self.arr_datemax.append(self.df.iloc[aa]['datetime'])
                print('고점', self.arr_datemax)
                print(self.arr_max)
            if bb != 0 :
                self.arr_min.append(self.df.iloc[bb]['low'])
                self.arr_datemin.append(self.df.iloc[bb]['datetime'])
                print('저점', self.arr_datemin)
                print(self.arr_min)
                
            if len(self.arr_max) >= 3:
                self.lineEdit_max1.setText(str(self.arr_max[-3]))
                self.lineEdit_max2.setText(str(self.arr_max[-2]))
                self.lineEdit_max3.setText(str(self.arr_max[-1]))
                
            if len(self.arr_min) >= 3:
                self.lineEdit_min1.setText(str(self.arr_min[-3]))
                self.lineEdit_min2.setText(str(self.arr_min[-2]))
                self.lineEdit_min3.setText(str(self.arr_min[-1]))
            
                
            # df2에서 값 뽑아내기
            m_maxvol = round(self.df2['volume'].max(), 2) # 최고 거래량
            m_minvol = round(self.df2['volume'].min(), 2) # 최저 거래량
            m_avgvol = round(self.df2['volume'].mean(), 2) # 거래량 평균
            
            ### Ui에 값 입력 ###
            self.lineEdit_16.setText(str(m_maxvol))
            self.lineEdit_15.setText(str(m_minvol))
            self.lineEdit_14.setText(str(m_avgvol))
            
            # 그래프 표시 항목
            agomaxval = float(self.lineEdit_agohigh.text()) # 전일고가
            agominval = float(self.lineEdit_agolow.text()) # 전일저가
            nowmaxvalex = float(self.lineEdit_nowhighex.text()) # 당일예상고가
            nowminvalex = float(self.lineEdit_nowlowex.text()) # 당일예상저가
            nowmaxval = float(self.df2['high'].max()) # 당일고가
            nowminval = float(self.df2['low'].min()) # 당일저가
            
            # 주가 위치 구하기
            agoprepare = round(((agomaxval + agominval) / cl) * 100, 2)
            nowprepare = round(((nowmaxvalex + nowminvalex) / cl) * 100, 2)
            if len(self.arr_max) >= 1 :
                preagoprepare = round((self.arr_max[-1] / cl) * 100, 2)
            else : 
                preagoprepare = 'nan'
            if len(self.arr_min) >= 1 :
                prenowprepare = round((self.arr_min[-1] / cl) * 100, 2)
            else : 
                prenowprepare = 'nan'
                
            ### Ui에 값 입력 ###
            self.lineEdit_19.setText(str(agoprepare))
            self.lineEdit_20.setText(str(nowprepare))
            self.lineEdit_21.setText(str(preagoprepare))
            self.lineEdit_22.setText(str(prenowprepare))
            
            ### --------------------------------------------------------------- ###
            ## 그래프 그리기 ##
            # 그래프 그리기 위해 배열에 값 append하기
            if self.xlay == 50 :
                del self.arr_xlay[-1]
                del self.arr_ylay[0]
                self.xlay -= 1
                self.arr_xlay.append(self.xlay)
                self.arr_ylay.append(cl)
            else :
                self.arr_ylay.append(cl)
                self.arr_xlay.append(self.xlay)
            
            # 그래프 그리기
            ax = self.fig.add_subplot(111)
            ax.cla()
            ax.axhline(agomaxval, 0, 1, color='black', linestyle='-')
            ax.axhline(agominval, 0, 1, color='black', linestyle='-')
            ax.axhline(nowmaxvalex, 0, 1, color='blue', linestyle='-')
            ax.axhline(nowminvalex, 0, 1, color='blue', linestyle='-')
            ax.axhline(nowmaxval, 0, 1, color='red', linestyle='--')
            ax.axhline(nowminval, 0, 1, color='red', linestyle='--')
            ax.scatter(self.arr_xlay, self.arr_ylay, s = 10, c = 'k', alpha = 0.5)
            self.canvas.draw()
            
            ### --------------------------------------------------------------- ###
            ## 결과 테이블에 값 넣기 ##
            # x축 1씩 증가
            self.xlay += 1
            
            # 결과테이블
            row_count = self.tableWidget_2.rowCount()
            
            if row_count >= 1 :
                for i in range(0, row_count):
                    item = self.tableWidget_2.item(i, 1) # 포지션
                    item1 = self.tableWidget_2.item(i, 2) # 진입가
                    item2 = self.tableWidget_2.item(i, 3) # 목표가
                    item3 = self.tableWidget_2.item(i, 4) # 손절가
                    item5 = self.tableWidget_2.item(i, 6) # 구분
                    
                    if item5.text() == "보유":
                        if item.text() == '매수' :
                            perpri = round(cl/float(item1.text()) * 100 - 100, 2)
                            self.tableWidget_2.setItem(i , 5, QTableWidgetItem(str(perpri)))
                            if cl >= float(item2.text()) :
                                self.tableWidget_2.setItem(i , 6, QTableWidgetItem("수익"))
                                
                            if cl <= float(item3.text()) :
                                self.tableWidget_2.setItem(i , 6, QTableWidgetItem("손절"))
                    
                        elif item.text() == '매도' :            
                            perpri = round(float(item1.text())/cl * 100 - 100, 2)
                            self.tableWidget_2.setItem(i , 5, QTableWidgetItem(str(perpri)))
                            if cl <= float(item2.text()) :
                                self.tableWidget_2.setItem(i , 6, QTableWidgetItem("수익"))
                                
                            if cl >= float(item3.text()) :
                                self.tableWidget_2.setItem(i , 6, QTableWidgetItem("손절"))
                            
            
         
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()