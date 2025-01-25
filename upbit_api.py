import pyupbit
import time

def get_api_keys(file_path):
    """
    API 키 파일에서 읽어오기
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        access_key = file.readline().strip()
        secret_key = file.readline().strip()
    return access_key, secret_key

def get_upbit_instance(file_path):
    """
    Upbit 객체 생성
    """
    access_key, secret_key = get_api_keys(file_path)
    return pyupbit.Upbit(access_key, secret_key)

def get_balance_cash(upbit):
    """
    현재 자산 조회
    """
    try:
        return upbit.get_balance("KRW")
    except Exception as e:
        print(f"잔고를 불러오는 중 오류가 발생했습니다: {e}")
        return None

def get_balances_coin(upbit):
    """
    현재 보유 중인 코인과 수량을 조회
    """
    balances = upbit.get_balances()
    holdings = []
    for balance in balances:
        ticker = balance['currency']
        if ticker == "KRW":
            continue  # 원화는 제외
        qty = float(balance['balance'])
        if qty > 0:
            holdings.append({
                'ticker': f"KRW-{ticker}",
                'quantity': qty
            })
    return holdings

def fetch_data(fetch_func, max_retries=20, delay=0.5):
    """
    데이터를 반복적으로 요청하여 가져옵니다.
    :param fetch_func: 데이터를 가져오는 함수
    :param max_retries: 최대 시도 횟수
    :param delay: 각 시도 간 대기 시간(초)
    :return: 가져온 데이터 또는 None
    """
    for _ in range(max_retries):
        res = fetch_func()  # 데이터를 가져오는 함수 호출
        if res is not None:  # 데이터가 유효한 경우 반환
            return res
        time.sleep(delay)  # 대기 후 다시 시도
    return None  # 데이터 가져오기 실패

def cancel_order(order_uuid, upbit):
    """
    특정 주문을 취소합니다.
    :param order_uuid: 취소할 주문의 UUID
    :param upbit: Upbit API 객체
    :return: 취소 성공 여부
    """
    try:
        res = upbit.cancel_order(order_uuid)
        if "error" in res:
            print(f"Cancel Order Error: {res}")
            return False
        print(f"Order {order_uuid} cancelled successfully.")
        return True
    except Exception as e:
        print(f"Exception during order cancellation: {e}")
        return False

def track_order_execution(order_uuid, upbit, max_retries=20, delay=0.5):
    """
    주문 체결 상태를 추적합니다.
    :param order_uuid: 추적할 주문의 UUID
    :param upbit: Upbit API 객체
    :param max_retries: 최대 시도 횟수
    :param delay: 각 시도 간 대기 시간(초)
    :return: 체결된 수량 또는 None
    """
    def fetch_func():
        try:
            order_info = upbit.get_order(order_uuid)
            if "error" in order_info:
                print(f"Order Info Error: {order_info}")
                return None
            return float(order_info.get('executed_volume', 0))
        except Exception as e:
            print(f"Exception during order tracking: {e}")
            return None

    executed_volume = fetch_data(fetch_func, max_retries=max_retries, delay=delay)
    return executed_volume

def order_buy(ticker, buy_amount, upbit):
    """
    시장가 매수 주문을 실행하고 체결된 수량을 반환합니다.
    :param ticker: 매수할 종목 티커
    :param buy_amount: 매수 금액
    :param upbit: Upbit API 객체
    :return: 성공 여부와 체결된 수량
    """
    if buy_amount < 5000:
        print("Amount must be greater than 5000 KRW")
        return False, 0

    try:
        res = upbit.buy_market_order(ticker, buy_amount)
        time.sleep(5) # 주문하고 10초 기다리기기
        if 'error' in res:
            print(f"Order Error: {res}")
            return False, 0

        order_uuid = res.get('uuid')
        if not order_uuid:
            print("Order UUID not found in response.")
            return False, 0

        executed_volume = track_order_execution(order_uuid, upbit)
        if executed_volume:
            return True, executed_volume

        print("Order not executed within the timeout. Cancelling...")
        cancel_order(order_uuid, upbit)
        return False, 0

    except Exception as e:
        print(f"Exception during order: {e}")
        return False, 0

def order_sell(ticker, sell_amount, upbit):
    """
    시장가 매도 주문을 실행하고 체결된 수량을 반환합니다.
    :param ticker: 매도할 종목 티커
    :param sell_amount: 매도 수량
    :param upbit: Upbit API 객체
    :return: 성공 여부와 체결된 수량
    """
    if sell_amount <= 0:
        print("Sell amount must be greater than 0")
        return False, 0

    try:
        res = upbit.sell_market_order(ticker, sell_amount)
        time.sleep(5) # 주문하고 5초 기다리기기
        if 'error' in res:
            print(f"Order Error: {res}")
            return False, 0

        order_uuid = res.get('uuid')
        if not order_uuid:
            print("Order UUID not found in response.")
            return False, 0

        executed_volume = track_order_execution(order_uuid, upbit)
        if executed_volume:
            return True, executed_volume

        print("Order not executed within the timeout. Cancelling...")
        cancel_order(order_uuid, upbit)
        return False, 0

    except Exception as e:
        print(f"Exception during order: {e}")
        return False, 0

