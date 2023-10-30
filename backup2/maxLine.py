import pandas as pd

class maxLine_cls:
    def exe_maxLine(self, dataset, long):
        ##--------------------------------------------------------------------------------------------------##
        ## 고점 구하기 ##
        highpoint_bf = [] # 저점보다 큰값들의 수 리스트(당일 이전)
        highpoint_af = [] # 저점보다 큰값들의 수 리스트(당일 이후)
        highpoint_count_bf = 0 # 저점보다 큰값들의 수(당일 이전)
        highpoint_count_af = 0 # 저점보다 큰값들의 수(당일 이후).
        highpoint_ind = []
        
        for i in dataset.index:
            # 고점 구하기
            for l in range(i) : 
                if i == 0:
                    break
                if dataset.iloc[i]['high'] <= dataset.iloc[i-l-1]['high']:
                    break
                elif dataset.iloc[i]['high'] > dataset.iloc[i-l-1]['high']:
                    highpoint_count_bf += 1
                if highpoint_count_bf >= long:
                    break
                
            for m in range(i,len(dataset)):
                if i == len(dataset)-1:
                    break
                if i == m :
                    continue
                if dataset.iloc[i]['high'] <= dataset.iloc[m]['high']:
                    break
                elif dataset.iloc[i]['high'] > dataset.iloc[m]['high']:
                    highpoint_count_af += 1
                if highpoint_count_af >= long:
                    break
            
            # 저점 배열 추가            
            highpoint_bf.append(highpoint_count_bf)
            highpoint_af.append(highpoint_count_af)
            highpoint_ind.append(i)
            highpoint_count_bf = 0
            highpoint_count_af = 0
            
        # 결과
        highpoint_data = pd.DataFrame({'before' : highpoint_bf, 'after' : highpoint_af, '인덱스' : highpoint_ind})
        
        # 전작은값수나 후작은값수가 long미만 인 것들은 필터
        highpoint_data_long = highpoint_data[highpoint_data['before'] >= long]
        highpoint_data_long = highpoint_data_long[highpoint_data_long['after'] >= long]
        
        ##--------------------------------------------------------------------------------------------------##        
        # 저점의 datetime, 인덱스, 가격 가져오기
        highpoint_date_long = []
        highpoint_open = []
        highpoint_high = []
        highpoint_low = []
        highpoint_close = []
        highpoint_volume_long = []
        highpoint_before = []
        highpoint_after = []
        
        for i in range(len(highpoint_data_long)) :
            # 인덱스 가져오기
            highidx = highpoint_data_long.iloc[i]['인덱스']
            
            # datetime
            highdate = dataset.loc[highidx]['datetime']
            
            # open
            highopen = dataset.loc[highidx]['open']
            # high
            highhigh = dataset.loc[highidx]['high']
            # low
            highlow = dataset.loc[highidx]['low']
            # close
            highclose = dataset.loc[highidx]['close'] 
                
            # volume
            highvolume = dataset.loc[highidx]['volume']
            
            # before
            cnt_bf = highpoint_data_long.iloc[i]['before']
            
            # after
            cnt_af = highpoint_data_long.iloc[i]['after']
            
            # 리스트에 값 넣기
            highpoint_date_long.append(highdate)
            highpoint_open.append(highopen)
            highpoint_high.append(highhigh)
            highpoint_low.append(highlow)
            highpoint_close.append(highclose)
            highpoint_volume_long.append(highvolume)
            highpoint_before.append(cnt_bf)
            highpoint_after.append(cnt_af)
            
        # 결과 데이터프레임 만들기
        highpoint_grape_data_long = pd.DataFrame({
                                                'datetime' : highpoint_date_long, 
                                                'open' : highpoint_open, 'high' : highpoint_high, 'low' : highpoint_low, 'close' : highpoint_close,
                                                'volume' : highpoint_volume_long, 
                                                'before' : highpoint_before, 'after' : highpoint_after
                                                 })
        
        # 내림차순 정리
        highpoint_grape_data_long = highpoint_grape_data_long.sort_values('datetime', ascending=True)
        
        # 결과 리턴
        return highpoint_grape_data_long