import pandas as pd

class viewtrend_cls:
    def exe_viewtrend(self, dataset):
        # 가장 최근에 볼린저밴드 상단이나 하단을 뚫은 봉을 찾기
        how_borebb = ''
        dt_borebb = ''
        for i in dataset.index:
            if i > 0 :
                if dataset.iloc[-i]['close'] >= dataset.iloc[-i]['bb_up'] :
                    how_borebb = '상단'
                    dt_borebb = dataset.iloc[-i]['datetime']
                    break
                elif dataset.iloc[-i]['close'] <= dataset.iloc[-i]['bb_down'] :
                    how_borebb = '하단'
                    dt_borebb = dataset.iloc[-i]['datetime']
                    break
        if how_borebb == '':
            return '없음'
        else : 
            # 선정봉 찾기(위의 봉 전후 5봉 사이중 선정수가 가장 작은 봉)
            # 선정수 = 고점보다 큰 봉수 + 저점보다 작은 봉수
            updtbore_num = len(dataset[dataset['datetime'] >= dt_borebb])
            downdtbore_num = len(dataset[dataset['datetime'] <= dt_borebb])
            if downdtbore_num < 5 :
                idx_bore = dataset[dataset['datetime'] == dt_borebb].index[0]
                sample_df = dataset.iloc[idx_bore-downdtbore_num+1:idx_bore+1]
                sample_df = sample_df.reset_index(drop=True) # 인덱스 초기화 
                sample_df['rank_high'] = sample_df['high'].rank(method='min', ascending=False)
                sample_df['rank_low'] = sample_df['low'].rank(method='min', ascending=True)
                sample_df['greatnum'] = (sample_df['rank_high'] - 1) + (sample_df['rank_low'] - 1)
            else :
                if updtbore_num >= 5 :
                    idx_bore = dataset[dataset['datetime'] == dt_borebb].index[0]
                    sample_df = dataset.iloc[idx_bore-4:idx_bore+5]
                    sample_df = sample_df.reset_index(drop=True) # 인덱스 초기화 
                    sample_df['rank_high'] = sample_df['high'].rank(method='min', ascending=False)
                    sample_df['rank_low'] = sample_df['low'].rank(method='min', ascending=True)
                    sample_df['greatnum'] = (sample_df['rank_high'] - 1) + (sample_df['rank_low'] - 1)
                else :
                    idx_bore = dataset[dataset['datetime'] == dt_borebb].index[0]
                    sample_df = dataset.iloc[idx_bore-4:idx_bore+updtbore_num]
                    sample_df = sample_df.reset_index(drop=True) # 인덱스 초기화
                    sample_df['rank_high'] = sample_df['high'].rank(method='min', ascending=False)
                    sample_df['rank_low'] = sample_df['low'].rank(method='min', ascending=True)
                    sample_df['greatnum'] = (sample_df['rank_high'] - 1) + (sample_df['rank_low'] - 1)
            
            # 선정수가 가장 작은 선정봉의 datetime
            final_gn = ''
            final_dt = ''
            for i in sample_df.index:
                if final_gn == '':
                    final_gn = sample_df.loc[i]['greatnum']
                    final_dt = sample_df.loc[i]['datetime']
                else:     
                    if final_gn >= sample_df.loc[i]['greatnum'] :
                        final_gn = sample_df.loc[i]['greatnum']
                        final_dt = sample_df.loc[i]['datetime']
            
            return final_dt

#start = viewtrend_cls()     
#start.exe_viewtrend(pd.DataFrame())
