import requests
import pandas as pd
from datetime import datetime, timedelta

def load_moex_candles(symbol="SBER", days=365):
    """Загружает данные с MOEX за последние `days` дней."""
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)

    url = f"https://iss.moex.com/iss/engines/stock/markets/shares/securities/{symbol}/candles.json"
    params = {
        "interval": 24,
        "from": start_date.strftime("%Y-%m-%d"),
        "till": end_date.strftime("%Y-%m-%d")
    }
    r = requests.get(url, params=params)
    js = r.json()
    candles = js["candles"]["data"]
    cols = js["candles"]["columns"]
    df = pd.DataFrame(candles, columns=cols)
    df = df.rename(columns={
        "open":"OPEN","close":"CLOSE","high":"HIGH","low":"LOW",
        "volume":"VOLUME","begin":"TRADEDATE"
    })
    df["TRADEDATE"] = pd.to_datetime(df["TRADEDATE"])
    df = df.sort_values("TRADEDATE").reset_index(drop=True)
    return df

def load_moex_candles(symbol="SBER", days=365):
    """Загружает данные с MOEX за последние `days` дней."""
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)

    url = f"https://iss.moex.com/iss/engines/stock/markets/shares/securities/{symbol}/candles.json"
    params = {
        "interval": 24,
        "from": start_date.strftime("%Y-%m-%d"),
        "till": end_date.strftime("%Y-%m-%d")
    }
    r = requests.get(url, params=params)
    js = r.json()
    candles = js["candles"]["data"]
    
    # ДЕБАГГИНГ: проверьте что возвращает API
    print(f"\n=== ДЕБАГГИНГ MOEX API ===")
    print(f"Символ: {symbol}")
    print(f"Период: {start_date} - {end_date}")
    print(f"Количество свечей: {len(candles)}")
    if candles:
        print(f"Первая дата: {candles[0][6]}")  # 6-й элемент это 'begin'
        print(f"Последняя дата: {candles[-1][6]}")
    
    cols = js["candles"]["columns"]
    df = pd.DataFrame(candles, columns=cols)
    df = df.rename(columns={
        "open":"OPEN","close":"CLOSE","high":"HIGH","low":"LOW",
        "volume":"VOLUME","begin":"TRADEDATE"
    })
    df["TRADEDATE"] = pd.to_datetime(df["TRADEDATE"])
    df = df.sort_values("TRADEDATE").reset_index(drop=True)
    
    # ДЕБАГГИНГ 2: проверьте датафрейм
    print(f"\nДатафрейм:")
    print(f"Размер: {df.shape}")
    print(f"Диапазон дат: {df['TRADEDATE'].min()} - {df['TRADEDATE'].max()}")
    print("="*50)
    
    return df