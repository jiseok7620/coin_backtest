import pandas as pd

class minLine_cls:
    def exe_minLine(self, dataset, long):
        ##--------------------------------------------------------------------------------------------------##
        ## 저점 구하기 ##
        lowpoint_bf = [] # 저점보다 큰값들의 수 리스트(당일 이전)
        lowpoint_af = [] # 저점보다 큰값들의 수 리스트(당일 이후)
        lowpoint_count_bf = 0 # 저점보다 큰값들의 수(당일 이전)
        lowpoint_count_af = 0 # 저점보다 큰값들의 수(당일 이후)
        lowpoint_ind = []
        
        for i in dataset.index:
            # 저점 구하기 = before
            for l in range(i) : 
                if i == 0:
                    break
                if dataset.iloc[i]['low'] >= dataset.iloc[i-l-1]['low']:
                    break
                elif dataset.iloc[i]['low'] < dataset.iloc[i-l-1]['low']:
                    lowpoint_count_bf += 1
                if lowpoint_count_bf >= long:
                    break
            
            # 저점 구하기 = after
            for m in range(i,len(dataset)):
                if i == len(dataset)-1:
                    break
                if i == m :
                    continue
                if dataset.iloc[i]['low'] >= dataset.iloc[m]['low']:
                    break
                elif dataset.iloc[i]['low'] < dataset.iloc[m]['low']:
                    lowpoint_count_af += 1
                if lowpoint_count_af >= long:
                    break
            
            # 저점 배열 추가            
            lowpoint_bf.append(lowpoint_count_bf)
            lowpoint_af.append(lowpoint_count_af)
            lowpoint_ind.append(i)
            lowpoint_count_bf = 0
            lowpoint_count_af = 0
            
        # 결과
        lowpoint_data = pd.DataFrame({'before' : lowpoint_bf, 'after' : lowpoint_af, '인덱스' : lowpoint_ind})
        
        # 전작은값수나 후작은값수가 10미만 인 것들은 필터
        lowpoint_data_long = lowpoint_data[lowpoint_data['before'] >= long]
        lowpoint_data_long = lowpoint_data_long[lowpoint_data_long['after'] >= long]
        
        ##--------------------------------------------------------------------------------------------------##        
        # 저점의 datetime, 인덱스, 가격 가져오기
        lowpoint_date_long = []
        lowpoint_index_long = []
        lowpoint_open = []
        lowpoint_high = []
        lowpoint_low = []
        lowpoint_close = []
        lowpoint_volume_long = []
        lowpoint_before = []
        lowpoint_after = []
        
        for i in range(len(lowpoint_data_long)) :
            # 인덱스 가져오기
            lowidx = lowpoint_data_long.iloc[i]['인덱스']
            
            # datetime
            lowdate = dataset.loc[lowidx]['datetime']
            
            # open
            lowopen = dataset.loc[lowidx]['open']
            # high
            lowhigh = dataset.loc[lowidx]['high']
            # low
            lowlow = dataset.loc[lowidx]['low']
            # close
            lowclose = dataset.loc[lowidx]['close'] 
            
            # volume
            lowvolume = dataset.loc[lowidx]['volume']
            
            # before
            cnt_bf = lowpoint_data_long.iloc[i]['before']
            
            # after
            cnt_af = lowpoint_data_long.iloc[i]['after']
            
            # 리스트에 값 넣기
            lowpoint_date_long.append(lowdate)
            lowpoint_index_long.append(lowidx)
            lowpoint_open.append(lowopen)
            lowpoint_high.append(lowhigh)
            lowpoint_low.append(lowlow)
            lowpoint_close.append(lowclose)
            lowpoint_volume_long.append(lowvolume)
            lowpoint_before.append(cnt_bf)
            lowpoint_after.append(cnt_af)
          
        # 결과 데이터프레임 만들기
        lowpoint_grape_data_long = pd.DataFrame({
                                                'datetime' : lowpoint_date_long, 
                                                'open' : lowpoint_open, 'high' : lowpoint_high, 'low' : lowpoint_low, 'close' : lowpoint_close,
                                                'volume' : lowpoint_volume_long,
                                                'before' : lowpoint_before, 'after' : lowpoint_after
                                                 })
        
        # 오름차순 정리
        lowpoint_grape_data_long = lowpoint_grape_data_long.sort_values('datetime', ascending=True)
        
        # 결과 리턴
        return lowpoint_grape_data_long