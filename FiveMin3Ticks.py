import os
import pyupbit
import pandas as pd
import time
from datetime import datetime

# 가상의 자산 초기 설정
default_log_file = os.path.abspath("../log2.txat")

def log_transaction(message, log_file_path=default_log_file):
    """
    로그파일에 메세지 작성, 기록용
    """
    try:
        # 로그 파일 경로 확인 및 디렉토리 생성
        log_file_path = os.path.abspath(log_file_path)
        log_dir = os.path.dirname(log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 파일에 로그 쓰기
        with open(log_file_path, "a", encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 시간 포맷: YYYY-MM-DD HH:MM:SS
            f.write(f"{timestamp}: {message}\n")
    except Exception as e:
        print(f"로그 작성 중 오류 발생: {e}")


def filter_top_coins_by_value(count=10):
    """
    거래대금 기준 상위 N(10)개 코인을 필터링
    """
    markets = pyupbit.get_tickers(fiat="KRW")

    data = []
    for market in markets:
        ticker_data = pyupbit.get_ohlcv(market, interval="day", count=1)
        if ticker_data is not None:
            volume = ticker_data['volume'].iloc[0]
            current_price = ticker_data['close'].iloc[0]
            trading_value = volume * current_price  # 거래대금 계산
            data.append({
                'ticker': market, 
                'trading_value': trading_value,
                # 틱 계산을 위함.
                'last_tick_price': None,
                'tick': 0,
                # 매수, 매도를 위한
                'buy_tick': 0,
                'current_price': current_price,
                'remaining_amount': 0,  # 매수 코인 수량
                'buy_price': 0
            })
        time.sleep(1)
    top_coins = sorted(data, key=lambda x: x['trading_value'], reverse=True)[:count]
    return pd.DataFrame(top_coins)


def filter_top_coins_by_volume(count=10):
    """
    거래량 기준 상위 N(10)개 코인을 필터링
    """
    markets = pyupbit.get_tickers(fiat="KRW")
    data = []

    for market in markets:
        ticker_data = pyupbit.get_ohlcv(market, interval="day", count=1)
        if ticker_data is not None:
            volume = ticker_data['volume'].iloc[0]
            current_price = ticker_data['close'].iloc[0]
            data.append({
                'ticker': market, 
                'volume': volume,

                'last_tick_price': None,
                'tick': 0,

                'buy_tick': 0,
                'current_price': current_price,
                'remaining_amount': 0,  # 매수 코인 수량
                'buy_price': 0
            })
        time.sleep(1)
    top_coins = sorted(data, key=lambda x: x['volume'], reverse=True)[:count]
    return pd.DataFrame(top_coins)


def calculate_criteria(previous_data):
    """
    틱 계산의 기준 값 계산
    """
    mean_change = previous_data['close'].diff().abs().mean()  # 평균 변화량
    std_change = previous_data['close'].diff().abs().std()    # 표준편차 변화량
    return mean_change + std_change  # 기준값: 평균 + 표준편차


def update_tick(ticker_series, interval_time): 
    """
    상위 10개 코인의 데이터를 업데이트하고 틱 계산
    return : 업데이트 된 series형의 ticker 데이터
    """      
    ticker = ticker_series['ticker']
    df = pyupbit.get_ohlcv(ticker, interval= interval_time, count=25)

    if df is not None:
        current_price = df['close'].iloc[-1]
        ticker_series['current_price'] = current_price

        # 각 종목에 대해 last_tick_price가 None이면 초기화
        if pd.isna(ticker_series['last_tick_price']):
            ticker_series['last_tick_price'] = current_price

        # 가격 변화 계산
        last_tick_price = ticker_series['last_tick_price']
        cri_value = calculate_criteria(df)
        price_change = current_price - last_tick_price

        # 틱 변화 조건
        if price_change < -cri_value:
            ticker_series['tick'] += 1  # 틱 증가
            ticker_series['last_tick_price'] = current_price  # 틱 변화 시점의 가격 갱신
        
        elif price_change > cri_value:
            ticker_series['tick'] = 0
            ticker_series['last_tick_price'] = current_price

    return ticker_series
