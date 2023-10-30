import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from mpl_toolkits.mplot3d import Axes3D
import mplfinance

form_chartwindow = uic.loadUiType("chart.ui")[0] # 차트 ui

class main_chart_cls(QDialog, QWidget, form_chartwindow):
    def __init__(self,chart_dataset, chart_viewtime):
        super(main_chart_cls, self).__init__()
        self.setupUi(self)
        self.show() # 세번째창 실행

        # 전역변수선언하기
        self.df = chart_dataset
        self.viewtime = chart_viewtime
        
        # 그래프 그리기
        self.fig = plt.Figure()
        self.canvas = FigureCanvas(self.fig)
        self.graph_verticalLayout.addWidget(self.canvas)
        
        # 그래프 그리기 함수 호출
        self.show_chart()
        
    def show_chart(self):
        try :
            # 인덱스 초기화
            self.df = self.df.reset_index(drop=True) # 인덱스 초기화 
            
            # 인덱스 찾기
            ind = self.df[self.df['datetime'] == self.viewtime].index[0] # 해당 시간의  인덱스
            
            # 그래프 그리기
            ax = self.fig.add_subplot(111)
            ax.cla()
            ax.axvline(ind, 0, 1, color='lightgray', linestyle='--', linewidth=1) # 진입봉 표시하기
            mplfinance.candlestick2_ohlc(ax, self.df['open'], self.df['high'], self.df['low'], self.df['close'], width=0.5, colorup='r', colordown='b')
            self.canvas.draw()
            
        except Exception as e:
            print(e)