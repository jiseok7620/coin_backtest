import pandas as pd

class searchtrend_cls:
    def exe_searchtrend(self, dataset, select_dt):
        # 선정봉의 인덱스 구하기
        ind_select = dataset[dataset['datetime'] == select_dt].index[0]
        
        # 선정폭 구하기
        select_up = dataset[dataset['datetime'] == select_dt]['high'].iloc[-1]
        select_down = dataset[dataset['datetime'] == select_dt]['low'].iloc[-1]
        
        # 선정봉의 종가와 그때 20일선 구하기
        select_close = dataset[dataset['datetime'] == select_dt]['close'].iloc[-1]
        select_20avg = dataset[dataset['datetime'] == select_dt]['20avg'].iloc[-1]
        
        # 전역변수
        result_txt = ''
        bohab_up = select_up
        bohab_down = select_down
        
        # 시작 : 볼밴을 뚫는 봉의 출현 = 선정봉
        if select_close > select_20avg : 
            result_txt = '상승추세구간'
        elif select_close < select_20avg :
            result_txt = '하락추세구간'
        
        for i in range(ind_select+1,len(dataset)):
            # 필요한 변수선언
            cl = dataset.iloc[i]['close']
            trendsig_20avg = dataset.iloc[i]['20avg']
            trendsig_bbup = dataset.iloc[i]['bb_up']
            trendsig_bbdown = dataset.iloc[i]['bb_down']
            
            if result_txt == '상승보합구간' or result_txt == '상승추세구간' :
                bohab_up = max(trendsig_bbup, select_up)
                bohab_down = min(trendsig_20avg, select_down)
                if bohab_down > cl :
                    result_txt = '하락전환전보합구간'
                elif bohab_up < cl : 
                    result_txt = '상승추세구간'
                elif bohab_up >= cl >= bohab_down :
                    result_txt = '상승보합구간'
                    
            elif result_txt == '상승보합구간(RE)' : 
                bohab_up = max(trendsig_bbup, select_up)
                bohab_down = min(trendsig_20avg, select_down)
                if bohab_down > cl :
                    result_txt = '보합구간'
                elif bohab_up < cl : 
                    result_txt = '상승추세구간'
                elif bohab_up >= cl >= bohab_down :
                    result_txt = '상승보합구간(RE)'
                    
            elif result_txt == '하락전환전보합구간' :
                bohab_up = trendsig_20avg
                bohab_down = trendsig_bbdown
                if bohab_down > cl : 
                    result_txt = '하락추세구간'
                elif cl > bohab_up : 
                    result_txt = '상승보합구간(RE)'
                elif bohab_up >= cl >= bohab_down :
                    result_txt = '하락전환전보합구간'
                    
            elif result_txt == '보합구간' :
                bohab_up = trendsig_bbup # or 보합구간 최대값)
                bohab_down = trendsig_bbdown # or 보합구간 최소값)
                if bohab_up < cl : 
                    self.lineEdit_trendsig.setText('보합후상승신호')
                    result_txt = '상승추세구간' 
                elif bohab_down > cl : 
                    self.lineEdit_trendsig.setText('보합후하락신호')
                    result_txt = '하락추세구간'
                elif bohab_up >= cl >= bohab_down :
                    result_txt = '보합구간'
                    
            elif result_txt == '하락보합구간' or result_txt == '하락추세구간' :
                bohab_up = max(trendsig_20avg, select_up)
                bohab_down = min(trendsig_bbdown, select_down) # 볼밴하단과 선정폭하단중 작은값
                if bohab_down > cl :
                    result_txt = '하락추세구간'
                elif bohab_up < cl :
                    result_txt = '상승전환전보합구간'
                elif bohab_up >= cl >= bohab_down :
                    result_txt = '하락보합구간'
                    
            elif result_txt == '하락보합구간(RE)' : 
                bohab_up = max(trendsig_20avg, select_up) # 20일선과 선정폭상단중 큰값
                bohab_down = min(trendsig_bbdown, select_down) # 볼밴하단과 선정폭하단중 작은값
                if bohab_down > cl :
                    result_txt = '하락추세구간' 
                elif bohab_up < cl : 
                    result_txt = '보합구간'
                elif bohab_up >= cl >= bohab_down :
                    result_txt = '하락보합구간(RE)'
                    
            elif result_txt == '상승전환전보합구간' :
                bohab_up = trendsig_bbup # 볼밴상단
                bohab_down = trendsig_20avg # 20일선
                if bohab_down > cl : 
                    result_txt = '하락보합구간(RE)'
                elif cl > bohab_up : 
                    result_txt = '상승추세구간'
                elif bohab_up >= cl >= bohab_down :
                    result_txt = '상승전환전보합구간'

        return result_txt, bohab_up, bohab_down
#start = viewtrend_cls()     
#start.exe_viewtrend(pd.DataFrame())
