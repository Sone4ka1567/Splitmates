from datetime import datetime, timedelta

import yfinance as yf

CURRENCY_EXCHANGE_OPTIONS = ['USD', 'EUR', 'RUB']


async def get_exchange_rate(currency_from: str, currency_to: str, amount: float, date_str):
    if (currency_from not in CURRENCY_EXCHANGE_OPTIONS) or (currency_to not in CURRENCY_EXCHANGE_OPTIONS):
        return None
    
    rub_flag = False
    if currency_from == "RUB":
        currency_from, currency_to = currency_to, currency_from
        rub_flag = True
    
    try:
        date = datetime.strptime(date_str[:10], "%Y-%m-%d")
    except Exception as e:
        raise ValueError("Date should be formatted as YYYY-MM-DD")
    # нужны данные за ближайший к date рабочий день (возможно сам date)
    prefix_date = date - timedelta(days=10)

    ticker = yf.Ticker(f"{currency_from+currency_to}=X")
    hist = ticker.history(interval='15m', start=prefix_date, end=date)
    exchange_rate = hist.iloc[-1]['Open']
    #print(f"Last available data up to the given date from: {hist.iloc[-1].name.date()}")

    if rub_flag:
        exchange_rate = 1 / exchange_rate

    return exchange_rate * amount