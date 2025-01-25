from .FiveMin3Ticks import update_tick, log_transaction
from .transaction import buy_strategy, sell_strategy
from .upbit_api import get_balance_cash
import pyupbit
import time

def monitoring_top10(top10_df):
    """
    10개 종목 모니터링
    조건 만족 종목 o => return : ticker series와 true
    조건 만족 종목 x => return : ticker dataframe과 false
    """
    for index, row in top10_df.iterrows():
        updated_row = update_tick(row, "minute3")
        if updated_row['tick'] >= 3:
            return updated_row, True # 한 개만 반환됨.
        top10_df.iloc[index] = updated_row
    return top10_df, False


def monitoring_buyticker(ticker_series, upbit, top10_df, log_file):
    """
    tick 3 이상 시시 해당 종목 모니터링
    전량 매도 시 루프 탈출
    10개 종목 업데이트 지속
    """
    monitoring = True
    before_budget = get_balance_cash(upbit)
    ticker = ticker_series['ticker']
    df = pyupbit.get_ohlcv(ticker, interval="minute1", count=30)

    while(monitoring):

        ticker_series = buy_strategy(df, ticker_series, upbit, log_file)
        ticker_series = sell_strategy(df, ticker_series, upbit, log_file)

        # 전량 매도
        remaining_amount = ticker_series['remaining_amount']
        if remaining_amount == 0:
            monitoring = False
        
        # ticker_series update
        ticker_series = update_tick(ticker_series, "minute3")

        print(ticker_series)

        time.sleep(60)
    
    after_budget = get_balance_cash(upbit)
    diff_buget = after_budget - before_budget
    log_transaction(f"After transaction => difference budget: {diff_buget}", log_file)

    # 거래 끝나면 top10_update => 끊어진 공백 발생, but 거래에 영향을 주는 건 하락, 큰 하락일 경우 RSI가 방어할 것..?
    for index, row in top10_df.iterrows():
        updated_row = update_tick(row, "minute3")
        top10_df.iloc[index] = updated_row

    return top10_df
