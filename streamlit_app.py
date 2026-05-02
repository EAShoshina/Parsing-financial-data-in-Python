import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from model import StockModel
from moex_loader import load_moex_candles

st.set_page_config(page_title="Прогнозирование цен российских акций с MOEX", layout="wide")
st.title("Прогнозирование цен российских акций с MOEX")

symbol = st.selectbox("Выберите акцию", ["SBER", "GAZP", "LKOH"])
forecast_days = st.slider("Количество дней прогнозирования", 1, 10, 5)
n_lags = st.slider("Количество лагов для модели", 1, 5, 3)
history_days = st.slider("Количество последних дней истории для графика", 30, 365, 365)

# ДОБАВЬТЕ УНИКАЛЬНЫЙ KEY К КНОПКЕ
if st.button("Загрузить данные", key="load_data_button"):
    df = load_moex_candles(symbol, 3*252)
    if df.empty:
        st.error(f"Нет данных для {symbol}")
    else:
        st.session_state.df = df
        
        # Показываем информацию о данных
        st.subheader(f"Исторические данные: {symbol}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Всего записей", len(df))
        with col2:
            st.metric("Начальная дата", df["TRADEDATE"].min().strftime("%Y-%m-%d"))
        with col3:
            st.metric("Конечная дата", df["TRADEDATE"].max().strftime("%Y-%m-%d"))
        
        st.dataframe(df.tail(10))

