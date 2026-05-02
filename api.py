from fastapi import FastAPI, HTTPException
from moex_loader import load_moex_candles
from model import StockModel

app = FastAPI()
models_cache = {}

@app.get("/stocks/{symbol}")
def stock_data(symbol: str):
    df = load_moex_candles(symbol, 90)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Нет данных для {symbol}")
    return df.to_dict(orient="records")

@app.get("/predict/{symbol}")
def predict(symbol: str):
    df = load_moex_candles(symbol, 5)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Нет данных для {symbol}")
    last = df.iloc[-1]

    if symbol not in models_cache:
        models_cache[symbol] = StockModel(symbol)
    
    model = models_cache[symbol]
    pred = model.predict(last)
    return {"symbol": symbol, "predict_close": pred, "model_r2": model.score}
