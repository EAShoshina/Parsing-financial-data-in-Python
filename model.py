import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import joblib
import os
from moex_loader import load_moex_candles
from pandas.tseries.offsets import BDay

class StockModel:
    def __init__(self, symbol, cache_dir="models", n_lags=3):
        self.symbol = symbol
        self.n_lags = n_lags
        self.model = LinearRegression()
        self.trained = False
        self.score = None
        self.feature_cols = None
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.model_path = os.path.join(self.cache_dir, f"{symbol}_lr.pkl")
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            self.trained = True

    def _prepare_features(self, df):
        df = df.sort_values("TRADEDATE").copy()
        # Скользящие средние
        df["CLOSE_MA5"] = df["CLOSE"].rolling(5).mean().shift(1)
        df["CLOSE_MA10"] = df["CLOSE"].rolling(10).mean().shift(1)
        # Разности цен
        df["CLOSE_DIFF1"] = df["CLOSE"].diff(1)
        df["CLOSE_DIFF2"] = df["CLOSE"].diff(2)
        # Лаги
        for lag in range(1, self.n_lags+1):
            df[f"CLOSE_lag{lag}"] = df["CLOSE"].shift(lag)
            df[f"VOLUME_lag{lag}"] = df["VOLUME"].shift(lag)
        df = df.dropna()
        self.feature_cols = [f"CLOSE_lag{lag}" for lag in range(1, self.n_lags+1)] + \
                            [f"VOLUME_lag{lag}" for lag in range(1, self.n_lags+1)] + \
                            ["CLOSE_MA5", "CLOSE_MA10", "CLOSE_DIFF1", "CLOSE_DIFF2"]
        X = df[self.feature_cols]
        y = df["CLOSE"].shift(-1).dropna()
        X = X.iloc[:-1]
        return X, y

    def train(self):
        df = load_moex_candles(self.symbol, 3*252)
        X, y = self._prepare_features(df)
        split = int(0.8 * len(X))
        X_train, X_test = X.iloc[:split], X.iloc[split:]
        y_train, y_test = y.iloc[:split], y.iloc[split:]
        self.model.fit(X_train, y_train)
        self.trained = True
        y_pred = self.model.predict(X_test)
        self.score = r2_score(y_test, y_pred)
        joblib.dump(self.model, self.model_path)

    def predict_next(self, last_rows):
        if not self.trained:
            self.train()
        data = {}
        data["CLOSE_MA5"] = last_rows["CLOSE"].tail(5).mean()
        data["CLOSE_MA10"] = last_rows["CLOSE"].tail(10).mean()
        data["CLOSE_DIFF1"] = last_rows["CLOSE"].diff(1).iloc[-1]
        data["CLOSE_DIFF2"] = last_rows["CLOSE"].diff(2).iloc[-1]
        for lag in range(1, self.n_lags+1):
            data[f"CLOSE_lag{lag}"] = last_rows["CLOSE"].iloc[-lag]
            data[f"VOLUME_lag{lag}"] = last_rows["VOLUME"].iloc[-lag]
        X_pred = pd.DataFrame([[data[col] for col in self.feature_cols]], columns=self.feature_cols)
        return float(self.model.predict(X_pred)[0])

    def forecast_n_days(self, df, n_days):
        """Прогноз на n рабочих дней вперед"""
        
        # Убедимся, что данные отсортированы
        df = df.sort_values("TRADEDATE").copy()
        
        # Импортируем BDay
        from pandas.tseries.offsets import BDay
        
        # Получаем последнюю дату
        last_date = df["TRADEDATE"].iloc[-1]
        
        # Создаем даты для прогноза (только рабочие дни)
        forecast_dates = pd.date_range(
            start=last_date + BDay(1),
            periods=n_days,
            freq='B'  # 'B' = Business day frequency
        )
        
        forecast = []
        df_last = df.copy()
        
        for i, next_date in enumerate(forecast_dates):
            pred_close = self.predict_next(df_last)
            last_row = df_last.iloc[-1]
            
            # Генерация OHLCV
            open_price = last_row["CLOSE"]
            close_price = pred_close
            
            # Волатильность
            high_price = max(close_price, open_price) * (1 + np.random.uniform(0, 0.01))
            low_price = min(close_price, open_price) * (1 - np.random.uniform(0, 0.01))
            
            # Объем
            volume = last_row["VOLUME"] * (1 + np.random.uniform(-0.05, 0.05))
            
            # Корректировка High/Low
            if high_price < low_price:
                high_price, low_price = low_price, high_price
            
            new_row = {
                "TRADEDATE": next_date,
                "OPEN": round(open_price, 2),
                "HIGH": round(high_price, 2),
                "LOW": round(low_price, 2),
                "CLOSE": round(close_price, 2),
                "VOLUME": int(volume)
            }
            
            forecast.append(new_row)
            
            # Обновляем df_last для следующей итерации
            new_df = pd.DataFrame([new_row])
            df_last = pd.concat([df_last, new_df], ignore_index=True)
        
        forecast_df = pd.DataFrame(forecast)
        
        # ДЕБАГ
        print(f"\n[DEBUG] Прогноз: {last_date} -> {forecast_df['TRADEDATE'].iloc[0]} ... {forecast_df['TRADEDATE'].iloc[-1]}")
        
        return forecast_df