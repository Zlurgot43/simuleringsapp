import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

def calculate_payoff(start_price, leverage, direction, product_type, investment, price_range, stop_loss=None):
    movement = price_range - start_price if direction == "long" else start_price - price_range
    if product_type in ["bullbear", "cfds"]:
        return_pct = (movement / start_price) * leverage
        return investment * (1 + return_pct)
    elif product_type == "turbo":
        if stop_loss is None:
            stop_loss = start_price * (0.85 if direction == "long" else 1.15)
        value = []
        for p in price_range:
            knocked = (p <= stop_loss) if direction == "long" else (p >= stop_loss)
            if knocked:
                value.append(0)
            else:
                ret = (movement[np.where(price_range == p)][0] / start_price) * leverage
                value.append(investment * (1 + ret))
        return np.array(value)

st.title("📊 Simulering av hävstångsprodukter")
st.markdown("Testa hur din position hade utvecklats beroende på produkt, riktning och marknadsrörelse.")

product_type = st.selectbox("Produkttyp", ["bullbear", "turbo", "cfds"])
direction = st.selectbox("Riktning", ["long", "short"])
leverage = st.slider("Hävstång", 1, 20, 5)
start_price = st.number_input("Startpris (underliggande)", value=100.0)
investment = st.number_input("Investerat belopp (kr)", value=10000)
stop_loss = None
if product_type == "turbo":
    stop_loss = st.number_input("Stop-loss-nivå", value=start_price * 0.85)

price_min = st.slider("Lägsta pris", 50, int(start_price), int(start_price * 0.7))
price_max = st.slider("Högsta pris", int(start_price), 200, int(start_price * 1.3))
price_range = np.linspace(price_min, price_max, 300)

result = calculate_payoff(start_price, leverage, direction, product_type, investment, price_range, stop_loss)

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(price_range, result, label=f"{product_type.capitalize()} {direction} x{leverage}", linewidth=2)
ax.axhline(investment, color='gray', linestyle='--', label="Break-even")
if product_type == "turbo":
    ax.axvline(stop_loss, color='red', linestyle=':', label="Stop-loss")
ax.set_title("Simulerad utveckling")
ax.set_xlabel("Pris på underliggande tillgång")
ax.set_ylabel("Positionens värde (kr)")
ax.grid(True)
ax.legend()
st.pyplot(fig)
