import pandas as pd

class maxLine_cls:
    def exe_maxLine(self, st_dd, dataset, long):
        ##--------------------------------------------------------------------------------------------------##
        ## 고점 구하기 ##
        highpoint_count_bf = 0 # 저점보다 큰값들의 수(당일 이전)
        highpoint_count_af = 0 # 저점보다 큰값들의 수(당일 이후).
        
        # for문 돌리기
        st_num = dataset[dataset['datetime']==st_dd].index[0]# 최저최대선 데이터 중 마지막을 시작점으로
        i = st_num - (long * 2)
        middle = i + long
        
        if i >= 0 :
            for l in range(0, long) : 
                if dataset.iloc[middle]['high'] <= dataset.iloc[middle-l-1]['high']:
                    break
                elif dataset.iloc[middle]['high'] > dataset.iloc[middle-l-1]['high']:
                    highpoint_count_bf += 1
                
            for m in range(middle,st_num+1):
                if middle == m :
                    continue
                if dataset.iloc[middle]['high'] <= dataset.iloc[m]['high']:
                    break
                elif dataset.iloc[middle]['high'] > dataset.iloc[m]['high']:
                    highpoint_count_af += 1
        
        if highpoint_count_bf >= long and highpoint_count_af >= long:
            # 결과 리턴
            return middle
        else:
            # 결과 리턴
            return 0