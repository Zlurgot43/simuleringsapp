import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

# --- Funktion för payoff ---
def calculate_payoff(start_price, leverage, direction, product_type, investment, price_range, stop_loss=None, days=20):
    direction_factor = 1 if direction == "long" else -1
    value = []

    if product_type in ["bullbear", "cfds"]:
        for end_price in price_range:
            daily_return = (end_price / start_price) ** (1 / days) - 1
            product_value = investment
            for _ in range(days):
                product_value *= 1 + leverage * daily_return * direction_factor
            value.append(product_value)

    elif product_type == "turbo":
        if stop_loss is None:
            stop_loss = start_price * (0.85 if direction == "long" else 1.15)
        for p in price_range:
            knocked = (p <= stop_loss) if direction == "long" else (p >= stop_loss)
            if knocked:
                value.append(0)
            else:
                ret = (p - start_price) / start_price * direction_factor
                value.append(investment * (1 + leverage * ret))

    elif product_type == "minifuture":
        if stop_loss is None:
            stop_loss = start_price * (0.85 if direction == "long" else 1.15)
        financing_rate = 0.0002
        if direction == "long":
            financing_level = start_price - (start_price / leverage)
        else:
            financing_level = start_price + (start_price / leverage)
        for p in price_range:
            knocked = (p <= stop_loss) if direction == "long" else (p >= stop_loss)
            if knocked or ((direction == "long" and p <= financing_level) or (direction == "short" and p >= financing_level)):
                value.append(0)
            else:
                try:
                    if direction == "long":
                        ratio = (p - financing_level) / (start_price - financing_level)
                    else:
                        ratio = (financing_level - p) / (financing_level - start_price)
                    payoff = investment * ratio * ((1 - financing_rate) ** days)
                    value.append(payoff)
                except ZeroDivisionError:
                    value.append(0)

    elif product_type == "warrant":
        strike_price = start_price * (1.05 if direction == "long" else 0.95)
        warrant_price = 1.0
        multiplier = 1
        num_warrants = investment / warrant_price

        st.session_state["strike_price"] = strike_price
        st.session_state["num_warrants"] = num_warrants

        for p in price_range:
            if direction == "long":
                intrinsic = max(p - strike_price, 0)
            else:
                intrinsic = max(strike_price - p, 0)
            total_payoff = num_warrants * intrinsic * multiplier
            value.append(total_payoff)

    elif product_type == "unlimited_turbo":
        if stop_loss is None:
            stop_loss = start_price * (0.85 if direction == "long" else 1.15)
        for p in price_range:
            knocked = (p <= stop_loss) if direction == "long" else (p >= stop_loss)
            if knocked:
                value.append(0)
            else:
                ret = (p - start_price) / start_price * direction_factor
                value.append(investment * (1 + leverage * ret))

    elif product_type == "tracker":
        for p in price_range:
            ret = (p - start_price) / start_price
            value.append(investment * (1 + ret))

    return np.array(value)

# --- Dag-för-dag simulering (bullbear) ---
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

# --- UI ---
st.set_page_config(page_title="Simulering av hävstångsprodukter", layout="centered")
st.title("📊 Simulering av hävstångsprodukter")

tickers = {
    "Tesla (TSLA)": "TSLA",
    "Apple (AAPL)": "AAPL",
    "Nvidia (NVDA)": "NVDA",
    "S&P 500 (SPY)": "SPY",
    "Bitcoin (BTC-USD)": "BTC-USD"
}
selected_asset = st.selectbox("Välj tillgång", list(tickers.keys()))
ticker_symbol = tickers[selected_asset]

try:
    ticker_data = yf.Ticker(ticker_symbol).history(period="1d")
    current_price = round(ticker_data["Close"].iloc[-1], 2)
    st.success(f"Aktuellt pris för {selected_asset}: {current_price} USD")
except:
    st.warning("Kunde inte hämta pris. Ange manuellt:")
    current_price = st.number_input("Startpris", value=100.0)

product_type = st.selectbox("Produkttyp", ["bullbear", "turbo", "cfds", "minifuture", "warrant", "unlimited_turbo", "tracker"])
direction = st.selectbox("Riktning", ["long", "short"])
if product_type in ["tracker"]:
    leverage = 1  # används inte men måste skickas med
else:
    leverage = st.slider("Hävstång", 1, 20, 5)

investment = st.number_input("Investerat belopp (kr)", value=10000)

if product_type != "bullbear":
    days = st.slider("Antal dagar i payoff-simuleringen", 1, 60, 20)

    prisförändring = st.slider("Prisförändring (%)", -50, 100, (0, 20))
    min_price = current_price * (1 + prisförändring[0] / 100)
    max_price = current_price * (1 + prisförändring[1] / 100)
    price_range = np.linspace(min_price, max_price, 100)

    stop_loss = None
    if product_type in ["turbo", "unlimited_turbo", "minifuture"]:
        stop_loss = st.number_input("Knock-out nivå", value=round(0.85 * current_price, 2))

    payoffs = calculate_payoff(current_price, leverage, direction, product_type, investment, price_range, stop_loss, days)

    if product_type == "warrant" and "strike_price" in st.session_state:
        st.info(f"Strike-pris: {st.session_state['strike_price']:.2f} USD\nAntal warranter: {st.session_state['num_warrants']:.0f}")

    fig, ax = plt.subplots()
    ax.plot(price_range, payoffs, label="Utveckling", color="blue")
    ax.axhline(y=investment, color='gray', linestyle='--', label="Break-even")
    ax.set_title("Resultat beroende på prisrörelse")
    ax.set_xlabel("Underliggande pris")
    ax.set_ylabel("Värde av position (kr)")
    ax.legend()
    st.pyplot(fig)

# Dag-för-dag ombalansering (bullbear)
if product_type == "bullbear":
    st.markdown("### 📅 Dag-för-dag simulering (Bull/Bear)")
    num_days = st.slider("Antal dagar att simulera", 1, 5, 3, key="sim_days")
    daily_changes = []
    for i in range(num_days):
        change = st.number_input(f"Prisförändring dag {i + 1} (%)", value=0.0, key=f"dag_{i+1}")
        daily_changes.append(change)
    values, underlying_values = simulate_day_by_day(current_price, leverage, direction, investment, daily_changes)

    fig2, ax1 = plt.subplots()
    ax1.plot(range(len(values)), values, marker='o', label="Produktvärde", color="blue")
    ax1.set_ylabel("Produktvärde (kr)", color="blue")
    ax1.tick_params(axis='y', labelcolor='blue')

    ax2 = ax1.twinx()
    ax2.plot(range(len(underlying_values)), underlying_values, marker='x', linestyle='--', label="Underliggande pris", color="orange")
    ax2.set_ylabel("Underliggande pris", color="orange")
    ax2.tick_params(axis='y', labelcolor='orange')

    ax1.set_title("Daglig utveckling av position vs. underliggande")
    ax1.set_xlabel("Dag")
    fig2.tight_layout()
    st.pyplot(fig2)

    st.markdown("### 🧾 Dagliga värden")
    for i, (pv, up) in enumerate(zip(values, underlying_values)):
        st.write(f"Dag {i}: Produkt = {pv:.2f} kr | Underliggande = {up:.2f}")
