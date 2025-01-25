import sys
sys.path.append("c:/Users/이동언/Desktop/myProject/Bitcoin")

import time
from datetime import datetime, timedelta
from utils.FiveMin3Ticks import filter_top_coins_by_value
from utils.upbit_api import get_upbit_instance
from utils.mornitoring import monitoring_top10, monitoring_buyticker

# Upbit 객체 생성
api_key_file = "C:/Users/이동언/Desktop/myProject/Bitcoin/config/API_key.txt"

upbit = get_upbit_instance(api_key_file)

log_file = "log2.txt"

def main():
    print("start!")
    
    # 상위 10개 코인을 하루에 한 번 갱신하기 위한 변수
    last_update_time = datetime.now() - timedelta(days=1)  # 초기값을 과거로 설정
    top10_df = None  # 상위 10개 코인 데이터프레임 초기화

    while True:
        current_time = datetime.now()
        
        # 하루에 한 번 상위 10개 코인 갱신
        if (current_time - last_update_time) >= timedelta(days=1):
            top10_df = filter_top_coins_by_value()
            last_update_time = current_time  # 마지막 업데이트 시간 갱신
            print(top10_df)
        
        # 틱 업데이트
        if top10_df is not None:
            ticker_data, isbuy = monitoring_top10(top10_df)
            # 매수 종목 모니터링
            if isbuy:
                top10_df = monitoring_buyticker(ticker_data, upbit, top10_df, log_file)
            else:
                top10_df = ticker_data
        
        print(top10_df)
        time.sleep(180)  # 3분 대기 후 다시 실행

if __name__ == "__main__":
    main()