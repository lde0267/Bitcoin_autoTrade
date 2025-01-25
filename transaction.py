from .upbit_api import get_balance_cash, order_buy, get_balances_coin, order_sell
from .FiveMin3Ticks import log_transaction
from .indicator import buy_signal, sell_signal

def buy_strategy(df, ticker_series, upbit, log_file):
    """
    매수 전략 구현
    tick에 따라 buy_percetage 추출, 매수 금액 산정
    매수 주문 실행, 주문 성공 시 변수 업데이트
    """
    budget = int(get_balance_cash(upbit))  # 자산
    tick = ticker_series['tick']
    indicator = buy_signal(df)
    buy_tick = ticker_series['buy_tick']

    if tick >= 3 and indicator and buy_tick < tick: # 각 틱 당 한번만 매수
        ticker = ticker_series['ticker']
        current_price = df['close'].iloc[-1]

        # 틱에 따른 매수 비율 결정
        buy_percentage = 0
        if tick == 3:
            buy_percentage = 0.5  # 예산의 50% 매수수
        elif tick >= 4:
            buy_percentage = 0.5 # 남은 예산의 50% 매수
        elif tick >= 5:
            buy_percentage = 1 # 남은 예산을 매수 

        # 매수 금액 계산
        amount_to_buy = budget * buy_percentage * (1 - 0.05)  # 수수료 반영

        if amount_to_buy > 5000:  # 최소 매수 금액 조건

            order_success, excuted_volume = order_buy(ticker, amount_to_buy, upbit)
            if order_success:  # 주문 성공 시 업데이트
                ticker_series['remaining_amount'] += excuted_volume  # 보유 코인 금액 증가
                ticker_series['buy_price'] = current_price  # 매수 시점 가격
                ticker_series['buy_tick'] = tick
                print(f"Buy=> {amount_to_buy} of {ticker} at {current_price} (Tick: {tick}).")
                log_transaction(f"Buy=> {amount_to_buy} of {ticker} at {current_price} (Tick: {tick}).", log_file)
        return ticker_series

    else: return ticker_series


def sell_strategy(df, ticker_series, upbit, log_file):
    """
    매도 전략 구현
    손절 조건, 익절 조건 명시
    매도 주문 실행, 주문 성공 시 변수 업데이트
    """
    current_price = ticker_series['current_price']
    remaining_amount = ticker_series['remaining_amount']

    buy_price = ticker_series['buy_price']
    ticker = ticker_series['ticker']
    excuted_volume = 0

    indicator = sell_signal(df)

    # 보유 코인 수량 조회
    holdings = get_balances_coin(upbit)
    
    for holding in holdings:
        if holding['ticker'] == ticker:
            remaining_amount = holding['quantity']
            break

    # 보유량이 없으면 종료
    if buy_price is None or remaining_amount <= 0:
        ticker_series['remaining_amount'] = 0
        return ticker_series
    
    # 손절 조건: -0.5% 하락, 자산을 어느정도 투자했을 때
    if ((current_price - buy_price) / buy_price <= -0.05) and (remaining_amount * buy_price > 400000):
        order_success, excuted_volume = order_sell(ticker, remaining_amount, upbit)
        if order_success:
            remaining_amount -= excuted_volume
            log_transaction(f"Sell=> {excuted_volume * current_price} of {ticker} at {current_price}", log_file)
            print(f"Sell=> {excuted_volume * current_price} of {ticker} at {current_price}")

    # 조금의 익절도 잡아내야 함. => 추후에 수정이 필요, rsi, macd 반응이 한발 느린 감이 있음. 1분봉이긴 하지만,, 일단 고
    elif indicator:
        order_success, excuted_volume = order_sell(ticker, remaining_amount, upbit)
        if order_success:
            remaining_amount -= excuted_volume
            log_transaction(f"Sell=> {excuted_volume * current_price} of {ticker} at {current_price}", log_file)
            print(f"Sell=> {excuted_volume * current_price} of {ticker} at {current_price}")

    # 익절 조건: +1% 상승 + 1번만 실행
    elif (current_price - buy_price) / buy_price >= 0.01 and (current_price * remaining_amount > 400000):
        amount_to_sell_half = remaining_amount / 2
        order_success, excuted_volume = order_sell(ticker, amount_to_sell_half, upbit)
        if order_success:
            remaining_amount -= excuted_volume
            log_transaction(f"Sell=> {excuted_volume * current_price} of {ticker} at {current_price}", log_file)
            print(f"Sell=> {excuted_volume * current_price} of {ticker} at {current_price}")
    
    ticker_series['remaining_amount'] = remaining_amount

    return ticker_series