# ДОБАВЬТЕ УНИКАЛЬНЫЙ KEY К КНОПКЕ
if st.button("Сделать прогноз", key="forecast_button"):
    if "df" not in st.session_state:
        st.error("Сначала загрузите данные")
    else:
        df = st.session_state.df
        
        # Показываем информацию о данных
        st.info(f"📊 Прогноз будет сделан от последней даты: **{df['TRADEDATE'].max().strftime('%Y-%m-%d')}**")
        
        model = StockModel(symbol, n_lags=n_lags)
        model.train()
        st.info(f"R² модели на тестовой выборке: {model.score:.3f}")

        df_forecast = model.forecast_n_days(df, forecast_days)
        df_plot_history = df.tail(history_days)

        # Показываем отладочную информацию
        st.write("**Отладочная информация:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"История: {len(df_plot_history)} дней")
            st.write(f"С {df_plot_history['TRADEDATE'].min().strftime('%Y-%m-%d')}")
            st.write(f"По {df_plot_history['TRADEDATE'].max().strftime('%Y-%m-%d')}")
        with col2:
            st.write(f"Прогноз: {len(df_forecast)} дней")
            st.write(f"С {df_forecast['TRADEDATE'].min().strftime('%Y-%m-%d')}")
            st.write(f"По {df_forecast['TRADEDATE'].max().strftime('%Y-%m-%d')}")
        with col3:
            # Проверяем разрыв между историей и прогнозом
            last_hist_date = df_plot_history['TRADEDATE'].max()
            first_forecast_date = df_forecast['TRADEDATE'].min()
            gap_days = (first_forecast_date - last_hist_date).days
            st.write(f"Разрыв: {gap_days} дней")
            if gap_days > 1:
                st.warning("Есть разрыв в датах!")

        

        # Сначала построим простой график для проверки
        st.subheader("График для проверки")
        fig_test = go.Figure()
        
        # ВАЖНОЕ ИЗМЕНЕНИЕ 2: Добавляем преобразование дат в строки для Plotly
        # Создаем копии с строковыми датами
        df_plot_history_str = df_plot_history.copy()
        df_forecast_str = df_forecast.copy()
        
        # Преобразуем даты в строки в формате YYYY-MM-DD
        df_plot_history_str['TRADEDATE_STR'] = df_plot_history_str['TRADEDATE'].dt.strftime('%Y-%m-%d')
        df_forecast_str['TRADEDATE_STR'] = df_forecast_str['TRADEDATE'].dt.strftime('%Y-%m-%d')
        
        fig_test.add_trace(go.Scatter(
            x=df_plot_history_str["TRADEDATE_STR"],  # Используем строковые даты
            y=df_plot_history_str["CLOSE"],
            mode='lines',
            name='История',
            line=dict(color='blue', width=1)
        ))
        fig_test.add_trace(go.Scatter(
            x=df_forecast_str["TRADEDATE_STR"],  # Используем строковые даты
            y=df_forecast_str["CLOSE"],
            mode='lines+markers',
            name='Прогноз',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        # ВАЖНОЕ ИЗМЕНЕНИЕ 3: Явно настраиваем ось X
        fig_test.update_layout(
            title=f"{symbol} ",
            xaxis_title="Дата",
            yaxis_title="Цена закрытия",
            height=400,
            xaxis=dict(
                type='category',  # Для строковых дат используем 'category'
                tickangle=45,  # Наклон подписей для лучшей читаемости
                showgrid=True,
                gridcolor='lightgray',
                tickmode='auto',
                nticks=20  # Показываем примерно 20 меток
            ),
            yaxis=dict(
                title="Цена закрытия",
                gridcolor='lightgray'
            )
        )
        st.plotly_chart(fig_test, use_container_width=True)

        # ВАЖНОЕ ИЗМЕНЕНИЕ 4: Альтернативный простой график с помощью Streamlit
        st.subheader("График (Streamlit)")
        
        # Подготавливаем данные для Streamlit chart
        history_chart = df_plot_history.set_index('TRADEDATE')[['CLOSE']].copy()
        history_chart.columns = ['История']
        
        forecast_chart = df_forecast.set_index('TRADEDATE')[['CLOSE']].copy()
        forecast_chart.columns = ['Прогноз']
        
        # Объединяем историю и прогноз
        combined_chart = pd.concat([history_chart, forecast_chart], axis=0)
        
        # Сортируем по дате
        combined_chart = combined_chart.sort_index()
        
        st.line_chart(combined_chart)

        # Затем основной свечной график
        st.subheader("Основной график (свечи)")
        fig = go.Figure()
        
        # Для свечного графика также используем строковые даты
        fig.add_trace(go.Candlestick(
            x=df_plot_history_str["TRADEDATE_STR"],  # Строковые даты
            open=df_plot_history_str["OPEN"],
            high=df_plot_history_str["HIGH"],
            low=df_plot_history_str["LOW"],
            close=df_plot_history_str["CLOSE"],
            name="История"
        ))
        fig.add_trace(go.Candlestick(
            x=df_forecast_str["TRADEDATE_STR"],  # Строковые даты
            open=df_forecast_str["OPEN"],
            high=df_forecast_str["HIGH"],
            low=df_forecast_str["LOW"],
            close=df_forecast_str["CLOSE"],
            name="Прогноз",
            increasing_line_color='green',
            decreasing_line_color='red'
        ))
        
        # ВАЖНОЕ ИЗМЕНЕНИЕ 5: Настраиваем ось X для свечного графика
        fig.update_layout(
            title=f"{symbol} — последние {history_days} дней истории + прогноз OHLCV",
            xaxis_title="Дата",
            yaxis_title="Цена",
            xaxis_rangeslider_visible=False,
            xaxis=dict(
                type='category',  # Для строковых дат
                tickangle=45,
                tickformat='%Y-%m-%d',
                tickmode='auto',
                nticks=15,
                showgrid=True,
                gridcolor='lightgray'
            ),
            yaxis=dict(
                gridcolor='lightgray'
            )
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Прогнозируемые свечи")
        st.dataframe(df_forecast)

        st.markdown("## Справка по финансовым и модельным показателям")

        st.markdown("### 1. Финансовые показатели OHLCV")
        st.markdown("""
        - **OPEN** — цена открытия торгового дня: отражает стартовую цену акции.
        - **HIGH** — максимальная цена за день: показывает наивысшее значение цены акции.
        - **LOW** — минимальная цена за день: показывает минимальное значение цены акции.
        - **CLOSE** — цена закрытия торгового дня: основная цена для анализа и построения тренда.
        - **VOLUME** — объём торгов: количество акций, купленных или проданных за день; отражает активность рынка.
        """)

        st.markdown("### 2. Показатели модели")
        st.markdown("""
        - **R² модели** — коэффициент детерминации, отражает качество прогноза:  
        1.0 — идеальное совпадение с фактическими данными,  
        0 — модель не объясняет вариацию цены,  
        <0 — модель хуже среднего значения.
        - **CLOSE_MA5 / CLOSE_MA10** — скользящие средние за 5 и 10 дней, сглаживают колебания и выявляют тренд.
        - **CLOSE_DIFF1 / CLOSE_DIFF2** — разности цены за 1 и 2 дня, показывают силу и направление движения цены.
        - **CLOSE_lagN / VOLUME_lagN** — лаговые значения цены и объёма за N предыдущих дней, учитывают исторические данные для прогнозирования следующего дня.
        """)

        st.markdown("### 3. Назначение прогноза")
        st.markdown("""
        Прогнозирование цен акций с помощью модели линейной регрессии с лагами и скользящими средними позволяет:
        1. Оценивать возможное направление движения цены на ближайшие дни.
        2. Визуализировать будущие свечи OHLCV для анализа рыночного тренда.
        3. Поддерживать принятие решений на основе данных о тенденциях и активности рынка.
        """)