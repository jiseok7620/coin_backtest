import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from mpl_toolkits.mplot3d import Axes3D
import mpl_finance
import traceback
from coin_invest_backtest.maxLine import maxLine_cls
from coin_invest_backtest.minLine import minLine_cls
import time
from coin_invest_backtest.viewtrend import viewtrend_cls
from coin_invest_backtest.searchtrend import searchtrend_cls

form_secondwindow = uic.loadUiType("second.ui")[0] #두 번째창 ui

class main_second_cls(QDialog, QWidget, form_secondwindow):
    def __init__(self, dataset, dateset_5m, dateset_1h, dateset_4h, dataset_1d):
        super(main_second_cls, self).__init__()
        self.setupUi(self)
        self.show() # 두번째창 실행

        # 전역변수선언
        self.df = dataset
        self.df2 = pd.DataFrame() # 데이터 1행씩 추가
        self.df_5m = dateset_5m # 5분 데이터 저장
        self.df_1h = dateset_1h # 1시간 데이터 저장
        self.df_4h = dateset_4h # 4시간 데이터 저장
        self.df_1d = dataset_1d # 일봉 데이터 저장
        self.arr_datemax = [] # 고점의 날짜를 넣음
        self.arr_max = [] # 고점의 배열
        self.arr_datemin = [] # 저점의 날짜를 넣음
        self.arr_min = [] # 저점의 배열
        self.goalprice = 0
        self.lossprice = 0
        self.long_num = 10
        
        # 매수,매도
        self.df_rank = pd.DataFrame() # 지지저항선(내림차순)
        
        # 선정봉 - 추세 전역변수
        self.select_result_5m = ''
        self.select_result_1h = ''
        self.select_result_4h = ''
        self.select_result_1d = ''
        self.bohab_up_5m = 0
        self.bohab_up_1h = 0
        self.bohab_up_4h = 0
        self.bohab_up_1d = 0
        self.bohab_down_5m = 0
        self.bohab_down_1h = 0
        self.bohab_down_4h = 0
        self.bohab_down_1d = 0
        
        # 고점저점 데이터
        self.df_high_5m = maxLine_cls.exe_maxLine(self, self.df_5m, 20)
        self.df_low_5m = minLine_cls.exe_minLine(self, self.df_5m, 20)
        
        ## 버튼 클릭 시 함수와 연결 모음 ##
        #self.pushButton_3.clicked.connect(self.pushButton_3_click) # 이전 버튼
        self.pushButton_8.clicked.connect(self.pushButton_8_click) # 다음 버튼
        self.pushButton_4.clicked.connect(self.pushButton_4_click) # 매수진입버튼
        self.pushButton_5.clicked.connect(self.pushButton_5_click) # 매도진입버튼
        self.push_chartview2.clicked.connect(self.push_chartview2_click) # 차트보기버튼
        
        ##----------------------------------------------------------------------------##
        ## TableWidget에서 Cell이 클릭 되었을 때 기능 실행
        self.tableWidget_2.cellClicked.connect(self.tablewidget2_cellclicked_event)
    
    # 직선의 방정식 함수
    def line_equation(self, x_val, incl, y_val):
        result = round(incl*x_val + y_val,2)
        return result
    
    # 이격도 구하기
    def make_separ(self, dataset, price, avgline):
        return round((dataset.iloc[-1][price] / dataset.iloc[-1][avgline]) * 100,2) 
    
    # 볼린저밴드 구하기
    def make_BB(self, dataset):
        # 20일 이동평균
        ma20 = dataset['close'].rolling(window=20).mean()
        # 20일 이동평균 + (20일 표준편차 * 2)
        bol_up = ma20 + (2 * dataset['close'].rolling(window=20).std())
        # 20일 이동평균 - (20일 표준편차 * 2)
        bol_down = ma20 - (2 * dataset['close'].rolling(window=20).std())
        return round(bol_up.iloc[-1],2), round(ma20.iloc[-1],2), round(bol_down.iloc[-1],2)
    
    # RSI 구하기
    def make_rsi(self, data1, period):
        U = np.where(data1['close'].diff(1) > 0, data1['close'].diff(1), 0)
        D = np.where(data1['close'].diff(1) < 0, data1['close'].diff(1)*(-1), 0)
        # 이동평균을 이용한 RSI 계산
        AU = pd.DataFrame(U).rolling(window=period).mean()
        AD = pd.DataFrame(D).rolling(window=period).mean()
        RSI = AU.div(AD+AU) *100
        return round(RSI.iloc[-1][0],2)
    
    # 이동평균 구하기
    def make_avgline(self, df):
        avg_5 = df['close'].rolling(window=5).mean()
        avg_10 = df['close'].rolling(window=10).mean()
        return round(avg_5.iloc[-1],2), round(avg_10.iloc[-1],2)
    
    # 지수이동평균 구하기
    def make_avgline2(self, df):
        avg_200 = df['close'].ewm(span=200, adjust=False).mean()
        return round(avg_200.iloc[-1],2)
    
    # Cell 클릭 시 datetime을 lineedit에 넣기
    def tablewidget2_cellclicked_event(self):
        cur_row = self.tableWidget_2.currentRow() # 현재 선택하고 있는 항목의 행을 반환합니다.
        sel_dt = self.tableWidget_2.item(cur_row, 0) # 선택한 행의 datetime을 반환 item형식
        value = sel_dt.text() # item형식을 text로 반환
        self.lineEdit_selectrow.setText(str(value)) # 텍스트 상자에 값을 넣음
        
    # 차트보기버튼 클릭시
    def push_chartview2_click(self):
        try : 
            # 스핀박스 숫자를 인덱스로 값 추출하기( : -1을 해야됨 = 이미 1이 증가되어있는상태라서)
            spinnum = self.spinBox.value() - 1
            
            # 필요한 변수 만들기
            dt = self.df.iloc[spinnum]['datetime']
            
            # 봉 데이터 마다 다른 시간을 적용해야함
            # 1D : | 
            dt_1h = dt - timedelta(minutes=55)
            dt_4h = dt - timedelta(minutes=235)
            dt_1d = dt - timedelta(minutes=1435)
            
            # 5분, 1시간, 4시간, 1일에서 표시할 데이터만 뽑기
            chart_5m = self.df_5m[self.df_5m['datetime'] <= dt] # 전봉의 데이터 5-1 6-2 7-3 8-4 9-5
            chart_1h = self.df_1h[self.df_1h['datetime'] <= dt_1h] # 전봉의 데이터
            chart_4h = self.df_4h[self.df_4h['datetime'] <= dt_4h] # 전봉의 데이터
            chart_1d = self.df_1d[self.df_1d['datetime'] <= dt_1d] # 전봉의 데이터

            # 종가는 공통
            add_close = self.df.iloc[spinnum]['close']
            if dt_1h != chart_1h.iloc[-1]['datetime'] :
                dt_1h_start = chart_1h.iloc[-1]['datetime'] + timedelta(minutes=60)
                temp_data = self.df[(self.df['datetime'] >= dt_1h_start) & (self.df['datetime'] <= dt)]
                add_open_1h = temp_data.iloc[0]['open']
                add_high_1h = float(temp_data['high'].max()) # 당일고가
                add_low_1h = float(temp_data['low'].min()) # 당일저가
                # 데이터프레임에 값 추가하기
                chart_1h = chart_1h.append({'datetime' : dt, 'open' : add_open_1h, 'high' : add_high_1h, 'low' : add_low_1h, 'close' : add_close}, ignore_index=True)
                chart_1h.loc[len(chart_1h)-1, '200avg'] = self.make_avgline2(chart_1h)
                chart_1h.loc[len(chart_1h)-1, 'bb_up'], chart_1h.loc[len(chart_1h)-1, '20avg'], chart_1h.loc[len(chart_1h)-1, 'bb_down'] = self.make_BB(chart_1h)
                chart_1h.loc[len(chart_1h)-1, 'separ'] = self.make_separ(chart_1h, "close", "200avg")
                chart_1h.loc[len(chart_1h)-1, 'strength'] = self.make_rsi(chart_1h, 9)
            if dt_4h != chart_4h.iloc[-1]['datetime'] :
                dt_4h_start = chart_4h.iloc[-1]['datetime'] + timedelta(minutes=240)
                temp_data = self.df[(self.df['datetime'] >= dt_4h_start) & (self.df['datetime'] <= dt)]
                add_open_4h = temp_data.iloc[0]['open']
                add_high_4h = float(temp_data['high'].max()) # 당일고가
                add_low_4h = float(temp_data['low'].min()) # 당일저가
                # 데이터프레임에 값 추가하기
                chart_4h = chart_4h.append({'datetime' : dt, 'open' : add_open_4h, 'high' : add_high_4h, 'low' : add_low_4h, 'close' : add_close}, ignore_index=True)
                chart_4h.loc[len(chart_4h)-1, '200avg'] = self.make_avgline2(chart_4h)
                chart_4h.loc[len(chart_4h)-1, 'bb_up'], chart_4h.loc[len(chart_4h)-1, '20avg'], chart_4h.loc[len(chart_4h)-1, 'bb_down'] = self.make_BB(chart_4h)
                chart_4h.loc[len(chart_4h)-1, 'separ'] = self.make_separ(chart_4h, "close", "200avg")
                chart_4h.loc[len(chart_4h)-1, 'strength'] = self.make_rsi(chart_4h, 9)
            if dt_1d != chart_1d.iloc[-1]['datetime'] :
                dt_1d_start = chart_1d.iloc[-1]['datetime'] + timedelta(minutes=1440)
                temp_data = self.df[(self.df['datetime'] >= dt_1d_start) & (self.df['datetime'] <= dt)]
                add_open_1d = temp_data.iloc[0]['open']
                add_high_1d = float(temp_data['high'].max()) # 당일고가
                add_low_1d = float(temp_data['low'].min()) # 당일저가
                # 데이터프레임에 값 추가하기
                chart_1d = chart_1d.append({'datetime' : dt, 'open' : add_open_1d, 'high' : add_high_1d, 'low' : add_low_1d, 'close' : add_close}, ignore_index=True)
                chart_1d.loc[len(chart_1d)-1, '5avg'], chart_1d.loc[len(chart_1d)-1, '10avg'] = self.make_avgline(chart_1d)
                chart_1d.loc[len(chart_1d)-1, '200avg'] = self.make_avgline2(chart_1d)
                chart_1d.loc[len(chart_1d)-1, 'bb_up'], chart_1d.loc[len(chart_1d)-1, '20avg'], chart_1d.loc[len(chart_1d)-1, 'bb_down'] = self.make_BB(chart_1d)
                chart_1d.loc[len(chart_1d)-1, 'separ'] = self.make_separ(chart_1d, "close", "200avg")
                chart_1d.loc[len(chart_1d)-1, 'strength'] = self.make_rsi(chart_1d, 9)
            
            # 이중 n개만 표시하도록 하기
            display_chart2_num = self.spinBox_chartview2.value()
            chart_5m = chart_5m[len(chart_5m) - display_chart2_num : len(chart_5m) + 1]
            chart_1h = chart_1h[len(chart_1h) - display_chart2_num : len(chart_1h) + 1]
            chart_4h = chart_4h[len(chart_4h) - display_chart2_num : len(chart_4h) + 1]
            chart_1d = chart_1d[len(chart_1d) - display_chart2_num : len(chart_1d) + 1]
            
            # 인덱스 초기화
            chart_5m = chart_5m.reset_index(drop=True) # 인덱스 초기화
            chart_1h = chart_1h.reset_index(drop=True) # 인덱스 초기화
            chart_4h = chart_4h.reset_index(drop=True) # 인덱스 초기화
            chart_1d = chart_1d.reset_index(drop=True) # 인덱스 초기화
            
            # 그래프 그리기(5분봉)
            self.fig_5m = plt.Figure()
            self.fig_5m.clear()
            self.canvas_5m = FigureCanvas(self.fig_5m)
            for i in reversed(range(self.graph_verticalLayout_5m.count())): # 레이아웃에 들어간 위젯 모두 지우기
                self.graph_verticalLayout_5m.itemAt(i).widget().deleteLater()
            self.graph_verticalLayout_5m.addWidget(self.canvas_5m)
            ax_5m = self.fig_5m.add_subplot(111)
            ax_5m.cla()
            ax_5m.plot(chart_5m.index, chart_5m['bb_up'], 'b-', linewidth='0.5')
            ax_5m.plot(chart_5m.index, chart_5m['20avg'], 'r-', linewidth='0.5')
            ax_5m.plot(chart_5m.index, chart_5m['bb_down'], 'b-', linewidth='0.5')
            ax_5m.plot(chart_5m.index, chart_5m['200avg'], color='black', linestyle='-', linewidth='0.5')
            if self.bohab_up_5m != 0 :
                ax_5m.axhline(self.bohab_up_5m, 0, 1, color='lightgray', linestyle='-', linewidth=1)
                ax_5m.axhline(self.bohab_down_5m, 0, 1, color='lightgray', linestyle='-', linewidth=1)
            mpl_finance.candlestick2_ohlc(ax_5m, chart_5m['open'], chart_5m['high'], chart_5m['low'], chart_5m['close'], width=0.5, colorup='r', colordown='b')
            self.canvas_5m.draw()
    
            # 그래프 그리기(1시간봉)
            self.fig_1h = plt.Figure()
            self.fig_1h.clear()
            self.canvas_1h = FigureCanvas(self.fig_1h)
            for i in reversed(range(self.graph_verticalLayout_1h.count())): # 레이아웃에 들어간 위젯 모두 지우기
                self.graph_verticalLayout_1h.itemAt(i).widget().deleteLater()
            self.graph_verticalLayout_1h.addWidget(self.canvas_1h)
            ax_1h = self.fig_1h.add_subplot(111)
            ax_1h.cla()
            ax_1h.plot(chart_1h.index, chart_1h['bb_up'], 'b-', linewidth='0.5')
            ax_1h.plot(chart_1h.index, chart_1h['20avg'], 'r-', linewidth='0.5')
            ax_1h.plot(chart_1h.index, chart_1h['bb_down'], 'b-', linewidth='0.5')
            ax_1h.plot(chart_1h.index, chart_1h['200avg'], color='black', linestyle='-', linewidth='0.5')
            if self.bohab_up_1h != 0 :
                ax_1h.axhline(self.bohab_up_1h, 0, 1, color='lightgray', linestyle='-', linewidth=1)
                ax_1h.axhline(self.bohab_down_1h, 0, 1, color='lightgray', linestyle='-', linewidth=1)
            mpl_finance.candlestick2_ohlc(ax_1h, chart_1h['open'], chart_1h['high'], chart_1h['low'], chart_1h['close'], width=0.5, colorup='r', colordown='b')
            self.canvas_1h.draw()
            
            # 그래프 그리기(4시간봉)
            self.fig_4h = plt.Figure()
            self.fig_4h.clear()
            self.canvas_4h = FigureCanvas(self.fig_4h)
            for i in reversed(range(self.graph_verticalLayout_4h.count())): # 레이아웃에 들어간 위젯 모두 지우기
                self.graph_verticalLayout_4h.itemAt(i).widget().deleteLater()
            self.graph_verticalLayout_4h.addWidget(self.canvas_4h)
            ax_4h = self.fig_4h.add_subplot(111)
            ax_4h.cla()
            ax_4h.plot(chart_4h.index, chart_4h['bb_up'], 'b-', linewidth='0.5')
            ax_4h.plot(chart_4h.index, chart_4h['20avg'], 'r-', linewidth='0.5')
            ax_4h.plot(chart_4h.index, chart_4h['bb_down'], 'b-', linewidth='0.5')
            ax_4h.plot(chart_4h.index, chart_4h['200avg'], color='black', linestyle='-', linewidth='0.5')
            if self.bohab_up_4h != 0 :
                ax_4h.axhline(self.bohab_up_4h, 0, 1, color='lightgray', linestyle='-', linewidth=1)
                ax_4h.axhline(self.bohab_down_4h, 0, 1, color='lightgray', linestyle='-', linewidth=1)
            mpl_finance.candlestick2_ohlc(ax_4h, chart_4h['open'], chart_4h['high'], chart_4h['low'], chart_4h['close'], width=0.5, colorup='r', colordown='b')
            self.canvas_4h.draw()
            
            # 그래프 그리기(1일봉)
            self.fig_1d = plt.Figure()
            self.fig_1d.clear()
            self.canvas_1d = FigureCanvas(self.fig_1d)
            for i in reversed(range(self.graph_verticalLayout_1d.count())): # 레이아웃에 들어간 위젯 모두 지우기
                self.graph_verticalLayout_1d.itemAt(i).widget().deleteLater()
            self.graph_verticalLayout_1d.addWidget(self.canvas_1d)
            ax_1d = self.fig_1d.add_subplot(111)
            ax_1d.cla()
            ax_1d.plot(chart_1d.index, chart_1d['bb_up'], 'b-', linewidth='0.5')
            ax_1d.plot(chart_1d.index, chart_1d['20avg'], 'r-', linewidth='0.5')
            ax_1d.plot(chart_1d.index, chart_1d['bb_down'], 'b-', linewidth='0.5')
            ax_1d.plot(chart_1d.index, chart_1d['5avg'], color='violet', linestyle='-', linewidth='0.5')
            ax_1d.plot(chart_1d.index, chart_1d['10avg'], color='green', linestyle='-', linewidth='0.5')
            ax_1d.plot(chart_1d.index, chart_1d['200avg'], color='black', linestyle='-', linewidth='0.5')
            if self.bohab_up_1d != 0 :
                ax_1d.axhline(self.bohab_up_1d, 0, 1, color='lightgray', linestyle='-', linewidth=1)
                ax_1d.axhline(self.bohab_down_1d, 0, 1, color='lightgray', linestyle='-', linewidth=1)
            mpl_finance.candlestick2_ohlc(ax_1d, chart_1d['open'], chart_1d['high'], chart_1d['low'], chart_1d['close'], width=0.5, colorup='r', colordown='b')
            self.canvas_1d.draw()
            
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            
    # 매수진입 버튼
    def pushButton_4_click(self): 
        # 스핀박스 숫자를 인덱스로 값 추출하기
        spinnum = self.spinBox.value()
    
        dt = self.df.iloc[spinnum]['datetime']
        cl_ago = self.df.iloc[spinnum-1]['close']
        
        width_cc = round((self.df_rank.iloc[5]['price'] / cl_ago * 100) - 100,2)
        print(width_cc)
        if width_cc > 0.8 :
            self.goalprice = round(cl_ago*1.008,2)
        elif width_cc > 0.5 :
            self.goalprice = round(cl_ago*1.005,2)
        elif width_cc > 0.2 :
            self.goalprice = self.df_rank.iloc[5]['price']
        else : 
            self.goalprice = round(cl_ago*1.002,2)
            
        self.lossprice = round(cl_ago*0.992,2)
        position = "매수"
        profit = 0
        gubun = "보유"
        
        # 테이블에 값 넣기
        row = self.tableWidget_2.rowCount()
        self.tableWidget_2.insertRow(row)
        self.tableWidget_2.setItem(row , 0, QTableWidgetItem(str(dt)))
        self.tableWidget_2.setItem(row , 1, QTableWidgetItem(position))
        self.tableWidget_2.setItem(row , 2, QTableWidgetItem(str(cl_ago)))
        self.tableWidget_2.setItem(row , 3, QTableWidgetItem(str(self.goalprice)))
        self.tableWidget_2.setItem(row , 4, QTableWidgetItem(str(self.lossprice)))
        self.tableWidget_2.setItem(row , 5, QTableWidgetItem(str(profit)))
        self.tableWidget_2.setItem(row , 6, QTableWidgetItem(gubun))
        self.tableWidget_2.scrollToBottom() # 스크롤을 제일 아래로 내린다
            
    # 매도진입 버튼
    def pushButton_5_click(self): 
        # 스핀박스 숫자를 인덱스로 값 추출하기
        spinnum = self.spinBox.value()
    
        dt = self.df.iloc[spinnum]['datetime']
        cl_ago = self.df.iloc[spinnum-1]['close']
        
        width_dd = round((self.df_rank.iloc[4]['price'] / cl_ago * 100) - 100,2)
        print(width_dd)
        if width_dd < -0.8 :
            self.goalprice = round(cl_ago*0.992,2)
        elif width_dd < -0.5 :
            self.goalprice = round(cl_ago*0.995,2)
        elif width_dd < -0.2 :
            self.goalprice = self.df_rank.iloc[4]['price']
        else : 
            self.goalprice = round(cl_ago*0.998,2)
            
        self.lossprice = round(cl_ago*1.008,2)
        position = "매도"
        profit = 0
        gubun = "보유"
        
        # 테이블에 값 넣기
        row = self.tableWidget_2.rowCount()
        self.tableWidget_2.insertRow(row)
        self.tableWidget_2.setItem(row , 0, QTableWidgetItem(str(dt)))
        self.tableWidget_2.setItem(row , 1, QTableWidgetItem(position))
        self.tableWidget_2.setItem(row , 2, QTableWidgetItem(str(cl_ago)))
        self.tableWidget_2.setItem(row , 3, QTableWidgetItem(str(self.goalprice)))
        self.tableWidget_2.setItem(row , 4, QTableWidgetItem(str(self.lossprice)))
        self.tableWidget_2.setItem(row , 5, QTableWidgetItem(str(profit)))
        self.tableWidget_2.setItem(row , 6, QTableWidgetItem(gubun))
        self.tableWidget_2.scrollToBottom() # 스크롤을 제일 아래로 내린다
    
    # 다음 버튼 클릭 시
    def pushButton_8_click(self):
        try :
            while True:
                # 스핀박스 숫자를 인덱스로 값 추출하기
                spinnum = self.spinBox.value()
                
                if len(self.df) == 0:
                    QMessageBox.information(self,'알림창','테스트 시작 버튼을 먼저 눌러주세요.')
                elif len(self.df) != len(self.df2) :
                    # 필요한 변수들 만들기
                    dt = self.df.iloc[spinnum]['datetime']
                    op = self.df.iloc[spinnum]['open']
                    hi = self.df.iloc[spinnum]['high']
                    lw = self.df.iloc[spinnum]['low']
                    cl = self.df.iloc[spinnum]['close']
                    vo = self.df.iloc[spinnum]['volume']
                    
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
                    
                    ### --------------------------------------------------------------- ###
                    ## 지지저항뚫음 파악 ##
                    dt_1h = dt - timedelta(minutes=55)
                    dt_4h = dt - timedelta(minutes=235)
                    dt_1d = dt - timedelta(minutes=1435)
                    
                    # 5분, 15분, 30분, 1시간, 4시간, 1일에서 표시할 데이터만 뽑기
                    chart_5m = self.df_5m[self.df_5m['datetime'] <= dt] # 전봉의 데이터 5-1 6-2 7-3 8-4 9-5
                    chart_1h = self.df_1h[self.df_1h['datetime'] <= dt_1h] # 전봉의 데이터
                    chart_4h = self.df_4h[self.df_4h['datetime'] <= dt_4h] # 전봉의 데이터
                    chart_1d = self.df_1d[self.df_1d['datetime'] <= dt_1d] # 전봉의 데이터
        
                    # 종가는 공통
                    add_close = self.df.iloc[spinnum]['close'] # 종가
                    if dt_1h != chart_1h.iloc[-1]['datetime'] :
                        dt_1h_start = chart_1h.iloc[-1]['datetime'] + timedelta(minutes=60)
                        temp_data = self.df[(self.df['datetime'] >= dt_1h_start) & (self.df['datetime'] <= dt)]
                        add_open_1h = temp_data.iloc[0]['open']
                        add_high_1h = float(temp_data['high'].max())
                        add_low_1h = float(temp_data['low'].min())
                        # 데이터프레임에 값 추가하기
                        chart_1h = chart_1h.append({'datetime' : dt, 'open' : add_open_1h, 'high' : add_high_1h, 'low' : add_low_1h, 'close' : add_close}, ignore_index=True)
                        chart_1h.loc[len(chart_1h)-1, '200avg'] = self.make_avgline2(chart_1h)
                        chart_1h.loc[len(chart_1h)-1, 'bb_up'], chart_1h.loc[len(chart_1h)-1, '20avg'], chart_1h.loc[len(chart_1h)-1, 'bb_down'] = self.make_BB(chart_1h)
                        chart_1h.loc[len(chart_1h)-1, 'separ'] = self.make_separ(chart_1h, "close", "200avg")
                        chart_1h.loc[len(chart_1h)-1, 'strength'] = self.make_rsi(chart_1h, 9)
                    if dt_4h != chart_4h.iloc[-1]['datetime'] :
                        dt_4h_start = chart_4h.iloc[-1]['datetime'] + timedelta(minutes=240)
                        temp_data = self.df[(self.df['datetime'] >= dt_4h_start) & (self.df['datetime'] <= dt)]
                        add_open_4h = temp_data.iloc[0]['open']
                        add_high_4h = float(temp_data['high'].max())
                        add_low_4h = float(temp_data['low'].min())
                        # 데이터프레임에 값 추가하기
                        chart_4h = chart_4h.append({'datetime' : dt, 'open' : add_open_4h, 'high' : add_high_4h, 'low' : add_low_4h, 'close' : add_close}, ignore_index=True)
                        chart_4h.loc[len(chart_4h)-1, '200avg'] = self.make_avgline2(chart_4h)
                        chart_4h.loc[len(chart_4h)-1, 'bb_up'], chart_4h.loc[len(chart_4h)-1, '20avg'], chart_4h.loc[len(chart_4h)-1, 'bb_down'] = self.make_BB(chart_4h)
                        chart_4h.loc[len(chart_4h)-1, 'separ'] = self.make_separ(chart_4h, "close", "200avg")
                        chart_4h.loc[len(chart_4h)-1, 'strength'] = self.make_rsi(chart_4h, 9)
                    if dt_1d != chart_1d.iloc[-1]['datetime'] :
                        dt_1d_start = chart_1d.iloc[-1]['datetime'] + timedelta(minutes=1440)
                        temp_data = self.df[(self.df['datetime'] >= dt_1d_start) & (self.df['datetime'] <= dt)]
                        add_open_1d = temp_data.iloc[0]['open']
                        add_high_1d = float(temp_data['high'].max())
                        add_low_1d = float(temp_data['low'].min())
                        # 데이터프레임에 값 추가하기
                        chart_1d = chart_1d.append({'datetime' : dt, 'open' : add_open_1d, 'high' : add_high_1d, 'low' : add_low_1d, 'close' : add_close}, ignore_index=True)
                        chart_1d.loc[len(chart_1d)-1, '200avg'] = self.make_avgline2(chart_1d)
                        chart_1d.loc[len(chart_1d)-1, 'bb_up'], chart_1d.loc[len(chart_1d)-1, '20avg'], chart_1d.loc[len(chart_1d)-1, 'bb_down'] = self.make_BB(chart_1d)
                        chart_1d.loc[len(chart_1d)-1, 'separ'] = self.make_separ(chart_1d, "close", "200avg")
                        chart_1d.loc[len(chart_1d)-1, 'strength'] = self.make_rsi(chart_1d, 9)
                    
                    # 7일 고저점, 15일 고저점, 30일 고저점, 3개월 고저점, 6개월 고저점 반영
                    high_7days = float(chart_1d.iloc[len(chart_1d)-7:len(chart_1d)]['high'].max()) # 7일고가
                    high_15days = float(chart_1d.iloc[len(chart_1d)-15:len(chart_1d)]['high'].max()) # 15일고가
                    high_30days = float(chart_1d.iloc[len(chart_1d)-30:len(chart_1d)]['high'].max()) # 30일고가
                    high_3mons = float(chart_1d.iloc[len(chart_1d)-90:len(chart_1d)]['high'].max()) # 1달고가
                    high_6mons = float(chart_1d.iloc[len(chart_1d)-180:len(chart_1d)]['high'].max()) # 6달고가
                    low_7days = float(chart_1d.iloc[len(chart_1d)-7:len(chart_1d)]['low'].min()) # 7일저가
                    low_15days = float(chart_1d.iloc[len(chart_1d)-15:len(chart_1d)]['low'].min()) # 15일저가
                    low_30days = float(chart_1d.iloc[len(chart_1d)-30:len(chart_1d)]['low'].min()) # 30일저가
                    low_3mons = float(chart_1d.iloc[len(chart_1d)-90:len(chart_1d)]['low'].min()) # 1달일저가
                    low_6mons = float(chart_1d.iloc[len(chart_1d)-180:len(chart_1d)]['low'].min()) # 6달저가
                    
                    df_sure = pd.DataFrame()
                    df_sure = df_sure.append({'datetime' : chart_5m.iloc[-1]['datetime'], 'price' : round(chart_5m.iloc[-1]['200avg'],2), 'gubun1' : '5M', 'gubun2' : '200EMA'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_5m.iloc[-1]['datetime'], 'price' : round(chart_5m.iloc[-1]['bb_up'],2), 'gubun1' : '5M', 'gubun2' : 'BB상단'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_5m.iloc[-1]['datetime'], 'price' : round(chart_5m.iloc[-1]['20avg'],2), 'gubun1' : '5M', 'gubun2' : '20이평'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_5m.iloc[-1]['datetime'], 'price' : round(chart_5m.iloc[-1]['bb_down'],2), 'gubun1' : '5M', 'gubun2' : 'BB하단'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_1h.iloc[-1]['datetime'], 'price' : round(chart_1h.iloc[-1]['200avg'],2), 'gubun1' : '1H', 'gubun2' : '200EMA'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_1h.iloc[-1]['datetime'], 'price' : round(chart_1h.iloc[-1]['bb_up'],2), 'gubun1' : '1H', 'gubun2' : 'BB상단'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_1h.iloc[-1]['datetime'], 'price' : round(chart_1h.iloc[-1]['20avg'],2), 'gubun1' : '1H', 'gubun2' : '20이평'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_1h.iloc[-1]['datetime'], 'price' : round(chart_1h.iloc[-1]['bb_down'],2), 'gubun1' : '1H', 'gubun2' : 'BB하단'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_4h.iloc[-1]['datetime'], 'price' : round(chart_4h.iloc[-1]['200avg'],2), 'gubun1' : '4H', 'gubun2' : '200EMA'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_4h.iloc[-1]['datetime'], 'price' : round(chart_4h.iloc[-1]['bb_up'],2), 'gubun1' : '4H', 'gubun2' : 'BB상단'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_4h.iloc[-1]['datetime'], 'price' : round(chart_4h.iloc[-1]['20avg'],2), 'gubun1' : '4H', 'gubun2' : '20이평'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_4h.iloc[-1]['datetime'], 'price' : round(chart_4h.iloc[-1]['bb_down'],2), 'gubun1' : '4H', 'gubun2' : 'BB하단'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_1d.iloc[-1]['datetime'], 'price' : round(chart_1d.iloc[-1]['200avg'],2), 'gubun1' : '1D', 'gubun2' : '200EMA'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_1d.iloc[-1]['datetime'], 'price' : round(chart_1d.iloc[-1]['bb_up'],2), 'gubun1' : '1D', 'gubun2' : 'BB상단'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_1d.iloc[-1]['datetime'], 'price' : round(chart_1d.iloc[-1]['20avg'],2), 'gubun1' : '1D', 'gubun2' : '20이평'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_1d.iloc[-1]['datetime'], 'price' : round(chart_1d.iloc[-1]['bb_down'],2), 'gubun1' : '1D', 'gubun2' : 'BB하단'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_1d.iloc[-1]['datetime'], 'price' : round(chart_1d.iloc[-2]['high'],2), 'gubun1' : '1D', 'gubun2' : '전일고점'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_1d.iloc[-1]['datetime'], 'price' : round(chart_1d.iloc[-2]['low'],2), 'gubun1' : '1D', 'gubun2' : '전일저점'}, ignore_index=True)      
                    df_sure = df_sure.append({'datetime' : chart_1d.iloc[-1]['datetime'], 'price' : round(high_7days,2), 'gubun1' : '1D', 'gubun2' : '7일고가'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_1d.iloc[-1]['datetime'], 'price' : round(high_15days,2), 'gubun1' : '1D', 'gubun2' : '15일고가'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_1d.iloc[-1]['datetime'], 'price' : round(high_30days,2), 'gubun1' : '1D', 'gubun2' : '1달고가'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_1d.iloc[-1]['datetime'], 'price' : round(high_3mons,2), 'gubun1' : '1D', 'gubun2' : '3달고가'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_1d.iloc[-1]['datetime'], 'price' : round(high_6mons,2), 'gubun1' : '1D', 'gubun2' : '6달고가'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_1d.iloc[-1]['datetime'], 'price' : round(low_7days,2), 'gubun1' : '1D', 'gubun2' : '7일저가'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_1d.iloc[-1]['datetime'], 'price' : round(low_15days,2), 'gubun1' : '1D', 'gubun2' : '15일저가'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_1d.iloc[-1]['datetime'], 'price' : round(low_30days,2), 'gubun1' : '1D', 'gubun2' : '1달저가'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_1d.iloc[-1]['datetime'], 'price' : round(low_3mons,2), 'gubun1' : '1D', 'gubun2' : '3달저가'}, ignore_index=True)
                    df_sure = df_sure.append({'datetime' : chart_1d.iloc[-1]['datetime'], 'price' : round(low_6mons,2), 'gubun1' : '1D', 'gubun2' : '6달저가'}, ignore_index=True)          
                    
                    # 고점, 저점 데이터 필터링
                    highlow_dt = dt - timedelta(minutes=100)
                    dataset_high_5m = self.df_high_5m[self.df_high_5m['datetime'] <= highlow_dt]
                    dataset_low_5m = self.df_low_5m[self.df_low_5m['datetime'] <= highlow_dt]
                    
                    # 고점, 저점 데이터프레임 정제하기
                    dataset_high_5m = dataset_high_5m[['datetime','high']]
                    dataset_high_5m['gubun1'] = '5M'
                    dataset_high_5m['gubun2'] = '전고점'
                    dataset_high_5m.columns = ['datetime', 'price', 'gubun1', 'gubun2']
                    dataset_low_5m = dataset_low_5m[['datetime', 'low']]
                    dataset_low_5m['gubun1'] = '5M'
                    dataset_low_5m['gubun2'] = '전저점'
                    dataset_low_5m.columns = ['datetime', 'price', 'gubun1', 'gubun2']
                    
                    ## 고점, 저점 데이터 append 하기
                    # 고점,저점 데이터 필터링(고점 : 현재값보다 큰값만, 저점 : 현재값보다 작은값만)
                    dataset_high_5m = dataset_high_5m[dataset_high_5m['price'] > cl]
                    dataset_low_5m = dataset_low_5m[dataset_low_5m['price'] < cl]
                    df_sure = df_sure.append(dataset_high_5m, ignore_index=True)
                    df_sure = df_sure.append(dataset_low_5m, ignore_index=True)
                    
                    # df_sure에서 상 3개, 하 3개 추출
                    ji_text = '[지지]'
                    ju_text = '[저항]'
                    dd_text = '[뚫음]'
                    df_sure = df_sure.sort_values('price', ascending=True) # 가격 순으로 정렬
                    df_sure = df_sure.reset_index(drop=True) # 인덱스 초기화
                   
                    ## 지지선 추출
                    df_sure_emp1 = df_sure[df_sure['price'] <= cl]
                    df_sure_emp1 = df_sure_emp1.reset_index(drop=True) # 인덱스 초기화
                    # 지지선들 => 볼밴 상단 제외
                    idx_sure_emp1 = df_sure_emp1[(df_sure_emp1['gubun2'] == 'BB상단')].index
                    if len(idx_sure_emp1) != 0 :
                        df_sure_emp1 = df_sure_emp1.drop(idx_sure_emp1)
                        df_sure_emp1 = df_sure_emp1.reset_index(drop=True) # 인덱스 초기화
                    
                    ## 저항선 추출
                    df_sure_emp2 = df_sure[df_sure['price'] > cl]
                    df_sure_emp2 = df_sure_emp2.reset_index(drop=True) # 인덱스 초기화
                    # 저항선들 => 볼밴 하단 제외
                    idx_sure_emp2 = df_sure_emp2[(df_sure_emp2['gubun2'] == 'BB하단')].index
                    if len(idx_sure_emp2) != 0 :
                        df_sure_emp2 = df_sure_emp2.drop(idx_sure_emp2)
                        df_sure_emp2 = df_sure_emp2.reset_index(drop=True) # 인덱스 초기화
                        
                    ## emp1, emp2 합치기
                    df_sure_emp = df_sure_emp1.append(df_sure_emp2, ignore_index=True)
                        
                    ### 현재봉의 지지선 표시하기 ###
                    for i in df_sure_emp1.index :
                        if df_sure_emp1.iloc[i]['gubun1'] == '5M' :
                            if chart_5m.iloc[-1]['close'] > chart_5m.iloc[-1]['open'] : # 일단 지지면 양봉이여야 한다.
                                if chart_5m.iloc[-1]['low'] <= df_sure_emp1.iloc[i]['price'] < chart_5m.iloc[-1]['open'] : # 현재봉
                                    ji_text += ',5M-'+df_sure_emp1.iloc[i]['gubun2']
                        elif df_sure_emp1.iloc[i]['gubun1'] == '1H' and df_sure_emp1.iloc[i]['gubun2'] != '전봉저점' :
                            if chart_1h.iloc[-1]['close'] > chart_1h.iloc[-1]['open'] : # 일단 지지면 양봉이여야 한다.
                                if chart_1h.iloc[-1]['low'] <= df_sure_emp1.iloc[i]['price'] < chart_1h.iloc[-1]['open'] : # 현재봉
                                    ji_text += ',1H-'+df_sure_emp1.iloc[i]['gubun2']
                        elif df_sure_emp1.iloc[i]['gubun1'] == '4H' and df_sure_emp1.iloc[i]['gubun2'] != '전봉저점' :
                            if chart_4h.iloc[-1]['close'] > chart_4h.iloc[-1]['open'] : # 일단 지지면 양봉이여야 한다.
                                if chart_4h.iloc[-1]['low'] <= df_sure_emp1.iloc[i]['price'] < chart_4h.iloc[-1]['open'] : # 현재봉
                                    ji_text += ',4H-'+df_sure_emp1.iloc[i]['gubun2']
                        elif df_sure_emp1.iloc[i]['gubun1'] == '1D' and df_sure_emp1.iloc[i]['gubun2'] != '전봉저점' :    
                            if chart_1d.iloc[-1]['close'] > chart_1d.iloc[-1]['open'] : # 일단 지지면 양봉이여야 한다.
                                if chart_1d.iloc[-1]['low'] <= df_sure_emp1.iloc[i]['price'] < chart_1d.iloc[-1]['open'] : # 현재봉
                                    ji_text += ',1D-'+df_sure_emp1.iloc[i]['gubun2']
                                
                    ### 현재봉의 저항선 표시하기 ###
                    for i in df_sure_emp2.index :
                        if df_sure_emp2.iloc[i]['gubun1'] == '5M' :
                            if chart_5m.iloc[-1]['close'] < chart_5m.iloc[-1]['open'] : # 일단 저항이면 움봉이여야 한다.
                                if chart_5m.iloc[-1]['high'] >= df_sure_emp2.iloc[i]['price'] > chart_5m.iloc[-1]['open'] : # 현재봉
                                    ju_text += ',5M-'+df_sure_emp2.iloc[i]['gubun2']
                        elif df_sure_emp2.iloc[i]['gubun1'] == '1H' and df_sure_emp2.iloc[i]['gubun2'] != '전봉고점' :
                            if chart_1h.iloc[-1]['close'] < chart_1h.iloc[-1]['open'] : # 일단 저항이면 움봉이여야 한다.
                                if chart_1h.iloc[-1]['high'] >= df_sure_emp2.iloc[i]['price'] > chart_1h.iloc[-1]['open'] : # 현재봉
                                    ju_text += ',1H-'+df_sure_emp2.iloc[i]['gubun2']
                        elif df_sure_emp2.iloc[i]['gubun1'] == '4H' and df_sure_emp2.iloc[i]['gubun2'] != '전봉고점' :
                            if chart_4h.iloc[-1]['close'] < chart_4h.iloc[-1]['open'] : # 일단 저항이면 움봉이여야 한다.
                                if chart_4h.iloc[-1]['high'] >= df_sure_emp2.iloc[i]['price'] > chart_4h.iloc[-1]['open'] : # 현재봉
                                    ju_text += ',4H-'+df_sure_emp2.iloc[i]['gubun2']
                        elif df_sure_emp2.iloc[i]['gubun1'] == '1D' and df_sure_emp2.iloc[i]['gubun2'] != '전봉고점' :    
                            if chart_1d.iloc[-1]['close'] < chart_1d.iloc[-1]['open'] : # 일단 저항이면 움봉이여야 한다.
                                if chart_1d.iloc[-1]['high'] >= df_sure_emp2.iloc[i]['price'] > chart_1d.iloc[-1]['open'] : # 현재봉
                                    ju_text += ',1D-'+df_sure_emp2.iloc[i]['gubun2']
                    
                    ### 현재봉이 뚫어버린 선 구하기 ###
                    for i in df_sure_emp.index :
                        if df_sure_emp.iloc[i]['gubun1'] == '5M' :
                            if chart_5m.iloc[-1]['open'] < df_sure_emp.iloc[i]['price'] < chart_5m.iloc[-1]['close'] :
                                if self.df2.iloc[-1]['close'] > self.df2.iloc[-1]['open'] : # 양봉일때
                                    if df_sure_emp.iloc[i]['gubun2'] != "BB하단": # 볼린저밴드 하단을 위로 뚫는건 제외
                                        dd_text += ',5M-'+df_sure_emp.iloc[i]['gubun2']
                            elif chart_5m.iloc[-1]['open'] > df_sure_emp.iloc[i]['price'] > chart_5m.iloc[-1]['close'] :
                                if self.df2.iloc[-1]['close'] < self.df2.iloc[-1]['open'] : # 음봉일때
                                    if df_sure_emp.iloc[i]['gubun2'] != "BB상단": # 볼린저밴드 상단을 아래로 뚫는건 제외
                                        dd_text += ',5M-'+df_sure_emp.iloc[i]['gubun2']
                        elif df_sure_emp.iloc[i]['gubun1'] == '1H' :
                            if chart_1h.iloc[-1]['open'] < df_sure_emp.iloc[i]['price'] < chart_1h.iloc[-1]['close'] :
                                if self.df2.iloc[-1]['close'] > self.df2.iloc[-1]['open'] : # 양봉일때
                                    if df_sure_emp.iloc[i]['gubun2'] != "BB하단": # 볼린저밴드 하단을 위로 뚫는건 제외
                                        dd_text += ',1H-'+df_sure_emp.iloc[i]['gubun2']
                            elif chart_1h.iloc[-1]['open'] > df_sure_emp.iloc[i]['price'] > chart_1h.iloc[-1]['close'] :
                                if self.df2.iloc[-1]['close'] < self.df2.iloc[-1]['open'] : # 음봉일때
                                    if df_sure_emp.iloc[i]['gubun2'] != "BB상단": # 볼린저밴드 상단을 아래로 뚫는건 제외
                                        dd_text += ',1H-'+df_sure_emp.iloc[i]['gubun2']
                        elif df_sure_emp.iloc[i]['gubun1'] == '4H' :
                            if chart_4h.iloc[-1]['open'] < df_sure_emp.iloc[i]['price'] < chart_4h.iloc[-1]['close'] :
                                if self.df2.iloc[-1]['close'] > self.df2.iloc[-1]['open'] : # 양봉일때
                                    if df_sure_emp.iloc[i]['gubun2'] != "BB하단": # 볼린저밴드 하단을 위로 뚫는건 제외ㄴ
                                        dd_text += ',4H-'+df_sure_emp.iloc[i]['gubun2']
                            elif chart_4h.iloc[-1]['open'] > df_sure_emp.iloc[i]['price'] > chart_4h.iloc[-1]['close'] :
                                if self.df2.iloc[-1]['close'] < self.df2.iloc[-1]['open'] : # 음봉일때
                                    if df_sure_emp.iloc[i]['gubun2'] != "BB상단": # 볼린저밴드 상단을 아래로 뚫는건 제외
                                        dd_text += ',4H-'+df_sure_emp.iloc[i]['gubun2']
                        elif df_sure_emp.iloc[i]['gubun1'] == '1D' :    
                            if chart_1d.iloc[-1]['open'] < df_sure_emp.iloc[i]['price'] < chart_1d.iloc[-1]['close'] :
                                if self.df2.iloc[-1]['close'] > self.df2.iloc[-1]['open'] : # 양봉일때
                                    if df_sure_emp.iloc[i]['gubun2'] != "BB하단": # 볼린저밴드 하단을 위로 뚫는건 제외
                                        dd_text += ',1D-'+df_sure_emp.iloc[i]['gubun2']
                            elif chart_1d.iloc[-1]['open'] > df_sure_emp.iloc[i]['price'] > chart_1d.iloc[-1]['close'] :
                                if self.df2.iloc[-1]['close'] < self.df2.iloc[-1]['open'] : # 음봉일때
                                    if df_sure_emp.iloc[i]['gubun2'] != "BB상단": # 볼린저밴드 상단을 아래로 뚫는건 제외
                                        dd_text += ',1D-'+df_sure_emp.iloc[i]['gubun2']
                    
                    # 표시할 데이터 프레임
                    df_sure_indemp = df_sure_emp[df_sure_emp['price'] <= cl]
                    ind_sure = len(df_sure_indemp) - 1
                    df_sure_rank = df_sure_emp[ind_sure-4:ind_sure+6]
                    df_sure_rank = df_sure_rank.reset_index(drop=True) # 인덱스 초기화
                        
                    # 지지저항 값 넣기
                    # 폭 = 큰값 / 작은값 * 100 - 100
                    width_aa = round((df_sure_rank.iloc[9]['price'] / cl * 100) - 100,2)
                    width_bb = round((df_sure_rank.iloc[8]['price'] / cl * 100) - 100,2)
                    width_cc = round((df_sure_rank.iloc[7]['price'] / cl * 100) - 100,2)
                    width_dd = round((df_sure_rank.iloc[6]['price'] / cl * 100) - 100,2)
                    width_ee = round((df_sure_rank.iloc[5]['price'] / cl * 100) - 100,2)
                    width_ff = round((df_sure_rank.iloc[4]['price'] / cl * 100) - 100,2)
                    width_gg = round((df_sure_rank.iloc[3]['price'] / cl * 100) - 100,2)
                    width_hh = round((df_sure_rank.iloc[2]['price'] / cl * 100) - 100,2)
                    width_ii = round((df_sure_rank.iloc[1]['price'] / cl * 100) - 100,2)
                    width_jj = round((df_sure_rank.iloc[0]['price'] / cl * 100) - 100,2)
                    
                    # 테이블(tableWidget_sure)에 값 넣기
                    self.tableWidget_sure.setItem(0 , 0, QTableWidgetItem(str(df_sure_rank.iloc[9]['gubun1']))) # 구분
                    self.tableWidget_sure.setItem(0 , 1, QTableWidgetItem(str(df_sure_rank.iloc[9]['gubun2']))) # 구분2
                    self.tableWidget_sure.setItem(0 , 2, QTableWidgetItem(str(df_sure_rank.iloc[9]['price']))) # 가격
                    self.tableWidget_sure.setItem(0 , 3, QTableWidgetItem(str(width_aa))) # 폭
                    
                    self.tableWidget_sure.setItem(1 , 0, QTableWidgetItem(str(df_sure_rank.iloc[8]['gubun1']))) # 구분
                    self.tableWidget_sure.setItem(1 , 1, QTableWidgetItem(str(df_sure_rank.iloc[8]['gubun2']))) # 구분2
                    self.tableWidget_sure.setItem(1 , 2, QTableWidgetItem(str(df_sure_rank.iloc[8]['price']))) # 가격
                    self.tableWidget_sure.setItem(1 , 3, QTableWidgetItem(str(width_bb))) # 폭
                    
                    self.tableWidget_sure.setItem(2 , 0, QTableWidgetItem(str(df_sure_rank.iloc[7]['gubun1']))) # 구분
                    self.tableWidget_sure.setItem(2 , 1, QTableWidgetItem(str(df_sure_rank.iloc[7]['gubun2']))) # 구분2
                    self.tableWidget_sure.setItem(2 , 2, QTableWidgetItem(str(df_sure_rank.iloc[7]['price']))) # 가격
                    self.tableWidget_sure.setItem(2 , 3, QTableWidgetItem(str(width_cc))) # 폭
                    
                    self.tableWidget_sure.setItem(3 , 0, QTableWidgetItem(str(df_sure_rank.iloc[6]['gubun1']))) # 구분
                    self.tableWidget_sure.setItem(3 , 1, QTableWidgetItem(str(df_sure_rank.iloc[6]['gubun2']))) # 구분2
                    self.tableWidget_sure.setItem(3 , 2, QTableWidgetItem(str(df_sure_rank.iloc[6]['price']))) # 가격
                    self.tableWidget_sure.setItem(3 , 3, QTableWidgetItem(str(width_dd))) # 폭
                    
                    self.tableWidget_sure.setItem(4 , 0, QTableWidgetItem(str(df_sure_rank.iloc[5]['gubun1']))) # 구분
                    self.tableWidget_sure.setItem(4 , 1, QTableWidgetItem(str(df_sure_rank.iloc[5]['gubun2']))) # 구분2
                    self.tableWidget_sure.setItem(4 , 2, QTableWidgetItem(str(df_sure_rank.iloc[5]['price']))) # 가격
                    self.tableWidget_sure.setItem(4 , 3, QTableWidgetItem(str(width_ee))) # 폭
                    
                    self.tableWidget_sure.setItem(5 , 0, QTableWidgetItem('---------------')) # 구분
                    self.tableWidget_sure.setItem(5 , 1, QTableWidgetItem('---------------')) # 구분2
                    self.tableWidget_sure.setItem(5 , 2, QTableWidgetItem(str(cl))) # 가격
                    self.tableWidget_sure.setItem(5 , 3, QTableWidgetItem('---------------')) # 폭
                    
                    self.tableWidget_sure.setItem(6 , 0, QTableWidgetItem(str(df_sure_rank.iloc[4]['gubun1']))) # 구분
                    self.tableWidget_sure.setItem(6 , 1, QTableWidgetItem(str(df_sure_rank.iloc[4]['gubun2']))) # 구분2
                    self.tableWidget_sure.setItem(6 , 2, QTableWidgetItem(str(df_sure_rank.iloc[4]['price']))) # 가격
                    self.tableWidget_sure.setItem(6 , 3, QTableWidgetItem(str(width_ff))) # 폭
                    
                    self.tableWidget_sure.setItem(7 , 0, QTableWidgetItem(str(df_sure_rank.iloc[3]['gubun1']))) # 구분
                    self.tableWidget_sure.setItem(7 , 1, QTableWidgetItem(str(df_sure_rank.iloc[3]['gubun2']))) # 구분2
                    self.tableWidget_sure.setItem(7 , 2, QTableWidgetItem(str(df_sure_rank.iloc[3]['price']))) # 가격
                    self.tableWidget_sure.setItem(7 , 3, QTableWidgetItem(str(width_gg))) # 폭
                    
                    self.tableWidget_sure.setItem(8 , 0, QTableWidgetItem(str(df_sure_rank.iloc[2]['gubun1']))) # 구분
                    self.tableWidget_sure.setItem(8 , 1, QTableWidgetItem(str(df_sure_rank.iloc[2]['gubun2']))) # 구분2
                    self.tableWidget_sure.setItem(8 , 2, QTableWidgetItem(str(df_sure_rank.iloc[2]['price']))) # 가격
                    self.tableWidget_sure.setItem(8 , 3, QTableWidgetItem(str(width_hh))) # 폭
                    
                    self.tableWidget_sure.setItem(9 , 0, QTableWidgetItem(str(df_sure_rank.iloc[1]['gubun1']))) # 구분
                    self.tableWidget_sure.setItem(9 , 1, QTableWidgetItem(str(df_sure_rank.iloc[1]['gubun2']))) # 구분2
                    self.tableWidget_sure.setItem(9 , 2, QTableWidgetItem(str(df_sure_rank.iloc[1]['price']))) # 가격
                    self.tableWidget_sure.setItem(9 , 3, QTableWidgetItem(str(width_ii))) # 폭
                    
                    self.tableWidget_sure.setItem(10 , 0, QTableWidgetItem(str(df_sure_rank.iloc[0]['gubun1']))) # 구분
                    self.tableWidget_sure.setItem(10 , 1, QTableWidgetItem(str(df_sure_rank.iloc[0]['gubun2']))) # 구분2
                    self.tableWidget_sure.setItem(10 , 2, QTableWidgetItem(str(df_sure_rank.iloc[0]['price']))) # 가격
                    self.tableWidget_sure.setItem(10 , 3, QTableWidgetItem(str(width_jj))) # 폭
                    
                    ### --------------------------------------------------------------- ###
                    ## 그래프 그리기 준비 ##
                    self.fig = plt.Figure()
                    self.fig.clear()
                    self.canvas = FigureCanvas(self.fig)
                    for i in reversed(range(self.graph_verticalLayout.count())): # 레이아웃에 들어간 위젯 모두 지우기
                        self.graph_verticalLayout.itemAt(i).widget().deleteLater()
                    self.graph_verticalLayout.addWidget(self.canvas)
            
                    # 그릴 그래프의 범위 구하기
                    num_df = len(self.df2) # 테이블에 표시되는 데이터의 수
                    num_display = 100 # 그래프에 표시될 봉의 수
                    if num_df > num_display :
                        df_bar = self.df2[num_df-num_display : num_df]
                    else :
                        df_bar = self.df2
                        
                    # 인덱스 초기화하기
                    df_bar = df_bar.reset_index(drop=True) # 인덱스 초기화
                    
                    ### --------------------------------------------------------------- ###
                    ## 단기추세구하기 ##
                    # 선정봉 구하기
                    select_bar = viewtrend_cls.exe_viewtrend(self, self.df2)
                    
                    # 추세 구하기
                    self.lineEdit_trendsig.setText('없음')
                    bohab_up = 0
                    bohab_down = 0
                    if select_bar == '없음' : # 아직 봉이 적어서 추세가 없다면 보합구간으로 결정하자
                        ### 그래프 그리기 ###
                        ax_1m_iv = self.fig.add_subplot(111)
                        ax_1m_iv.cla()
                        ax_1m_iv.plot(df_bar.index, df_bar['bb_up'], color='black', linestyle='-', linewidth='1')
                        ax_1m_iv.plot(df_bar.index, df_bar['20avg'], color='red', linestyle='-', linewidth='0.5')
                        ax_1m_iv.plot(df_bar.index, df_bar['200avg'], color='violet', linestyle='-', linewidth='1')
                        ax_1m_iv.plot(df_bar.index, df_bar['bb_down'], color='black', linestyle='-', linewidth='1')
                        mpl_finance.candlestick2_ohlc(ax_1m_iv, df_bar['open'], df_bar['high'], df_bar['low'], df_bar['close'], width=0.5, colorup='r', colordown='b')
                        self.canvas.draw()
                    else :
                        # 선정폭 구하기
                        select_up = self.df2[self.df2['datetime'] == select_bar]['high'].iloc[-1]
                        select_down = self.df2[self.df2['datetime'] == select_bar]['low'].iloc[-1]
                        
                        # 필요한 변수선언
                        trendsig_20avg = self.df2.iloc[-1]['20avg']
                        trendsig_bbup = self.df2.iloc[-1]['bb_up']
                        trendsig_bbdown = self.df2.iloc[-1]['bb_down']
                        
                        # 시작 : 볼밴을 뚫는 봉의 출현 = 선정봉
                        # 선정봉이 20일선위 vs 선정봉이 20일선 아래 vs 선정봉이 없음 : 보합권
                        if self.lineEdit_trend.text() == '상승보합구간' or self.lineEdit_trend.text() == '상승추세구간' or (self.lineEdit_trend.text() == '' and cl > trendsig_20avg) :
                            bohab_up = max(trendsig_bbup, select_up)
                            bohab_down = min(trendsig_20avg, select_down)
                            if bohab_down > cl :
                                print('1')
                                self.lineEdit_trendsig.setText('하락전환신호')
                                self.lineEdit_trend.setText('하락전환전보합구간')
                            elif bohab_up < cl : 
                                self.lineEdit_trendsig.setText('상승지속신호')
                                self.lineEdit_trend.setText('상승추세구간')
                                print('2')
                            elif bohab_up >= cl >= bohab_down :
                                self.lineEdit_trend.setText('상승보합구간')
                                print('3')
                                
                        elif self.lineEdit_trend.text() == '상승보합구간(RE)' : # 하락전환전보합구간에서 20일선을 다시 뚫고 올라갔을 때 RE를 붙임
                            bohab_up = max(trendsig_bbup, select_up)
                            bohab_down = min(trendsig_20avg, select_down)
                            if bohab_down > cl :
                                self.lineEdit_trendsig.setText('보합구간전환신호')
                                self.lineEdit_trend.setText('보합구간')
                                print('4')
                            elif bohab_up < cl : 
                                self.lineEdit_trendsig.setText('상승지속신호')
                                self.lineEdit_trend.setText('상승추세구간') 
                                print('5')
                            elif bohab_up >= cl >= bohab_down :
                                self.lineEdit_trend.setText('상승보합구간(RE)')
                                print('6')
                                
                        elif self.lineEdit_trend.text() == '하락전환전보합구간' :
                            bohab_up = trendsig_20avg
                            bohab_down = trendsig_bbdown
                            if bohab_down > cl : 
                                self.lineEdit_trendsig.setText('하락지속신호')
                                self.lineEdit_trend.setText('하락추세구간')
                                print('7')
                            elif cl > bohab_up : # 하락전환전보합구간에서 다시 20일선을 위로 뚫음 => 상승보합구간으로 변경
                                self.lineEdit_trend.setText('상승보합구간(RE)')
                                print('8')
                            elif bohab_up >= cl >= bohab_down :
                                self.lineEdit_trend.setText('하락전환전보합구간')
                                print('9')
                                
                        elif self.lineEdit_trend.text() == '보합구간' :
                            bohab_up = trendsig_bbup # or 보합구간 최대값)
                            bohab_down = trendsig_bbdown # or 보합구간 최소값)
                            if bohab_up < cl : 
                                self.lineEdit_trendsig.setText('보합후상승신호')
                                self.lineEdit_trend.setText('상승추세구간') 
                                print('10')
                            elif bohab_down > cl : 
                                self.lineEdit_trendsig.setText('보합후하락신호')
                                self.lineEdit_trend.setText('하락추세구간') 
                                print('11')
                            elif bohab_up >= cl >= bohab_down :
                                self.lineEdit_trend.setText('보합구간')
                                print('12')
                                
                        elif self.lineEdit_trend.text() == '하락보합구간' or self.lineEdit_trend.text() == '하락추세구간' or (self.lineEdit_trend.text() == '' and cl < trendsig_20avg):
                            bohab_up = max(trendsig_20avg, select_up)
                            bohab_down = min(trendsig_bbdown, select_down) # 볼밴하단과 선정폭하단중 작은값
                            if bohab_down > cl :
                                self.lineEdit_trendsig.setText('하락지속신호')
                                self.lineEdit_trend.setText('하락추세구간')
                                print('13')
                            elif bohab_up < cl :
                                self.lineEdit_trendsig.setText('상승전환신호')
                                self.lineEdit_trend.setText('상승전환전보합구간')
                                print('14')
                            elif bohab_up >= cl >= bohab_down :
                                self.lineEdit_trend.setText('하락보합구간')
                                print('15')
                                
                        elif self.lineEdit_trend.text() == '하락보합구간(RE)' : 
                            bohab_up = max(trendsig_20avg, select_up) # 20일선과 선정폭상단중 큰값
                            bohab_down = min(trendsig_bbdown, select_down) # 볼밴하단과 선정폭하단중 작은값
                            if bohab_down > cl :
                                self.lineEdit_trendsig.setText('하락지속신호')
                                self.lineEdit_trend.setText('하락추세구간') 
                                print('16')
                            elif bohab_up < cl : 
                                self.lineEdit_trendsig.setText('보합구간전환신호')
                                self.lineEdit_trend.setText('보합구간')
                                print('17')
                            elif bohab_up >= cl >= bohab_down :
                                self.lineEdit_trend.setText('하락보합구간(RE)')
                                print('18')
                                
                        elif self.lineEdit_trend.text() == '상승전환전보합구간' :
                            bohab_up = trendsig_bbup # 볼밴상단
                            bohab_down = trendsig_20avg # 20일선
                            if bohab_down > cl : 
                                self.lineEdit_trend.setText('하락보합구간(RE)')
                                print('19')
                            elif cl > bohab_up : 
                                self.lineEdit_trendsig.setText('상승지속신호')
                                self.lineEdit_trend.setText('상승추세구간')
                                print('20')
                            elif bohab_up >= cl >= bohab_down :
                                self.lineEdit_trend.setText('상승전환전보합구간')
                                print('21')
                        
                        ### 그래프 그리기 ###
                        # 선정폭 : 추세 or 추세보합일땐 선정봉의 폭 / 보합구간일 땐
                        ax_1m_iv = self.fig.add_subplot(111)
                        ax_1m_iv.cla()
                        ax_1m_iv.plot(df_bar.index, df_bar['bb_up'], color='black', linestyle='-', linewidth='1')
                        ax_1m_iv.plot(df_bar.index, df_bar['20avg'], color='red', linestyle='-', linewidth='0.5')
                        ax_1m_iv.plot(df_bar.index, df_bar['200avg'], color='violet', linestyle='-', linewidth='1')
                        ax_1m_iv.plot(df_bar.index, df_bar['bb_down'], color='black', linestyle='-', linewidth='1')
                        ax_1m_iv.axhline(bohab_up, 0, 1, color='gray', linestyle='-', linewidth=1)
                        ax_1m_iv.axhline(bohab_down, 0, 1, color='gray', linestyle='-', linewidth=1)
                        mpl_finance.candlestick2_ohlc(ax_1m_iv, df_bar['open'], df_bar['high'], df_bar['low'], df_bar['close'], width=0.5, colorup='r', colordown='b')
                        self.canvas.draw()
                    
                    ### --------------------------------------------------------------- ###
                    ## 단기추세구하기(전체봉) ##
                    # 선정봉구하기
                    self.select_bar_1h = viewtrend_cls.exe_viewtrend(self, chart_1h)
                    self.select_bar_4h = viewtrend_cls.exe_viewtrend(self, chart_4h)
                    self.select_bar_1d = viewtrend_cls.exe_viewtrend(self, chart_1d)
                    
                    # 추세구하기
                    if self.select_bar_1h != '없음' :
                        self.select_result_1h, self.bohab_up_1h, self.bohab_down_1h = searchtrend_cls.exe_searchtrend(self, chart_1h, self.select_bar_1h)
                    if self.select_bar_4h != '없음' :
                        self.select_result_4h, self.bohab_up_4h, self.bohab_down_4h = searchtrend_cls.exe_searchtrend(self, chart_4h, self.select_bar_4h)
                    if self.select_bar_1d != '없음' :
                        self.select_result_1d, self.bohab_up_1d, self.bohab_down_1d = searchtrend_cls.exe_searchtrend(self, chart_1d, self.select_bar_1d)
                    
                    # 추세입력하기
                    self.lineEdit_trend1h.setText(self.select_result_1h)
                    self.lineEdit_trend4h.setText(self.select_result_4h)
                    self.lineEdit_trend1d.setText(self.select_result_1d)
                    
                    ### --------------------------------------------------------------- ###
                    ## 투자봉 정보 넣기 ##
                    '''
                    self.lineEdit_stren1m.setText(str(self.df2.iloc[-1]['strength']))
                    
                    ## 클리어하기
                    self.lineEdit_stren1m_2.clear()
                    
                    ## 과이탈, 과침체 넣기 
                    if self.df2.iloc[-1]['strength'] >= 70 :
                        self.lineEdit_stren1m_2.setText('과이탈')
                    elif self.df2.iloc[-1]['strength'] <= 30 :
                        self.lineEdit_stren1m_2.setText('과침체')
                        
                    ## 거래량 넣기
                    volval = round(self.df2.iloc[-1]['volume'], 2)
                    volavg = round(self.df2['volume'].mean(), 2) # 거래량 평균
                    volbae = round(volval / volavg,2)
                    self.lineEdit_volume.setText(str(volval))
                    self.lineEdit_volume_2.setText(str(volavg))
                    self.lineEdit_volume_3.setText(str(volbae))
                    '''
                    
                    ## 지지저항뚫음 넣기
                    self.lineEdit_su.setText(ji_text) # 텍스트 상자에 값을 넣음
                    self.lineEdit_re.setText(ju_text) # 텍스트 상자에 값을 넣음
                    self.lineEdit_sp.setText(dd_text) # 텍스트 상자에 값을 넣음
                    
                    # 매수, 매도 가격 구하기 위해 전역변수 초기화하기
                    self.df_rank = df_sure_rank
                    
                    ### --------------------------------------------------------------- ###
                    ## 전체봉 정보 넣기 ##
                    # 양봉음봉
                    pm_bar_1h = ''
                    pm_bar_4h = ''
                    pm_bar_1d = ''
                    if chart_1h.iloc[-1]['close'] > chart_1h.iloc[-1]['open'] : # 양봉일때
                        pm_bar_1h = '양봉'
                    elif chart_1h.iloc[-1]['close'] < chart_1h.iloc[-1]['open'] : # 음봉일때
                        pm_bar_1h = '음봉'
                    else : # 십자가일때
                        pm_bar_1h = '십자가'
                    
                    if chart_4h.iloc[-1]['close'] > chart_4h.iloc[-1]['open'] : # 양봉일때
                        pm_bar_4h = '양봉'
                    elif chart_4h.iloc[-1]['close'] < chart_4h.iloc[-1]['open'] : # 음봉일때
                        pm_bar_4h = '음봉'
                    else : # 십자가일때
                        pm_bar_4h = '십자가'
                    
                    if chart_1d.iloc[-1]['close'] > chart_1d.iloc[-1]['open'] : # 양봉일때
                        pm_bar_1d = '양봉'
                    elif chart_1d.iloc[-1]['close'] < chart_1d.iloc[-1]['open'] : # 음봉일때
                        pm_bar_1d = '음봉'
                    else : # 십자가일때
                        pm_bar_1d = '십자가'
                    
                    # 고저% = 볼린저밴드 상~하단과 주가의 퍼센트 : 상단 근접시 100, 하단 근접시 0에 수렴
                    bb_val_1h = chart_1h.iloc[-1]['bb_up'] - chart_1h.iloc[-1]['bb_down']
                    bb_val_4h = chart_4h.iloc[-1]['bb_up'] - chart_4h.iloc[-1]['bb_down']
                    bb_val_1d = chart_1d.iloc[-1]['bb_up'] - chart_1d.iloc[-1]['bb_down']
                    bb_close_1h = round((chart_1h.iloc[-1]['close'] - chart_1h.iloc[-1]['bb_down']) / bb_val_1h * 100,0)
                    bb_close_4h = round((chart_4h.iloc[-1]['close'] - chart_4h.iloc[-1]['bb_down']) / bb_val_4h * 100,0)
                    bb_close_1d = round((chart_1d.iloc[-1]['close'] - chart_1d.iloc[-1]['bb_down']) / bb_val_1d * 100,0)
                    
                    # 양봉음봉 입력하기
                    self.lineEdit_trend1h_2.setText(pm_bar_1h)
                    self.lineEdit_trend4h_2.setText(pm_bar_4h)
                    self.lineEdit_trend1d_2.setText(pm_bar_1d)
                    
                    # 고저 % 입력하기
                    self.lineEdit_trend1h_3.setText(str(bb_close_1h))
                    self.lineEdit_trend4h_3.setText(str(bb_close_4h))
                    self.lineEdit_trend1d_3.setText(str(bb_close_1d))

                    
                    ### --------------------------------------------------------------- ###
                    ## [RESULT]의 결과 테이블에 값 넣기 ##
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
                                        
                                    if lw <= float(item3.text()) :
                                        self.tableWidget_2.setItem(i , 6, QTableWidgetItem("손절"))
                            
                                elif item.text() == '매도' :            
                                    perpri = round(float(item1.text())/cl * 100 - 100, 2)
                                    self.tableWidget_2.setItem(i , 5, QTableWidgetItem(str(perpri)))
                                    if cl <= float(item2.text()) :
                                        self.tableWidget_2.setItem(i , 6, QTableWidgetItem("수익"))
                                        
                                    if hi >= float(item3.text()) :
                                        self.tableWidget_2.setItem(i , 6, QTableWidgetItem("손절"))
                    
                    ### --------------------------------------------------------------- ###
                    ## 신호 파악하기 ##
                    if len(self.df2) >= 3 :
                        if self.df2.iloc[-2]['macd'] < self.df2.iloc[-2]['macd_signal'] and self.df2.iloc[-1]['macd'] > self.df2.iloc[-1]['macd_signal'] : # 골드크로스
                            self.textEdit_signal.append(str(dt) + ' macd 골크')
                            break
                        elif self.df2.iloc[-2]['macd'] > self.df2.iloc[-2]['macd_signal'] and self.df2.iloc[-1]['macd'] < self.df2.iloc[-1]['macd_signal'] : # 데드크로스
                            self.textEdit_signal.append(str(dt) + ' macd 데크')
                            break
                    
                    if self.comboBox_mode.currentText() == '수동' :
                        break
                
                else :
                    break
                    
        except Exception as e:
            print(e)
            print(traceback.format_exc())