import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Simulering av hävstångsprodukter", page_icon="📊", layout="centered")

st.title("📊 Simulering av hävstångsprodukter")
st.write("Testa hur din position hade utvecklats beroende på produkt, riktning och marknadsrörelse.")

# Steg 1: Tillgångsval
assets = {
    "Tesla (TSLA)": "TSLA",
    "Apple (AAPL)": "AAPL",
    "Bitcoin (BTC-USD)": "BTC-USD",
    "Ethereum (ETH-USD)": "ETH-USD",
    "OMX Stockholm 30 (OMXS30.ST)": "^OMX"
}
chosen_asset = st.selectbox("Välj tillgång", list(assets.keys()))
ticker_symbol = assets[chosen_asset]

try:
    ticker = yf.Ticker(ticker_symbol)
    current_price = ticker.history(period="1d")["Close"].iloc[-1]
    st.success(f"Aktuellt pris för {chosen_asset}: {current_price:.2f} USD")
except Exception as e:
    st.error("Kunde inte hämta pris för tillgången.")
    st.stop()

# Steg 2: Parametrar för simulering
product_type = st.selectbox("Produkttyp", ["bullbear", "minifuture", "warrant"])
direction = st.selectbox("Riktning", ["long", "short"])
leverage = st.slider("Hävstång", 1, 20, 5)
investment = st.number_input("Investerat belopp (kr)", value=10000)
min_price = st.number_input("Lägsta pris", value=current_price * 0.8)
max_price = st.number_input("Högsta pris", value=current_price * 1.2)

# Steg 3: Beräkning
prices = np.linspace(min_price, max_price, 100)
if direction == "long":
    change = (prices - current_price) / current_price
else:
    change = (current_price - prices) / current_price

if product_type == "bullbear":
    result = investment * (1 + leverage * change)
elif product_type == "minifuture":
    result = investment * (1 + leverage * change)  # förenklat
elif product_type == "warrant":
    result = investment * (1 + leverage * change)  # förenklat
else:
    result = investment

# Steg 4: Visa graf
fig, ax = plt.subplots()
ax.plot(prices, result)
ax.axvline(current_price, color='gray', linestyle='--', label='Startpris')
ax.set_xlabel("Underliggande pris")
ax.set_ylabel("Värde på position (kr)")
ax.set_title("Simulerat resultat")
ax.legend()
st.pyplot(fig)
