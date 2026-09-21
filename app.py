import time
import requests
import streamlit as st

API = "https://api.elections.kalshi.com/trade-api/v2"

st.set_page_config(
    page_title="Kalshi Monitor",
    page_icon="📊"
)

st.title("📊 Kalshi Market Monitor")
st.caption("Solo lectura — no coloca órdenes.")

seconds = st.slider("Actualización", 5, 60, 10)


def get_open_markets():
    r = requests.get(
        f"{API}/markets",
        params={
            "series_ticker": "KXBTC15M",
            "status": "open",
            "limit": 100
        },
        timeout=10
    )
    r.raise_for_status()
    return r.json().get("markets", [])


def get_market(ticker):
    r = requests.get(
        f"{API}/markets/{ticker}",
        timeout=10
    )
    r.raise_for_status()
    return r.json().get("market", r.json())


if st.button("▶️ Buscar mercado BTC 15m", use_container_width=True):

    try:
        markets = get_open_markets()

        if not markets:
            st.warning("No se encontró ningún mercado BTC 15m abierto.")
        else:
            # Mostrar los mercados encontrados
            st.success(f"Mercados BTC 15m abiertos encontrados: {len(markets)}")

            for market in markets[:10]:

                ticker = market.get("ticker", "N/A")
                title = market.get("title", "")
                bid = market.get(
                    "yes_bid_dollars",
                    market.get("yes_bid")
                )
                ask = market.get(
                    "yes_ask_dollars",
                    market.get("yes_ask")
                )

                st.subheader(ticker)

                if title:
                    st.write(title)

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("YES BID", bid if bid is not None else "N/A")

                with col2:
                    st.metric("YES ASK", ask if ask is not None else "N/A")

    except Exception as e:
        st.error(f"No se pudo consultar Kalshi: {e}")
