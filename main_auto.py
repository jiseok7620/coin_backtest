import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from mpl_toolkits.mplot3d import Axes3D
#import mpl_finance
import traceback
from coin_invest_backtest.maxLine import maxLine_cls
from coin_invest_backtest.minLine import minLine_cls
import time
from coin_invest_backtest.viewtrend import viewtrend_cls
from coin_invest_backtest.searchtrend import searchtrend_cls

form_secondwindow = uic.loadUiType("auto.ui")[0] # 두 번째창 ui

class main_auto_cls(QDialog, QWidget, form_secondwindow):
    def __init__(self, dataset, dateset_5m, dateset_1h, dateset_4h, dataset_1d):
        super(main_auto_cls, self).__init__()
        self.setupUi(self)
        self.show() # 두번째창 실행
        
        # 전역변수선언
        self.df = dataset
        self.df2 = pd.DataFrame() # 데이터 1행씩 추가
        self.df_5m = dateset_5m # 5분 데이터 저장
        self.df_1h = dateset_1h # 1시간 데이터 저장
        self.df_4h = dateset_4h # 4시간 데이터 저장
        self.df_1d = dataset_1d # 일봉 데이터 저장
        
        # 결과 데이터프레임
        column_name = ['시간','포지션','진입가','목표가','손절가','수익률','비고']
        self.result_table = pd.DataFrame(columns=column_name) # 결과저장할 데이터프레임
        
        ##----------------------------------------------------------------------------##
        ## 버튼 클릭 시 함수와 연결 모음 ##
        self.pushButton.clicked.connect(self.exe_auto)
        
    def exe_auto(self):
        try :
            for i in self.df.index:
                if i == 0 :
                    pass
                else :
                    # MACD 신호 발굴
                    if self.df.iloc[i-1]['macd'] < self.df.iloc[i-1]['macd_signal'] and self.df.iloc[i]['macd'] > self.df.iloc[i]['macd_signal'] : # 골드크로스
                        # 목표가, 손절가
                        goalprice = round(self.df.iloc[i]['close']*1.005,2)
                        lossprice = round(self.df.iloc[i]['close']*0.992,2)
                        # 결과 리스트 만들기
                        result_list = [self.df.iloc[i]['datetime'], '매수', self.df.iloc[i]['close'], goalprice, lossprice, 0, '보유']
                        self.result_table = self.result_table.append(pd.Series(result_list, index=self.result_table.columns), ignore_index=True)
                        
                    elif self.df.iloc[i-1]['macd'] > self.df.iloc[i-1]['macd_signal'] and self.df.iloc[i]['macd'] < self.df.iloc[i]['macd_signal'] : # 데드크로스
                        # 목표가, 손절가
                        goalprice = round(self.df.iloc[i]['close']*0.995,2)
                        lossprice = round(self.df.iloc[i]['close']*1.008,2)
                        # 결과 리스트 만들기
                        result_list = [self.df.iloc[i]['datetime'], '매도', self.df.iloc[i]['close'], goalprice, lossprice, 0, '보유']
                        self.result_table = self.result_table.append(pd.Series(result_list, index=self.result_table.columns), ignore_index=True)
                        
                    # 결과테이블 손익, 손절 구하기
                    for k in self.result_table.index:
                        if self.result_table.iloc[k]['비고'] == '보유' :
                            if self.result_table.iloc[k]['포지션'] == '매수' :
                                perpri = round(self.df.iloc[i]['close']/self.result_table.iloc[k]['진입가'] * 100 - 100, 2)
                                self.result_table.loc[k, '수익률'] = perpri # 수익률 넣기
                                if self.df.iloc[i]['high'] >= self.result_table.iloc[k]['목표가'] :
                                    self.result_table.loc[k, '비고'] = '수익'
                                elif self.df.iloc[i]['low'] <= self.result_table.iloc[k]['손절가'] :
                                    self.result_table.loc[k, '비고'] = '손절'  
                                    
                            elif self.result_table.iloc[k]['포지션'] == '매도' :
                                perpri = round(self.result_table.iloc[k]['진입가']/self.df.iloc[i]['close'] * 100 - 100, 2)
                                self.result_table.loc[k, '수익률'] = perpri # 수익률 넣기
                                if self.df.iloc[i]['high'] >= self.result_table.iloc[k]['손절가'] :
                                    self.result_table.loc[k, '비고'] = '손절'
                                elif self.df.iloc[i]['low'] <= self.result_table.iloc[k]['목표가'] :
                                    self.result_table.loc[k, '비고'] = '수익'          
                                    
            print(self.result_table)
            
            
            
            
            
            
            
            
            
            
            
        except Exception as e:
            print(e)
            print(traceback.format_exc())
