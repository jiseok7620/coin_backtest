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
from coin_invest_backtest.main_chart import main_chart_cls
import traceback
from coin_invest_backtest.maxLine import maxLine_cls
from coin_invest_backtest.minLine import minLine_cls

form_secondwindow = uic.loadUiType("second.ui")[0] #두 번째창 ui

class main_second_cls(QDialog, QWidget, form_secondwindow):
    def __init__(self, dataset, dateset_5m, dateset_15m, dateset_30m, dateset_1h, dateset_4h, dataset_1d):
        super(main_second_cls, self).__init__()
        self.setupUi(self)
        self.show() # 두번째창 실행

        # 전역변수선언
        self.df = dataset # 전체 데이터 저장(1분 데이터)
        self.df2 = pd.DataFrame() # 데이터 1행씩 추가
        self.df_5m = dateset_5m # 5분 데이터 저장
        self.df_15m = dateset_15m # 15분 데이터 저장
        self.df_30m = dateset_30m # 30분 데이터 저장
        self.df_1h = dateset_1h # 1시간 데이터 저장
        self.df_4h = dateset_4h # 4시간 데이터 저장
        self.df_1d = dataset_1d # 일봉 데이터 저장
        self.xlay = 0 # 그래프 x축 증가데이터
        self.arr_xlay = [] # 그래프 x축 데이터 배열
        self.arr_ylay = [] # 그래프 y축 데이터 배열
        self.arr_datemax = [] # 고점의 날짜를 넣음
        self.arr_max = [] # 고점의 배열
        self.arr_datemin = [] # 저점의 날짜를 넣음
        self.arr_min = [] # 저점의 배열
        self.ddtm = datetime.strptime(str(self.df.iloc[0]['datetime']), '%Y-%m-%d %H:%M:%S') # 당일 시간
        self.ddtime = self.ddtm - timedelta(days=1) # 전일 시간
        self.agohigh = round(self.df_1d[self.df_1d['datetime']== self.ddtime]['high'].iloc[-1], 2) # 전일고가
        self.agolow = round(self.df_1d[self.df_1d['datetime']== self.ddtime]['low'].iloc[-1], 2) # 전일저가
        self.nowopen = round(self.df_1d[self.df_1d['datetime']== self.ddtm]['open'].iloc[-1], 2) # 당일 시가
        self.agovariance = round((self.agohigh - self.agolow) / 2, 2) # 변동폭 = (전일최고 - 전일최저) / 2
        self.nowhighex = round(self.nowopen + self.agovariance, 2) # 당일예상고가
        self.nowlowex = round(self.nowopen - self.agovariance, 2) # 당일예상저가
        
        # 고점, 저점 데이터프레임 만들기
        self.df_high_1m = maxLine_cls.exe_maxLine(self, self.df, 20)
        self.df_high_5m = maxLine_cls.exe_maxLine(self, self.df_5m, 20)
        self.df_high_15m = maxLine_cls.exe_maxLine(self, self.df_15m, 20)
        self.df_high_30m = maxLine_cls.exe_maxLine(self, self.df_30m, 20)
        self.df_high_1h = maxLine_cls.exe_maxLine(self, self.df_1h, 20)
        self.df_high_4h = maxLine_cls.exe_maxLine(self, self.df_4h, 20)
        self.df_high_1d = maxLine_cls.exe_maxLine(self, self.df_1d, 20)
        self.df_low_1m = minLine_cls.exe_minLine(self, self.df, 20)
        self.df_low_5m = minLine_cls.exe_minLine(self, self.df_5m, 20)
        self.df_low_15m = minLine_cls.exe_minLine(self, self.df_15m, 20)
        self.df_low_30m = minLine_cls.exe_minLine(self, self.df_30m, 20)
        self.df_low_1h = minLine_cls.exe_minLine(self, self.df_1h, 20)
        self.df_low_4h = minLine_cls.exe_minLine(self, self.df_4h, 20)
        self.df_low_1d = minLine_cls.exe_minLine(self, self.df_1d, 20)
        
        ## 버튼 클릭 시 함수와 연결 모음 ##
        self.pushButton_8.clicked.connect(self.pushButton_8_click) # 다음 버튼
        self.pushButton_4.clicked.connect(self.pushButton_4_click) # 매수진입버튼
        self.pushButton_5.clicked.connect(self.pushButton_5_click) # 매도진입버튼
        self.push_chartview.clicked.connect(self.push_chartview_click) # 차트보기버튼
        self.push_chartview2.clicked.connect(self.push_chartview2_click) # 차트보기버튼2
        
        ##----------------------------------------------------------------------------##
        ## TableWidget에서 Cell이 클릭 되었을 때 기능 실행
        self.tableWidget_2.cellClicked.connect(self.tablewidget2_cellclicked_event)
    
    # 직선의 방정식 함수
    def line_equation(self, x_val, incl, y_val):
        result = round(incl*x_val + y_val,2)
        return result
    
    # 차트 띄우기 함수
    def open_chartwindow(self,chart_dataset, chart_viewtime):
        try :
            # 그래프 그리기2
            self.fig2 = plt.Figure()
            self.fig2.clear()
            self.canvas2 = FigureCanvas(self.fig2)
            for i in reversed(range(self.graph_verticalLayout_2.count())): # 레이아웃에 들어간 위젯 모두 지우기
                self.graph_verticalLayout_2.itemAt(i).widget().deleteLater()
            self.graph_verticalLayout_2.addWidget(self.canvas2)
            
            # 인덱스 초기화
            chart_dataset = chart_dataset.reset_index(drop=True) # 인덱스 초기화 
            
            # 인덱스 찾기
            ind = chart_dataset[chart_dataset['datetime'] == chart_viewtime].index[0] # 해당 시간의  인덱스
            
            # 그래프 그리기
            ax = self.fig2.add_subplot(111)
            ax.cla()
            ax.axvline(ind, 0, 1, color='lightgray', linestyle='--', linewidth=1) # 진입봉 표시하기
            mpl_finance.candlestick2_ohlc(ax, chart_dataset['open'], chart_dataset['high'], chart_dataset['low'], chart_dataset['close'], width=0.5, colorup='r', colordown='b')
            self.canvas2.draw()
            
        except Exception as e:
            print(e)
    
    # Cell 클릭 시 datetime을 lineedit에 넣기
    def tablewidget2_cellclicked_event(self):
        cur_row = self.tableWidget_2.currentRow() # 현재 선택하고 있는 항목의 행을 반환합니다.
        sel_dt = self.tableWidget_2.item(cur_row, 0) # 선택한 행의 datetime을 반환 item형식
        value = sel_dt.text() # item형식을 text로 반환
        self.lineEdit_selectrow.setText(str(value)) # 텍스트 상자에 값을 넣음
        
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
    
    # 차트보기버튼2 클릭시
    def push_chartview2_click(self):
        try : 
            # 스핀박스 숫자를 인덱스로 값 추출하기(: -1을 해야됨 - 이미 1이 증가되어있는상태라서)
            spinnum = self.spinBox.value() - 1
            
            # 필요한 변수 만들기
            dt = self.df.iloc[spinnum]['datetime']
            
            # 5분, 15분, 30분, 1시간, 4시간, 1일에서 표시할 데이터만 뽑기
            chart_5m = self.df_5m[self.df_5m['datetime'] <= dt] # 전봉의 데이터
            chart_15m = self.df_15m[self.df_15m['datetime'] <= dt] # 전봉의 데이터
            chart_30m = self.df_30m[self.df_30m['datetime'] <= dt] # 전봉의 데이터
            chart_1h = self.df_1h[self.df_1h['datetime'] <= dt] # 전봉의 데이터
            chart_4h = self.df_4h[self.df_4h['datetime'] <= dt] # 전봉의 데이터
            chart_1d = self.df_1d[self.df_1d['datetime'] <= dt] # 전봉의 데이터
            
            # 이중 n개만 표시하도록 하기
            display_chart2_num = self.spinBox_chartview2.value()
            chart_5m = chart_5m[len(chart_5m) - display_chart2_num : len(chart_5m) + 1]
            chart_15m = chart_15m[len(chart_15m) - display_chart2_num : len(chart_15m) + 1]
            chart_30m = chart_30m[len(chart_30m) - display_chart2_num : len(chart_30m) + 1]
            chart_1h = chart_1h[len(chart_1h) - display_chart2_num : len(chart_1h) + 1]
            chart_4h = chart_4h[len(chart_4h) - display_chart2_num : len(chart_4h) + 1]
            chart_1d = chart_1d[len(chart_1d) - display_chart2_num : len(chart_1d) + 1]
            
            # 인덱스 초기화
            chart_5m = chart_5m.reset_index(drop=True) # 인덱스 초기화
            chart_15m = chart_15m.reset_index(drop=True) # 인덱스 초기화
            chart_30m = chart_30m.reset_index(drop=True) # 인덱스 초기화
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
            mpl_finance.candlestick2_ohlc(ax_5m, chart_5m['open'], chart_5m['high'], chart_5m['low'], chart_5m['close'], width=0.5, colorup='r', colordown='b')
            self.canvas_5m.draw()
    
            # 그래프 그리기(15분봉)
            self.fig_15m = plt.Figure()
            self.fig_15m.clear()
            self.canvas_15m = FigureCanvas(self.fig_15m)
            for i in reversed(range(self.graph_verticalLayout_15m.count())): # 레이아웃에 들어간 위젯 모두 지우기
                self.graph_verticalLayout_15m.itemAt(i).widget().deleteLater()
            self.graph_verticalLayout_15m.addWidget(self.canvas_15m)
            ax_15m = self.fig_15m.add_subplot(111)
            ax_15m.cla()
            ax_15m.plot(chart_15m.index, chart_15m['bb_up'], 'b-', linewidth='0.5')
            ax_15m.plot(chart_15m.index, chart_15m['20avg'], 'r-', linewidth='0.5')
            ax_15m.plot(chart_15m.index, chart_15m['bb_down'], 'b-', linewidth='0.5')
            mpl_finance.candlestick2_ohlc(ax_15m, chart_15m['open'], chart_15m['high'], chart_15m['low'], chart_15m['close'], width=0.5, colorup='r', colordown='b')
            self.canvas_15m.draw()
            
            # 그래프 그리기(30분봉)
            self.fig_30m = plt.Figure()
            self.fig_30m.clear()
            self.canvas_30m = FigureCanvas(self.fig_30m)
            for i in reversed(range(self.graph_verticalLayout_30m.count())): # 레이아웃에 들어간 위젯 모두 지우기
                self.graph_verticalLayout_30m.itemAt(i).widget().deleteLater()
            self.graph_verticalLayout_30m.addWidget(self.canvas_30m)
            ax_30m = self.fig_30m.add_subplot(111)
            ax_30m.cla()
            ax_30m.plot(chart_30m.index, chart_30m['bb_up'], 'b-', linewidth='0.5')
            ax_30m.plot(chart_30m.index, chart_30m['20avg'], 'r-', linewidth='0.5')
            ax_30m.plot(chart_30m.index, chart_30m['bb_down'], 'b-', linewidth='0.5')
            mpl_finance.candlestick2_ohlc(ax_30m, chart_30m['open'], chart_30m['high'], chart_30m['low'], chart_30m['close'], width=0.5, colorup='r', colordown='b')
            self.canvas_30m.draw()
            
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
            
    # 매도진입 버튼
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
        try :
            # 스핀박스 숫자를 인덱스로 값 추출하기
            spinnum = self.spinBox.value()
            
            if len(self.df) == 0:
                QMessageBox.information(self,'알림창','테스트 시작 버튼을 먼저 눌러주세요.')
            else :
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
                ## 그래프 그리기 ##
                self.fig = plt.Figure()
                self.fig.clear()
                self.canvas = FigureCanvas(self.fig)
                for i in reversed(range(self.graph_verticalLayout.count())): # 레이아웃에 들어간 위젯 모두 지우기
                    self.graph_verticalLayout.itemAt(i).widget().deleteLater()
                self.graph_verticalLayout.addWidget(self.canvas)
        
                # 그릴 그래프의 범위 구하기
                num_df = len(self.df2) # 테이블에 표시되는 데이터의 수
                num_display = 30 # 그래프에 표시될 봉의 수
                if num_df > num_display :
                    df_bar = self.df2[num_df-num_display : num_df]
                else :
                    df_bar = self.df2
                    
                # 인덱스 초기화하기
                df_bar = df_bar.reset_index(drop=True) # 인덱스 초기화
                
                # 그래프 그리기
                ax_1m_iv = self.fig.add_subplot(111)
                ax_1m_iv.cla()
                ax_1m_iv.plot(df_bar.index, df_bar['bb_up'], color='black', linestyle='-', linewidth='1')
                ax_1m_iv.plot(df_bar.index, df_bar['20avg'], color='red', linestyle='-', linewidth='0.5')
                ax_1m_iv.plot(df_bar.index, df_bar['60avg'], color='green', linestyle='-', linewidth='0.5')
                ax_1m_iv.plot(df_bar.index, df_bar['120avg'], color='blue', linestyle='-', linewidth='0.5')
                ax_1m_iv.plot(df_bar.index, df_bar['200avg'], color='violet', linestyle='-', linewidth='1')
                ax_1m_iv.plot(df_bar.index, df_bar['bb_down'], color='black', linestyle='-', linewidth='1')
                mpl_finance.candlestick2_ohlc(ax_1m_iv, df_bar['open'], df_bar['high'], df_bar['low'], df_bar['close'], width=0.5, colorup='r', colordown='b')
                self.canvas.draw()
                
                ### --------------------------------------------------------------- ###
                ## 5분~1일 데이터 추세 파악하기(볼린저밴드)
                # 5분, 15분, 30분, 1시간, 4시간, 1일에서 표시할 데이터만 뽑기
                temp_data_5m = self.df_5m[self.df_5m['datetime'] <= dt] # 전봉의 데이터
                temp_data_15m = self.df_15m[self.df_15m['datetime'] <= dt] # 전봉의 데이터
                temp_data_30m = self.df_30m[self.df_30m['datetime'] <= dt] # 전봉의 데이터
                temp_data_1h = self.df_1h[self.df_1h['datetime'] <= dt] # 전봉의 데이터
                temp_data_4h = self.df_4h[self.df_4h['datetime'] <= dt] # 전봉의 데이터
                temp_data_1d = self.df_1d[self.df_1d['datetime'] <= dt] # 전봉의 데이터
                
                # 이중 n개만 표시하도록 하기
                display_chart2_num = self.spinBox_chartview2.value()
                chart_5m = temp_data_5m[len(temp_data_5m) - display_chart2_num : len(temp_data_5m) + 1]
                chart_15m = temp_data_15m[len(temp_data_15m) - display_chart2_num : len(temp_data_15m) + 1]
                chart_30m = temp_data_30m[len(temp_data_30m) - display_chart2_num : len(temp_data_30m) + 1]
                chart_1h = temp_data_1h[len(temp_data_1h) - display_chart2_num : len(temp_data_1h) + 1]
                chart_4h = temp_data_4h[len(temp_data_4h) - display_chart2_num : len(temp_data_4h) + 1]
                chart_1d = temp_data_1d[len(temp_data_1d) - display_chart2_num : len(temp_data_1d) + 1]
                
                # 인덱스 초기화
                chart_5m = chart_5m.reset_index(drop=True) # 인덱스 초기화
                chart_15m = chart_15m.reset_index(drop=True) # 인덱스 초기화
                chart_30m = chart_30m.reset_index(drop=True) # 인덱스 초기화
                chart_1h = chart_1h.reset_index(drop=True) # 인덱스 초기화
                chart_4h = chart_4h.reset_index(drop=True) # 인덱스 초기화
                chart_1d = chart_1d.reset_index(drop=True) # 인덱스 초기화
                
                # 시간
                time_5m = chart_5m.iloc[-1]['datetime']
                time_15m = chart_15m.iloc[-1]['datetime']
                time_30m = chart_30m.iloc[-1]['datetime']
                time_1h = chart_1h.iloc[-1]['datetime']
                time_4h = chart_4h.iloc[-1]['datetime']
                time_1d = chart_1d.iloc[-1]['datetime']
                
                # 볼린저밴드 상~하단과 주가의 퍼센트 : 상단 근접시 100, 하단 근접시 0에 수렴
                # 상단 - 값 / 값 - 하단
                bb_val_5m = chart_5m.iloc[-1]['bb_up'] - chart_5m.iloc[-1]['bb_down']
                bb_val_15m = chart_15m.iloc[-1]['bb_up'] - chart_15m.iloc[-1]['bb_down']
                bb_val_30m = chart_30m.iloc[-1]['bb_up'] - chart_30m.iloc[-1]['bb_down']
                bb_val_1h = chart_1h.iloc[-1]['bb_up'] - chart_1h.iloc[-1]['bb_down']
                bb_val_4h = chart_4h.iloc[-1]['bb_up'] - chart_4h.iloc[-1]['bb_down']
                bb_val_1d = chart_1d.iloc[-1]['bb_up'] - chart_1d.iloc[-1]['bb_down']
                
                # 종가위치
                bb_close_5m = round((chart_5m.iloc[-1]['close'] - chart_5m.iloc[-1]['bb_down']) / bb_val_5m * 100,0)
                bb_close_15m = round((chart_15m.iloc[-1]['close'] - chart_15m.iloc[-1]['bb_down']) / bb_val_15m * 100,0)
                bb_close_30m = round((chart_30m.iloc[-1]['close'] - chart_30m.iloc[-1]['bb_down']) / bb_val_30m * 100,0)
                bb_close_1h = round((chart_1h.iloc[-1]['close'] - chart_1h.iloc[-1]['bb_down']) / bb_val_1h * 100,0)
                bb_close_4h = round((chart_4h.iloc[-1]['close'] - chart_4h.iloc[-1]['bb_down']) / bb_val_4h * 100,0)
                bb_close_1d = round((chart_1d.iloc[-1]['close'] - chart_1d.iloc[-1]['bb_down']) / bb_val_1d * 100,0)
                
                # 터치
                bb_touch_5m = ''
                bb_touch_15m = ''
                bb_touch_30m = ''
                bb_touch_1h = ''
                bb_touch_4h = ''
                bb_touch_1d = ''
                if chart_5m.iloc[-1]['high'] >= chart_5m.iloc[-1]['bb_up'] :
                    bb_touch_5m = '위터치'
                elif chart_5m.iloc[-1]['low'] <= chart_5m.iloc[-1]['bb_down'] : 
                    bb_touch_5m = '아래터치'
                
                if chart_15m.iloc[-1]['high'] >= chart_15m.iloc[-1]['bb_up'] :
                    bb_touch_15m = '위터치'
                elif chart_15m.iloc[-1]['low'] <= chart_15m.iloc[-1]['bb_down'] : 
                    bb_touch_15m = '아래터치'   
                
                if chart_30m.iloc[-1]['high'] >= chart_30m.iloc[-1]['bb_up'] :
                    bb_touch_30m = '위터치'
                elif chart_30m.iloc[-1]['low'] <= chart_30m.iloc[-1]['bb_down'] : 
                    bb_touch_30m = '아래터치'    
                
                if chart_1h.iloc[-1]['high'] >= chart_1h.iloc[-1]['bb_up'] :
                    bb_touch_1h = '위터치'
                elif chart_1h.iloc[-1]['low'] <= chart_1h.iloc[-1]['bb_down'] : 
                    bb_touch_1h = '아래터치'
                
                if chart_4h.iloc[-1]['high'] >= chart_4h.iloc[-1]['bb_up'] :
                    bb_touch_4h = '위터치'
                elif chart_4h.iloc[-1]['low'] <= chart_4h.iloc[-1]['bb_down'] : 
                    bb_touch_4h = '아래터치'
                
                if chart_1d.iloc[-1]['high'] >= chart_1d.iloc[-1]['bb_up'] :
                    bb_touch_1d = '위터치'
                elif chart_1d.iloc[-1]['low'] <= chart_1d.iloc[-1]['bb_down'] : 
                    bb_touch_1d = '아래터치'
                
                # 구분
                if chart_5m.iloc[-1]['close'] >= chart_5m.iloc[-1]['open'] :
                    bb_gubun_5m = '양봉'
                else : 
                    bb_gubun_5m = '음봉'
                if chart_15m.iloc[-1]['close'] >= chart_15m.iloc[-1]['open'] :
                    bb_gubun_15m = '양봉'
                else : 
                    bb_gubun_15m = '음봉'   
                if chart_30m.iloc[-1]['close'] >= chart_30m.iloc[-1]['open'] :
                    bb_gubun_30m = '양봉'
                else : 
                    bb_gubun_30m = '음봉'    
                if chart_1h.iloc[-1]['close'] >= chart_1h.iloc[-1]['open'] :
                    bb_gubun_1h = '양봉'
                else : 
                    bb_gubun_1h = '음봉'
                if chart_4h.iloc[-1]['close'] >= chart_4h.iloc[-1]['open'] :
                    bb_gubun_4h = '양봉'
                else : 
                    bb_gubun_4h = '음봉'
                if chart_1d.iloc[-1]['close'] >= chart_1d.iloc[-1]['open'] :
                    bb_gubun_1d = '양봉'
                else : 
                    bb_gubun_1d = '음봉'
                    
                # 상승폭
                rise_width_5m = round(((chart_5m.iloc[-1]['bb_up'] - chart_5m.iloc[-1]['close']) / chart_5m.iloc[-1]['close']) * 100 ,2)
                rise_width_15m = round(((chart_15m.iloc[-1]['bb_up'] - chart_15m.iloc[-1]['close']) / chart_15m.iloc[-1]['close']) * 100,2)
                rise_width_30m = round(((chart_30m.iloc[-1]['bb_up'] - chart_30m.iloc[-1]['close']) / chart_30m.iloc[-1]['close']) * 100,2)
                rise_width_1h = round(((chart_1h.iloc[-1]['bb_up'] - chart_1h.iloc[-1]['close']) / chart_1h.iloc[-1]['close']) * 100,2)
                rise_width_4h = round(((chart_4h.iloc[-1]['bb_up'] - chart_4h.iloc[-1]['close']) / chart_4h.iloc[-1]['close']) * 100,2)
                rise_width_1d = round(((chart_1d.iloc[-1]['bb_up'] - chart_1d.iloc[-1]['close']) / chart_1d.iloc[-1]['close']) * 100,2)
                
                # 하락폭
                de_width_5m = round(((chart_5m.iloc[-1]['bb_down'] - chart_5m.iloc[-1]['close']) / chart_5m.iloc[-1]['close']) * 100,2)
                de_width_15m = round(((chart_15m.iloc[-1]['bb_down'] - chart_15m.iloc[-1]['close']) / chart_15m.iloc[-1]['close']) * 100,2)
                de_width_30m = round(((chart_30m.iloc[-1]['bb_down'] - chart_30m.iloc[-1]['close']) / chart_30m.iloc[-1]['close']) * 100,2)
                de_width_1h = round(((chart_1h.iloc[-1]['bb_down'] - chart_1h.iloc[-1]['close']) / chart_1h.iloc[-1]['close']) * 100,2)
                de_width_4h = round(((chart_4h.iloc[-1]['bb_down'] - chart_4h.iloc[-1]['close']) / chart_4h.iloc[-1]['close']) * 100,2)
                de_width_1d = round(((chart_1d.iloc[-1]['bb_down'] - chart_1d.iloc[-1]['close']) / chart_1d.iloc[-1]['close']) * 100,2)
                
                # 테이블에 값 넣기
                self.tableWidget_BB.setItem(0 , 0, QTableWidgetItem(str(time_1d)))
                self.tableWidget_BB.setItem(0 , 1, QTableWidgetItem(str(bb_gubun_1d)))
                self.tableWidget_BB.setItem(0 , 2, QTableWidgetItem(str(bb_close_1d)))
                self.tableWidget_BB.setItem(0 , 3, QTableWidgetItem(str(bb_touch_1d)))
                if bb_touch_1d == '위터치' :
                    self.tableWidget_BB.setItem(0 , 4, QTableWidgetItem("-"))
                    self.tableWidget_BB.setItem(0 , 5, QTableWidgetItem(str(de_width_1d)))
                elif bb_touch_1d == '아래터치' :
                    self.tableWidget_BB.setItem(0 , 4, QTableWidgetItem(str(rise_width_1d)))
                    self.tableWidget_BB.setItem(0 , 5, QTableWidgetItem("-"))
                else :
                    self.tableWidget_BB.setItem(0 , 4, QTableWidgetItem(str(rise_width_1d)))
                    self.tableWidget_BB.setItem(0 , 5, QTableWidgetItem(str(de_width_1d)))
                self.tableWidget_BB.setItem(1 , 0, QTableWidgetItem(str(time_4h)))
                self.tableWidget_BB.setItem(1 , 1, QTableWidgetItem(str(bb_gubun_4h)))
                self.tableWidget_BB.setItem(1 , 2, QTableWidgetItem(str(bb_close_4h)))
                self.tableWidget_BB.setItem(1 , 3, QTableWidgetItem(str(bb_touch_4h)))
                if bb_touch_4h == '위터치' :
                    self.tableWidget_BB.setItem(1 , 4, QTableWidgetItem("-"))
                    self.tableWidget_BB.setItem(1 , 5, QTableWidgetItem(str(de_width_4h)))
                elif bb_touch_4h == '아래터치' :
                    self.tableWidget_BB.setItem(1 , 4, QTableWidgetItem(str(rise_width_4h)))
                    self.tableWidget_BB.setItem(1 , 5, QTableWidgetItem("-"))
                else :
                    self.tableWidget_BB.setItem(1 , 4, QTableWidgetItem(str(rise_width_4h)))
                    self.tableWidget_BB.setItem(1 , 5, QTableWidgetItem(str(de_width_4h)))
                self.tableWidget_BB.setItem(2 , 0, QTableWidgetItem(str(time_1h)))
                self.tableWidget_BB.setItem(2 , 1, QTableWidgetItem(str(bb_gubun_1h)))
                self.tableWidget_BB.setItem(2 , 2, QTableWidgetItem(str(bb_close_1h)))
                self.tableWidget_BB.setItem(2 , 3, QTableWidgetItem(str(bb_touch_1h)))
                if bb_touch_1h == '위터치' :
                    self.tableWidget_BB.setItem(2 , 4, QTableWidgetItem("-"))
                    self.tableWidget_BB.setItem(2 , 5, QTableWidgetItem(str(de_width_1h)))
                elif bb_touch_1h == '아래터치' :
                    self.tableWidget_BB.setItem(2 , 4, QTableWidgetItem(str(rise_width_1h)))
                    self.tableWidget_BB.setItem(2 , 5, QTableWidgetItem("-"))
                else :
                    self.tableWidget_BB.setItem(2 , 4, QTableWidgetItem(str(rise_width_1h)))
                    self.tableWidget_BB.setItem(2 , 5, QTableWidgetItem(str(de_width_1h)))
                self.tableWidget_BB.setItem(3 , 0, QTableWidgetItem(str(time_30m)))
                self.tableWidget_BB.setItem(3 , 1, QTableWidgetItem(str(bb_gubun_30m)))
                self.tableWidget_BB.setItem(3 , 2, QTableWidgetItem(str(bb_close_30m)))
                self.tableWidget_BB.setItem(3 , 3, QTableWidgetItem(str(bb_touch_30m)))
                if bb_touch_30m == '위터치' :
                    self.tableWidget_BB.setItem(3 , 4, QTableWidgetItem("-"))
                    self.tableWidget_BB.setItem(3 , 5, QTableWidgetItem(str(de_width_30m)))
                elif bb_touch_30m == '아래터치' :
                    self.tableWidget_BB.setItem(3 , 4, QTableWidgetItem(str(rise_width_30m)))
                    self.tableWidget_BB.setItem(3 , 5, QTableWidgetItem("-"))
                else :
                    self.tableWidget_BB.setItem(3 , 4, QTableWidgetItem(str(rise_width_30m)))
                    self.tableWidget_BB.setItem(3 , 5, QTableWidgetItem(str(de_width_30m)))
                self.tableWidget_BB.setItem(4 , 0, QTableWidgetItem(str(time_15m)))
                self.tableWidget_BB.setItem(4 , 1, QTableWidgetItem(str(bb_gubun_15m)))
                self.tableWidget_BB.setItem(4 , 2, QTableWidgetItem(str(bb_close_15m)))
                self.tableWidget_BB.setItem(4 , 3, QTableWidgetItem(str(bb_touch_15m)))
                if bb_touch_15m == '위터치' :
                    self.tableWidget_BB.setItem(4 , 4, QTableWidgetItem("-"))
                    self.tableWidget_BB.setItem(4 , 5, QTableWidgetItem(str(de_width_15m)))
                elif bb_touch_15m == '아래터치' :
                    self.tableWidget_BB.setItem(4 , 4, QTableWidgetItem(str(rise_width_15m)))
                    self.tableWidget_BB.setItem(4 , 5, QTableWidgetItem("-"))
                else :
                    self.tableWidget_BB.setItem(4 , 4, QTableWidgetItem(str(rise_width_15m)))
                    self.tableWidget_BB.setItem(4 , 5, QTableWidgetItem(str(de_width_15m)))
                self.tableWidget_BB.setItem(5 , 0, QTableWidgetItem(str(time_5m)))
                self.tableWidget_BB.setItem(5 , 1, QTableWidgetItem(str(bb_gubun_5m)))
                self.tableWidget_BB.setItem(5 , 2, QTableWidgetItem(str(bb_close_5m)))
                self.tableWidget_BB.setItem(5 , 3, QTableWidgetItem(str(bb_touch_5m)))
                if bb_touch_5m == '위터치' :
                    self.tableWidget_BB.setItem(5 , 4, QTableWidgetItem("-"))     
                    self.tableWidget_BB.setItem(5 , 5, QTableWidgetItem(str(de_width_5m)))
                elif bb_touch_5m == '아래터치' :
                    self.tableWidget_BB.setItem(5 , 4, QTableWidgetItem(str(rise_width_5m)))     
                    self.tableWidget_BB.setItem(5 , 5, QTableWidgetItem("-"))
                else :
                    self.tableWidget_BB.setItem(5 , 4, QTableWidgetItem(str(rise_width_5m)))     
                    self.tableWidget_BB.setItem(5 , 5, QTableWidgetItem(str(de_width_5m)))
                
                ### --------------------------------------------------------------- ###
                ## 5분~1일 데이터 추세 파악하기(고점, 저점을 이용)
                # 고점 데이터 필터링
                dataset_high_1m = self.df_high_1m[self.df_high_1m['datetime'] <= dt]
                dataset_high_5m = self.df_high_5m[self.df_high_5m['datetime'] <= dt]
                dataset_high_15m = self.df_high_15m[self.df_high_15m['datetime'] <= dt]
                dataset_high_30m = self.df_high_30m[self.df_high_30m['datetime'] <= dt]
                dataset_high_1h = self.df_high_1h[self.df_high_1h['datetime'] <= dt]
                dataset_high_4h = self.df_high_4h[self.df_high_4h['datetime'] <= dt]
                dataset_high_1d = self.df_high_1d[self.df_high_1d['datetime'] <= dt]
                
                # 저점 데이터 필터링
                dataset_low_1m = self.df_low_1m[self.df_low_1m['datetime'] <= dt]
                dataset_low_5m = self.df_low_5m[self.df_low_5m['datetime'] <= dt]
                dataset_low_5m = self.df_low_5m[self.df_low_5m['datetime'] <= dt]
                dataset_low_15m = self.df_low_15m[self.df_low_15m['datetime'] <= dt]
                dataset_low_30m = self.df_low_30m[self.df_low_30m['datetime'] <= dt]
                dataset_low_1h = self.df_low_1h[self.df_low_1h['datetime'] <= dt]
                dataset_low_4h = self.df_low_4h[self.df_low_4h['datetime'] <= dt]
                dataset_low_1d = self.df_low_1d[self.df_low_1d['datetime'] <= dt]
                
                # 이중 최신 데이터 두개만 표시하기(고점)
                before_highpoint_5m = dataset_high_5m.iloc[-2]['high']
                after_highpoint_5m = dataset_high_5m.iloc[-1]['high']
                before_highpoint_15m = dataset_high_15m.iloc[-2]['high']
                after_highpoint_15m = dataset_high_15m.iloc[-1]['high']
                before_highpoint_30m = dataset_high_30m.iloc[-2]['high']
                after_highpoint_30m = dataset_high_30m.iloc[-1]['high']
                before_highpoint_1h = dataset_high_1h.iloc[-2]['high']
                after_highpoint_1h = dataset_high_1h.iloc[-1]['high']
                before_highpoint_4h = dataset_high_4h.iloc[-2]['high']
                after_highpoint_4h = dataset_high_4h.iloc[-1]['high']
                before_highpoint_1d = dataset_high_1d.iloc[-2]['high']
                after_highpoint_1d = dataset_high_1d.iloc[-1]['high']
                
                # 고점 기울기 구하기
                inclination_high_5m = (after_highpoint_5m - before_highpoint_5m) / (self.df_5m[self.df_5m['datetime'] == dataset_high_5m.iloc[-1]['datetime']].index[0] - self.df_5m[self.df_5m['datetime'] == dataset_high_5m.iloc[-2]['datetime']].index[0])                
                inclination_high_15m = (after_highpoint_15m - before_highpoint_15m) / (self.df_15m[self.df_15m['datetime'] == dataset_high_15m.iloc[-1]['datetime']].index[0] - self.df_15m[self.df_15m['datetime'] == dataset_high_15m.iloc[-2]['datetime']].index[0])
                inclination_high_30m = (after_highpoint_30m - before_highpoint_30m) / (self.df_30m[self.df_30m['datetime'] == dataset_high_30m.iloc[-1]['datetime']].index[0] - self.df_30m[self.df_30m['datetime'] == dataset_high_30m.iloc[-2]['datetime']].index[0])
                inclination_high_1h = (after_highpoint_1h - before_highpoint_1h) / (self.df_1h[self.df_1h['datetime'] == dataset_high_1h.iloc[-1]['datetime']].index[0] - self.df_1h[self.df_1h['datetime'] == dataset_high_1h.iloc[-2]['datetime']].index[0])
                inclination_high_4h = (after_highpoint_4h - before_highpoint_4h) / (self.df_4h[self.df_4h['datetime'] == dataset_high_4h.iloc[-1]['datetime']].index[0] - self.df_4h[self.df_4h['datetime'] == dataset_high_4h.iloc[-2]['datetime']].index[0])
                inclination_high_1d = (after_highpoint_1d - before_highpoint_1d) / (self.df_1d[self.df_1d['datetime'] == dataset_high_1d.iloc[-1]['datetime']].index[0] - self.df_1d[self.df_1d['datetime'] == dataset_high_1d.iloc[-2]['datetime']].index[0])
                              
                # 이중 최신 데이터 두개만 표시하기(저점)
                before_lowpoint_5m = dataset_low_5m.iloc[-2]['low']
                after_lowpoint_5m = dataset_low_5m.iloc[-1]['low']
                before_lowpoint_15m = dataset_low_15m.iloc[-2]['low']
                after_lowpoint_15m = dataset_low_15m.iloc[-1]['low']
                before_lowpoint_30m = dataset_low_30m.iloc[-2]['low']
                after_lowpoint_30m = dataset_low_30m.iloc[-1]['low']
                before_lowpoint_1h = dataset_low_1h.iloc[-2]['low']
                after_lowpoint_1h = dataset_low_1h.iloc[-1]['low']
                before_lowpoint_4h = dataset_low_4h.iloc[-2]['low']
                after_lowpoint_4h = dataset_low_4h.iloc[-1]['low']
                before_lowpoint_1d = dataset_low_1d.iloc[-2]['low']
                after_lowpoint_1d = dataset_low_1d.iloc[-1]['low']
                
                # 저점 기울기 구하기
                inclination_low_5m = (after_lowpoint_5m - before_lowpoint_5m) / (self.df_5m[self.df_5m['datetime'] == dataset_low_5m.iloc[-1]['datetime']].index[0] - self.df_5m[self.df_5m['datetime'] == dataset_low_5m.iloc[-2]['datetime']].index[0])                
                inclination_low_15m = (after_lowpoint_15m - before_lowpoint_15m) / (self.df_15m[self.df_15m['datetime'] == dataset_low_15m.iloc[-1]['datetime']].index[0] - self.df_15m[self.df_15m['datetime'] == dataset_low_15m.iloc[-2]['datetime']].index[0])
                inclination_low_30m = (after_lowpoint_30m - before_lowpoint_30m) / (self.df_30m[self.df_30m['datetime'] == dataset_low_30m.iloc[-1]['datetime']].index[0] - self.df_30m[self.df_30m['datetime'] == dataset_low_30m.iloc[-2]['datetime']].index[0])
                inclination_low_1h = (after_lowpoint_1h - before_lowpoint_1h) / (self.df_1h[self.df_1h['datetime'] == dataset_low_1h.iloc[-1]['datetime']].index[0] - self.df_1h[self.df_1h['datetime'] == dataset_low_1h.iloc[-2]['datetime']].index[0])
                inclination_low_4h = (after_lowpoint_4h - before_lowpoint_4h) / (self.df_4h[self.df_4h['datetime'] == dataset_low_4h.iloc[-1]['datetime']].index[0] - self.df_4h[self.df_4h['datetime'] == dataset_low_4h.iloc[-2]['datetime']].index[0])
                inclination_low_1d = (after_lowpoint_1d - before_lowpoint_1d) / (self.df_1d[self.df_1d['datetime'] == dataset_low_1d.iloc[-1]['datetime']].index[0] - self.df_1d[self.df_1d['datetime'] == dataset_low_1d.iloc[-2]['datetime']].index[0])
                
                # 고점 방정식 구하기
                # y = mx + n(n은 y절편) -> 전 저/고점을 중심축으로 하면 전 저/고점의 y값이 절편이 됨 => 그 후 x값 대입은 (현재 인덱스 - 전 저점의 인덱스)를 넣어주면 됨
                y_high_5m = self.line_equation(self.df_5m[self.df_5m['datetime'] == time_5m].index[0] - self.df_5m[self.df_5m['datetime'] == dataset_high_5m.iloc[-2]['datetime']].index[0], inclination_high_5m, before_highpoint_5m)
                y_high_15m = self.line_equation(self.df_15m[self.df_15m['datetime'] == time_15m].index[0] - self.df_15m[self.df_15m['datetime'] == dataset_high_15m.iloc[-2]['datetime']].index[0], inclination_high_15m, before_highpoint_15m)
                y_high_30m = self.line_equation(self.df_30m[self.df_30m['datetime'] == time_30m].index[0] - self.df_30m[self.df_30m['datetime'] == dataset_high_30m.iloc[-2]['datetime']].index[0], inclination_high_30m, before_highpoint_30m)
                y_high_1h = self.line_equation(self.df_1h[self.df_1h['datetime'] == time_1h].index[0] - self.df_1h[self.df_1h['datetime'] == dataset_high_1h.iloc[-2]['datetime']].index[0], inclination_high_1h, before_highpoint_1h)
                y_high_4h = self.line_equation(self.df_4h[self.df_4h['datetime'] == time_4h].index[0] - self.df_4h[self.df_4h['datetime'] == dataset_high_4h.iloc[-2]['datetime']].index[0], inclination_high_4h, before_highpoint_4h)
                y_high_1d = self.line_equation(self.df_1d[self.df_1d['datetime'] == time_1d].index[0] - self.df_1d[self.df_1d['datetime'] == dataset_high_1d.iloc[-2]['datetime']].index[0], inclination_high_1d, before_highpoint_1d)
                
                # 저점 방정식 구하기
                y_low_5m = self.line_equation(self.df_5m[self.df_5m['datetime'] == time_5m].index[0] - self.df_5m[self.df_5m['datetime'] == dataset_low_5m.iloc[-2]['datetime']].index[0], inclination_low_5m, before_lowpoint_5m)
                y_low_15m = self.line_equation(self.df_15m[self.df_15m['datetime'] == time_15m].index[0] - self.df_15m[self.df_15m['datetime'] == dataset_low_15m.iloc[-2]['datetime']].index[0], inclination_low_15m, before_lowpoint_15m)
                y_low_30m = self.line_equation(self.df_30m[self.df_30m['datetime'] == time_30m].index[0] - self.df_30m[self.df_30m['datetime'] == dataset_low_30m.iloc[-2]['datetime']].index[0], inclination_low_30m, before_lowpoint_30m)
                y_low_1h = self.line_equation(self.df_1h[self.df_1h['datetime'] == time_1h].index[0] - self.df_1h[self.df_1h['datetime'] == dataset_low_1h.iloc[-2]['datetime']].index[0], inclination_low_1h, before_lowpoint_1h)
                y_low_4h = self.line_equation(self.df_4h[self.df_4h['datetime'] == time_4h].index[0] - self.df_4h[self.df_4h['datetime'] == dataset_low_4h.iloc[-2]['datetime']].index[0], inclination_low_4h, before_lowpoint_4h)
                y_low_1d = self.line_equation(self.df_1d[self.df_1d['datetime'] == time_1d].index[0] - self.df_1d[self.df_1d['datetime'] == dataset_low_1d.iloc[-2]['datetime']].index[0], inclination_low_1d, before_lowpoint_1d)
 
                # 테이블에 값 넣기
                self.tableWidget_highlow.setItem(5 , 0, QTableWidgetItem(str(time_5m))) # 시간
                self.tableWidget_highlow.setItem(5 , 1, QTableWidgetItem(str(before_highpoint_5m))) # 전고점
                self.tableWidget_highlow.setItem(5 , 2, QTableWidgetItem(str(after_highpoint_5m))) # 현고점
                self.tableWidget_highlow.setItem(5 , 3, QTableWidgetItem(str(before_lowpoint_5m))) # 전저점
                self.tableWidget_highlow.setItem(5 , 4, QTableWidgetItem(str(after_lowpoint_5m))) # 현저점
                self.tableWidget_highlow.setItem(5 , 5, QTableWidgetItem(str(round(inclination_high_5m,2)))) # 고점기울기
                self.tableWidget_highlow.setItem(5 , 6, QTableWidgetItem(str(round(inclination_low_5m,2)))) # 저점기울기
                self.tableWidget_highlow.setItem(5 , 7, QTableWidgetItem(str(y_high_5m))) # 현상태(선 위, 선 아래, 선 터치)
            
                self.tableWidget_highlow.setItem(4 , 0, QTableWidgetItem(str(time_15m))) # 시간
                self.tableWidget_highlow.setItem(4 , 1, QTableWidgetItem(str(before_highpoint_15m))) # 전고점
                self.tableWidget_highlow.setItem(4 , 2, QTableWidgetItem(str(after_highpoint_15m))) # 현고점
                self.tableWidget_highlow.setItem(4 , 3, QTableWidgetItem(str(before_lowpoint_15m))) # 전저점
                self.tableWidget_highlow.setItem(4 , 4, QTableWidgetItem(str(after_lowpoint_15m))) # 현저점
                self.tableWidget_highlow.setItem(4 , 5, QTableWidgetItem(str(round(inclination_high_15m,2)))) # 고점기울기
                self.tableWidget_highlow.setItem(4 , 6, QTableWidgetItem(str(round(inclination_low_15m,2)))) # 저점기울기
                self.tableWidget_highlow.setItem(4 , 7, QTableWidgetItem(str(y_high_15m))) # 현상태(선 위, 선 아래, 선 터치)
                
                self.tableWidget_highlow.setItem(3 , 0, QTableWidgetItem(str(time_30m))) # 시간
                self.tableWidget_highlow.setItem(3 , 1, QTableWidgetItem(str(before_highpoint_30m))) # 전고점
                self.tableWidget_highlow.setItem(3 , 2, QTableWidgetItem(str(after_highpoint_30m))) # 현고점
                self.tableWidget_highlow.setItem(3 , 3, QTableWidgetItem(str(before_lowpoint_30m))) # 전저점
                self.tableWidget_highlow.setItem(3 , 4, QTableWidgetItem(str(after_lowpoint_30m))) # 현저점
                self.tableWidget_highlow.setItem(3 , 5, QTableWidgetItem(str(round(inclination_high_30m,2)))) # 고점기울기
                self.tableWidget_highlow.setItem(3 , 6, QTableWidgetItem(str(round(inclination_low_30m,2)))) # 저점기울기
                self.tableWidget_highlow.setItem(3 , 7, QTableWidgetItem(str(y_high_30m))) # 현상태(선 위, 선 아래, 선 터치)
                
                self.tableWidget_highlow.setItem(2 , 0, QTableWidgetItem(str(time_1h))) # 시간
                self.tableWidget_highlow.setItem(2 , 1, QTableWidgetItem(str(before_highpoint_1h))) # 전고점
                self.tableWidget_highlow.setItem(2 , 2, QTableWidgetItem(str(after_highpoint_1h))) # 현고점
                self.tableWidget_highlow.setItem(2 , 3, QTableWidgetItem(str(before_lowpoint_1h))) # 전저점
                self.tableWidget_highlow.setItem(2 , 4, QTableWidgetItem(str(after_lowpoint_1h))) # 현저점
                self.tableWidget_highlow.setItem(2 , 5, QTableWidgetItem(str(round(inclination_high_1h,2)))) # 고점기울기
                self.tableWidget_highlow.setItem(2 , 6, QTableWidgetItem(str(round(inclination_low_1h,2)))) # 저점기울기
                self.tableWidget_highlow.setItem(2 , 7, QTableWidgetItem(str(y_high_1h))) # 현상태(선 위, 선 아래, 선 터치)
                
                self.tableWidget_highlow.setItem(1 , 0, QTableWidgetItem(str(time_4h))) # 시간
                self.tableWidget_highlow.setItem(1 , 1, QTableWidgetItem(str(before_highpoint_4h))) # 전고점
                self.tableWidget_highlow.setItem(1 , 2, QTableWidgetItem(str(after_highpoint_4h))) # 현고점
                self.tableWidget_highlow.setItem(1 , 3, QTableWidgetItem(str(before_lowpoint_4h))) # 전저점
                self.tableWidget_highlow.setItem(1 , 4, QTableWidgetItem(str(after_lowpoint_4h))) # 현저점
                self.tableWidget_highlow.setItem(1 , 5, QTableWidgetItem(str(round(inclination_high_4h,2)))) # 고점기울기
                self.tableWidget_highlow.setItem(1 , 6, QTableWidgetItem(str(round(inclination_low_4h,2)))) # 저점기울기
                self.tableWidget_highlow.setItem(1 , 7, QTableWidgetItem(str(y_high_4h))) # 현상태(선 위, 선 아래, 선 터치)
            
                self.tableWidget_highlow.setItem(0 , 0, QTableWidgetItem(str(time_1d))) # 시간
                self.tableWidget_highlow.setItem(0 , 1, QTableWidgetItem(str(before_highpoint_1d))) # 전고점
                self.tableWidget_highlow.setItem(0 , 2, QTableWidgetItem(str(after_highpoint_1d))) # 현고점
                self.tableWidget_highlow.setItem(0 , 3, QTableWidgetItem(str(before_lowpoint_1d))) # 전저점
                self.tableWidget_highlow.setItem(0 , 4, QTableWidgetItem(str(after_lowpoint_1d))) # 현저점
                self.tableWidget_highlow.setItem(0 , 5, QTableWidgetItem(str(round(inclination_high_1d,2)))) # 고점기울기
                self.tableWidget_highlow.setItem(0 , 6, QTableWidgetItem(str(round(inclination_low_1d,2)))) # 저점기울기
                self.tableWidget_highlow.setItem(0 , 7, QTableWidgetItem(str(y_high_1d))) # 현상태(선 위, 선 아래, 선 터치)
            
                ### --------------------------------------------------------------- ###
                ## 매물대 지지저항 라인 파악하기
                df_sure = pd.DataFrame()
                df_sure = df_sure.append({'datetime' : self.ddtime, 'price' : self.agohigh, 'gubun' : '전일고가'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : self.ddtime, 'price' : self.agolow, 'gubun' : '전일저가'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : self.ddtm, 'price' : self.nowopen, 'gubun' : '당일시가'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : self.ddtm, 'price' : self.nowhighex, 'gubun' : '당일예상고가'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : self.ddtm, 'price' : self.nowlowex, 'gubun' : '당일예상저가'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : self.df.iloc[spinnum]['datetime'], 'price' : round(self.df.iloc[spinnum]['20avg'],2), 'gubun' : '1M20일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_5m.iloc[-1]['datetime'], 'price' : round(temp_data_5m.iloc[-1]['20avg'],2), 'gubun' : '5M20일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_15m.iloc[-1]['datetime'], 'price' : round(temp_data_15m.iloc[-1]['20avg'],2), 'gubun' : '15M20일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_30m.iloc[-1]['datetime'], 'price' : round(temp_data_30m.iloc[-1]['20avg'],2), 'gubun' : '30M20일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_1h.iloc[-1]['datetime'], 'price' : round(temp_data_1h.iloc[-1]['20avg'],2), 'gubun' : '1H20일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_4h.iloc[-1]['datetime'], 'price' : round(temp_data_4h.iloc[-1]['20avg'],2), 'gubun' : '4H20일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_1d.iloc[-1]['datetime'], 'price' : round(temp_data_1d.iloc[-1]['20avg'],2), 'gubun' : '1D20일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : self.df.iloc[spinnum]['datetime'], 'price' : round(self.df.iloc[spinnum]['60avg'],2), 'gubun' : '1M60일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_5m.iloc[-1]['datetime'], 'price' : round(temp_data_5m.iloc[-1]['60avg'],2), 'gubun' : '5M60일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_15m.iloc[-1]['datetime'], 'price' : round(temp_data_15m.iloc[-1]['60avg'],2), 'gubun' : '15M60일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_30m.iloc[-1]['datetime'], 'price' : round(temp_data_30m.iloc[-1]['60avg'],2), 'gubun' : '30M60일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_1h.iloc[-1]['datetime'], 'price' : round(temp_data_1h.iloc[-1]['60avg'],2), 'gubun' : '1H60일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_4h.iloc[-1]['datetime'], 'price' : round(temp_data_4h.iloc[-1]['60avg'],2), 'gubun' : '4H60일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_1d.iloc[-1]['datetime'], 'price' : round(temp_data_1d.iloc[-1]['60avg'],2), 'gubun' : '1D60일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : self.df.iloc[spinnum]['datetime'], 'price' : round(self.df.iloc[spinnum]['120avg'],2), 'gubun' : '1M120일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_5m.iloc[-1]['datetime'], 'price' : round(temp_data_5m.iloc[-1]['120avg'],2), 'gubun' : '5M120일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_15m.iloc[-1]['datetime'], 'price' : round(temp_data_15m.iloc[-1]['120avg'],2), 'gubun' : '15M120일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_30m.iloc[-1]['datetime'], 'price' : round(temp_data_30m.iloc[-1]['120avg'],2), 'gubun' : '30M120일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_1h.iloc[-1]['datetime'], 'price' : round(temp_data_1h.iloc[-1]['120avg'],2), 'gubun' : '1H120일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_4h.iloc[-1]['datetime'], 'price' : round(temp_data_4h.iloc[-1]['120avg'],2), 'gubun' : '4H120일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_1d.iloc[-1]['datetime'], 'price' : round(temp_data_1d.iloc[-1]['120avg'],2), 'gubun' : '1D120일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : self.df.iloc[spinnum]['datetime'], 'price' : round(self.df.iloc[spinnum]['200avg'],2), 'gubun' : '1M200일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_5m.iloc[-1]['datetime'], 'price' : round(temp_data_5m.iloc[-1]['200avg'],2), 'gubun' : '5M200일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_15m.iloc[-1]['datetime'], 'price' : round(temp_data_15m.iloc[-1]['200avg'],2), 'gubun' : '15M200일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_30m.iloc[-1]['datetime'], 'price' : round(temp_data_30m.iloc[-1]['200avg'],2), 'gubun' : '30M200일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_1h.iloc[-1]['datetime'], 'price' : round(temp_data_1h.iloc[-1]['200avg'],2), 'gubun' : '1H200일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_4h.iloc[-1]['datetime'], 'price' : round(temp_data_4h.iloc[-1]['200avg'],2), 'gubun' : '4H200일선'}, ignore_index=True)
                df_sure = df_sure.append({'datetime' : temp_data_1d.iloc[-1]['datetime'], 'price' : round(temp_data_1d.iloc[-1]['200avg'],2), 'gubun' : '1D200일선'}, ignore_index=True)
                
                # 고점, 저점 데이터프레임 정제하기
                dataset_high_1m = dataset_high_1m[['datetime','close']]
                dataset_high_1m['gubun'] = '1M고점'
                dataset_high_1m.columns = ['datetime', 'price', 'gubun']
                dataset_high_5m = dataset_high_5m[['datetime','close']]
                dataset_high_5m['gubun'] = '5M고점'
                dataset_high_5m.columns = ['datetime', 'price', 'gubun']
                dataset_high_15m = dataset_high_15m[['datetime','close']]
                dataset_high_15m['gubun'] = '15M고점'
                dataset_high_15m.columns = ['datetime', 'price', 'gubun']
                dataset_high_30m = dataset_high_30m[['datetime','close']]
                dataset_high_30m['gubun'] = '30M고점'
                dataset_high_30m.columns = ['datetime', 'price', 'gubun']
                dataset_high_1h = dataset_high_1h[['datetime','close']]
                dataset_high_1h['gubun'] = '1H고점'
                dataset_high_1h.columns = ['datetime', 'price', 'gubun']
                dataset_high_4h = dataset_high_4h[['datetime','close']]
                dataset_high_4h['gubun'] = '4H고점'
                dataset_high_4h.columns = ['datetime', 'price', 'gubun']
                dataset_high_1d = dataset_high_1d[['datetime','close']]
                dataset_high_1d['gubun'] = '1D고점'
                dataset_high_1d.columns = ['datetime', 'price', 'gubun']
                dataset_low_1m = dataset_low_1m[['datetime', 'close']]
                dataset_low_1m['gubun'] = '1M저점'
                dataset_low_1m.columns = ['datetime', 'price', 'gubun']
                dataset_low_5m = dataset_low_5m[['datetime', 'close']]
                dataset_low_5m['gubun'] = '5M저점'
                dataset_low_5m.columns = ['datetime', 'price', 'gubun']
                dataset_low_15m = dataset_low_15m[['datetime', 'close']]
                dataset_low_15m['gubun'] = '15M저점'
                dataset_low_15m.columns = ['datetime', 'price', 'gubun']
                dataset_low_30m = dataset_low_30m[['datetime', 'close']]
                dataset_low_30m['gubun'] = '30M저점'
                dataset_low_30m.columns = ['datetime', 'price', 'gubun']
                dataset_low_1h = dataset_low_1h[['datetime', 'close']]
                dataset_low_1h['gubun'] = '1H저점'
                dataset_low_1h.columns = ['datetime', 'price', 'gubun']
                dataset_low_4h = dataset_low_4h[['datetime', 'close']]
                dataset_low_4h['gubun'] = '4H저점'
                dataset_low_4h.columns = ['datetime', 'price', 'gubun']
                dataset_low_1d = dataset_low_1d[['datetime', 'close']]
                dataset_low_1d['gubun'] = '1D저점'
                dataset_low_1d.columns = ['datetime', 'price', 'gubun']
                
                # 고점, 저점 데이터 append 하기
                df_sure = df_sure.append(dataset_high_1m, ignore_index=True)
                df_sure = df_sure.append(dataset_high_5m, ignore_index=True)
                df_sure = df_sure.append(dataset_high_15m, ignore_index=True)
                df_sure = df_sure.append(dataset_high_30m, ignore_index=True)
                df_sure = df_sure.append(dataset_high_1h, ignore_index=True)
                df_sure = df_sure.append(dataset_high_4h, ignore_index=True)
                df_sure = df_sure.append(dataset_high_1d, ignore_index=True)
                df_sure = df_sure.append(dataset_low_1m, ignore_index=True)
                df_sure = df_sure.append(dataset_low_5m, ignore_index=True)
                df_sure = df_sure.append(dataset_low_15m, ignore_index=True)
                df_sure = df_sure.append(dataset_low_30m, ignore_index=True)
                df_sure = df_sure.append(dataset_low_1h, ignore_index=True)
                df_sure = df_sure.append(dataset_low_4h, ignore_index=True)
                df_sure = df_sure.append(dataset_low_1d, ignore_index=True)
                
                # df_sure에서 상 5개, 하 5개 추출
                df_sure = df_sure.sort_values('price', ascending=True) # 가격 순으로 정렬
                df_sure = df_sure.reset_index(drop=True) # 인덱스 초기화
                df_sure_emp = df_sure[df_sure['price'] <= cl]
                ind_sure = len(df_sure_emp) - 1
                if len(df_sure_emp) < 5 :
                    df_sure_rank = df_sure[0:10]
                else : 
                    df_sure_rank = df_sure[ind_sure-4:ind_sure+6]                
                    
                # 테이블(tableWidget_sure)에 값 넣기
                self.tableWidget_sure.setItem(0 , 0, QTableWidgetItem(str(df_sure_rank.iloc[9]['datetime']))) # 시간
                self.tableWidget_sure.setItem(1 , 0, QTableWidgetItem(str(df_sure_rank.iloc[8]['datetime']))) # 시간
                self.tableWidget_sure.setItem(2 , 0, QTableWidgetItem(str(df_sure_rank.iloc[7]['datetime']))) # 시간
                self.tableWidget_sure.setItem(3 , 0, QTableWidgetItem(str(df_sure_rank.iloc[6]['datetime']))) # 시간
                self.tableWidget_sure.setItem(4 , 0, QTableWidgetItem(str(df_sure_rank.iloc[5]['datetime']))) # 시간
                self.tableWidget_sure.setItem(5 , 0, QTableWidgetItem(str(dt))) # 시간
                self.tableWidget_sure.setItem(6 , 0, QTableWidgetItem(str(df_sure_rank.iloc[4]['datetime']))) # 시간
                self.tableWidget_sure.setItem(7 , 0, QTableWidgetItem(str(df_sure_rank.iloc[3]['datetime']))) # 시간
                self.tableWidget_sure.setItem(8 , 0, QTableWidgetItem(str(df_sure_rank.iloc[2]['datetime']))) # 시간
                self.tableWidget_sure.setItem(9 , 0, QTableWidgetItem(str(df_sure_rank.iloc[1]['datetime']))) # 시간
                self.tableWidget_sure.setItem(10 , 0, QTableWidgetItem(str(df_sure_rank.iloc[0]['datetime']))) # 시간
                
                self.tableWidget_sure.setItem(0 , 1, QTableWidgetItem(str(df_sure_rank.iloc[9]['price']))) # 가격
                self.tableWidget_sure.setItem(1 , 1, QTableWidgetItem(str(df_sure_rank.iloc[8]['price']))) # 가격
                self.tableWidget_sure.setItem(2 , 1, QTableWidgetItem(str(df_sure_rank.iloc[7]['price']))) # 가격
                self.tableWidget_sure.setItem(3 , 1, QTableWidgetItem(str(df_sure_rank.iloc[6]['price']))) # 가격
                self.tableWidget_sure.setItem(4 , 1, QTableWidgetItem(str(df_sure_rank.iloc[5]['price']))) # 가격
                self.tableWidget_sure.setItem(5 , 1, QTableWidgetItem(str(cl))) # 가격
                self.tableWidget_sure.setItem(6 , 1, QTableWidgetItem(str(df_sure_rank.iloc[4]['price']))) # 가격
                self.tableWidget_sure.setItem(7 , 1, QTableWidgetItem(str(df_sure_rank.iloc[3]['price']))) # 가격
                self.tableWidget_sure.setItem(8 , 1, QTableWidgetItem(str(df_sure_rank.iloc[2]['price']))) # 가격
                self.tableWidget_sure.setItem(9 , 1, QTableWidgetItem(str(df_sure_rank.iloc[1]['price']))) # 가격
                self.tableWidget_sure.setItem(10 , 1, QTableWidgetItem(str(df_sure_rank.iloc[0]['price']))) # 가격
                
                self.tableWidget_sure.setItem(0 , 2, QTableWidgetItem(str(df_sure_rank.iloc[9]['gubun']))) # 종류
                self.tableWidget_sure.setItem(1 , 2, QTableWidgetItem(str(df_sure_rank.iloc[8]['gubun']))) # 종류
                self.tableWidget_sure.setItem(2 , 2, QTableWidgetItem(str(df_sure_rank.iloc[7]['gubun']))) # 종류
                self.tableWidget_sure.setItem(3 , 2, QTableWidgetItem(str(df_sure_rank.iloc[6]['gubun']))) # 종류
                self.tableWidget_sure.setItem(4 , 2, QTableWidgetItem(str(df_sure_rank.iloc[5]['gubun']))) # 종류
                self.tableWidget_sure.setItem(5 , 2, QTableWidgetItem(str('현재가격'))) # 종류
                self.tableWidget_sure.setItem(6 , 2, QTableWidgetItem(str(df_sure_rank.iloc[4]['gubun']))) # 종류
                self.tableWidget_sure.setItem(7 , 2, QTableWidgetItem(str(df_sure_rank.iloc[3]['gubun']))) # 종류
                self.tableWidget_sure.setItem(8 , 2, QTableWidgetItem(str(df_sure_rank.iloc[2]['gubun']))) # 종류
                self.tableWidget_sure.setItem(9 , 2, QTableWidgetItem(str(df_sure_rank.iloc[1]['gubun']))) # 종류
                self.tableWidget_sure.setItem(10 , 2, QTableWidgetItem(str(df_sure_rank.iloc[0]['gubun']))) # 종류
                
                ### --------------------------------------------------------------- ###
                ## 신호 lineedit 넣기 ##
                # 넣을 값
                # 변수(2)
                volavg = round(self.df2['volume'].mean(), 2) # 거래량 평균
                sp = self.df.iloc[spinnum]['separ'] # 이격도
                st = self.df.iloc[spinnum]['strength'] # 상대강도
                
                self.lineEdit_1.setText('추세1')
                self.lineEdit_2.setText('추세2')
                self.lineEdit_3.setText(str(volavg))
                self.lineEdit_4.setText(str(round(sp,2)))
                self.lineEdit_5.setText(str(round(st,2)))
                touch_arr = []
                for i in df_sure.index:
                    if lw <= df_sure.iloc[i]['price'] <= hi :
                        touch_arr.append(df_sure.iloc[i]['gubun'])
                if 2 > len(touch_arr) >= 1 :
                    self.lineEdit_6.setText(str(touch_arr[0]))
                    self.lineEdit_7.setText('없음')
                    self.lineEdit_8.setText('없음')
                    
                elif 3 > len(touch_arr) >= 2 :
                    self.lineEdit_6.setText(str(touch_arr[0]))
                    self.lineEdit_7.setText(str(touch_arr[1]))
                    self.lineEdit_8.setText('없음')
                elif len(touch_arr) >= 3 :    
                    self.lineEdit_6.setText(str(touch_arr[0]))
                    self.lineEdit_7.setText(str(touch_arr[1]))
                    self.lineEdit_8.setText(str(touch_arr[2]))
                
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
                                    
        except Exception as e:
            print(e)
            print(traceback.format_exc())