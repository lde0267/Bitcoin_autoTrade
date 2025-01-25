import pandas

# MACD 계산 함수
def calculate_macd(df, fast_period=12, slow_period=26, signal_period=9):
    """
    MACD 계산 함수
    :param df: 종목 데이터 (OHLCV)
    :param fast_period: 빠른 EMA 기간 (기본 12)
    :param slow_period: 느린 EMA 기간 (기본 26)
    :param signal_period: 시그널 기간 (기본 9)
    :return: MACD, Signal, Histogram
    """
    df['ema_fast'] = df['close'].ewm(span=fast_period, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=slow_period, adjust=False).mean()
    df['macd'] = df['ema_fast'] - df['ema_slow']
    df['signal'] = df['macd'].ewm(span=signal_period, adjust=False).mean()
    # df['histogram'] = df['macd'] - df['signal']
    return df

# RSI 계산 함수
def calculate_rsi(df, period=14):
    """
    RSI 계산 함수
    :param df: 종목 데이터 (OHLCV)
    :param period: RSI 계산 기간 (기본 14)
    :return: RSI
    """
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df

def buy_signal(df):
    """매수 신호 판단 함수"""
    macd_df = calculate_macd(df)
    rsi_df = calculate_rsi(df)

    macd = macd_df['macd']
    signal = macd_df['signal']
    rsi = rsi_df['rsi']
    
    if macd.iloc[-1] > signal.iloc[-1] and rsi.iloc[-1] > 40:
        return True  # 매수 신호
    return False  # 매수 신호 아님

def sell_signal(df):
    """매도 신호 판단 함수"""
    macd_df = calculate_macd(df)
    rsi_df = calculate_rsi(df)

    macd = macd_df['macd']
    signal = macd_df['signal']
    rsi = rsi_df['rsi']
    
    if macd.iloc[-1] < signal.iloc[-1] and rsi.iloc[-1] < 50:
        return True  # 매도 신호
    return False  # 매도 신호 아님