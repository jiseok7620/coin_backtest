import pandas as pd

class minLine_cls:
    def exe_minLine(self, st_dd, dataset, long):
        ##--------------------------------------------------------------------------------------------------##
        ## 고점 구하기 ##
        lowpoint_count_bf = 0 # 저점보다 큰값들의 수(당일 이전)
        lowpoint_count_af = 0 # 저점보다 큰값들의 수(당일 이후).
        
        # for문 돌리기
        st_num = dataset[dataset['datetime']==st_dd].index[0]# 최저최대선 데이터 중 마지막을 시작점으로
        i = st_num - (long * 2)
        middle = i + long
        
        if i >= 0 :
            for l in range(0, long) : 
                if dataset.iloc[middle]['low'] >= dataset.iloc[middle-l-1]['low']:
                    break
                elif dataset.iloc[middle]['low'] < dataset.iloc[middle-l-1]['low']:
                    lowpoint_count_bf += 1
                
            for m in range(middle,st_num+1):
                if middle == m :
                    continue
                if dataset.iloc[middle]['low'] >= dataset.iloc[m]['low']:
                    break
                elif dataset.iloc[middle]['low'] < dataset.iloc[m]['low']:
                    lowpoint_count_af += 1
        
        if lowpoint_count_bf >= long and lowpoint_count_af >= long:
            # 결과 리턴
            return middle
        else:
            # 결과 리턴
            return 0
