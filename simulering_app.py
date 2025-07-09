import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

# Funktioner
def calculate_payoff(start_price, leverage, direction, product_type, investment, price_range, stop_loss=None, days=20, kostnad_per_dag=0.0):
    direction_factor = 1 if direction == "long" else -1
    value = []

    for p in price_range:
        if product_type in ["turbo", "unlimited_turbo"]:
            knocked = (p <= stop_loss) if direction == "long" else (p >= stop_loss)
            if knocked:
                value.append(0)
            else:
                ret = (p - start_price) / start_price * direction_factor
                val = investment * (1 + leverage * ret)
                val *= (1 - kostnad_per_dag) ** days
                value.append(val)

        elif product_type == "minifuture":
            price = start_price
            val = investment
            for _ in range(days):
                daily_return = (p / price) ** (1 / days) - 1
                val *= 1 + leverage * daily_return * direction_factor
                val *= 1 - kostnad_per_dag
                price *= 1 + daily_return
            value.append(val)

        elif product_type == "warrant":
            strike_price = start_price * (1.05 if direction == "long" else 0.95)
            intrinsic = max((p - strike_price) if direction == "long" else (strike_price - p), 0)
            value.append(investment * leverage * intrinsic / start_price)

        elif product_type == "tracker":
            ret = (p - start_price) / start_price
            val = investment * (1 + ret)
            val *= (1 - kostnad_per_dag) ** days
            value.append(val)

        elif product_type == "cfds":
            val = investment
            daily_return = (p / start_price) ** (1 / days) - 1
            for _ in range(days):
                val *= 1 + leverage * daily_return * direction_factor
            value.append(val)

    return np.array(value)

def simulate_day_by_day(start_price, leverage, direction, investment, daily_changes):
    direction_factor = 1 if direction == "long" else -1
    product_value = investment
    price = start_price
    values = [product_value]
    underlying = [price]
    for change_pct in daily_changes:
        price *= 1 + change_pct / 100
        product_value *= 1 + direction_factor * leverage * (change_pct / 100)
        values.append(product_value)
        underlying.append(price)
    return values, underlying

# Layout
st.set_page_config(page_title="Simulering av hävstångsprodukter", layout="wide")
st.markdown("### 📊 Simulering av hävstångsprodukter")

# Kolumner
col1, col2 = st.columns([1, 1.3])

# Vänsterkolumn
with col1:
    tickers = {
        "Tesla (TSLA)": "TSLA", "Apple (AAPL)": "AAPL", "Nvidia (NVDA)": "NVDA", "Amazon (AMZN)": "AMZN",
        "Google (GOOGL)": "GOOGL", "Meta (META)": "META", "Microsoft (MSFT)": "MSFT",
        "OMXS30": "^OMX", "S&P 500 (SPY)": "SPY", "Nasdaq 100 (NDX)": "^NDX", "Dow Jones (DJI)": "^DJI",
        "Bitcoin (BTC)": "BTC-USD", "Ethereum (ETH)": "ETH-USD", "Guld (Gold)": "GC=F", "Olja (Brent)": "BZ=F"
    }

    search_query = st.text_input("🔎 Sök tillgång", "").lower()
    filtered_tickers = {k: v for k, v in tickers.items() if search_query in k.lower()} or tickers
    selected_asset = st.selectbox("Välj tillgång", list(filtered_tickers.keys()), index=0)
    ticker_symbol = filtered_tickers[selected_asset]

    try:
        current_price = round(yf.Ticker(ticker_symbol).history(period="1d")["Close"].iloc[-1], 2)
        st.success(f"Aktuellt pris för {selected_asset}: {current_price} USD")
    except:
        current_price = st.number_input("Startpris (USD)", value=100.0)

    product_type = st.selectbox("Produkttyp", ["bullbear", "turbo", "cfds", "minifuture", "warrant", "unlimited_turbo", "tracker"])
    direction = st.selectbox("Riktning", ["long", "short"])
    investment = st.number_input("Investerat belopp (kr)", value=10000)
    leverage = st.slider("Hävstång", 1, 20, 5)

    kostnad_per_dag = st.number_input("Daglig kostnad (%)", value=0.0, step=0.01) / 100 if product_type not in ["bullbear", "warrant"] else 0.0
    days = st.slider("Simulerade dagar", 1, 60, 20)

    stop_loss = st.number_input("Knock-out-nivå", value=round(current_price * 0.85, 2)) if product_type in ["turbo", "unlimited_turbo"] else None

    if product_type == "bullbear":
        num_days = st.slider("Antal dagar att simulera", 1, 5, 3)
        daily_changes = [st.number_input(f"Dag {i+1} (% förändring)", value=0.0, step=0.1, key=f"dag_{i}") for i in range(num_days)]

# Högerkolumn
with col2:
    if product_type == "bullbear":
        values, under = simulate_day_by_day(current_price, leverage, direction, investment, daily_changes)
        fig, ax1 = plt.subplots(figsize=(6.5, 3))
        ax1.plot(range(len(values)), values, marker='o', color="blue")
        ax2 = ax1.twinx()
        ax2.plot(range(len(under)), under, marker='x', linestyle='--', color="orange")
        ax1.set_xlabel("Dag")
        ax1.set_ylabel("Produktvärde (kr)", color="blue")
        ax2.set_ylabel("Pris", color="orange")
        ax1.set_title("📈 Dag-för-dag utveckling")
        st.pyplot(fig)

        for i, (pv, up) in enumerate(zip(values, under)):
            st.caption(f"Dag {i}: Produkt = {pv:.2f} kr | Underliggande = {up:.2f} USD")

    else:
        price_range = np.linspace(current_price * 0.6, current_price * 1.4, 100)
        payoff = calculate_payoff(current_price, leverage, direction, product_type, investment, price_range, stop_loss, days, kostnad_per_dag)

        fig, ax = plt.subplots(figsize=(6.5, 3))
        ax.plot(price_range, payoff, label="Med avgift", color="blue")
        ax.axhline(y=investment, linestyle="--", color="gray", label="Break-even")
        ax.set_xlabel("Pris")
        ax.set_ylabel("Värde (kr)")
        ax.set_title("📊 Payoff beroende på underliggande pris")
        ax.legend()
        st.pyplot(fig)
