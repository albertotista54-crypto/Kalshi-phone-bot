import requests
import streamlit as st
from datetime import datetime, timezone

API = "https://api.elections.kalshi.com/trade-api/v2"

st.set_page_config(
    page_title="Kalshi BTC Monitor",
    page_icon="₿"
)

st.title("₿ Kalshi BTC 15M Monitor")
st.caption("Solo lectura — no coloca órdenes.")

def buscar_mercados():
    respuesta = requests.get(
        f"{API}/markets",
        params={
            "series_ticker": "KXBTC15M",
            "status": "open",
            "limit": 100
        },
        timeout=10
    )

    respuesta.raise_for_status()

    return respuesta.json().get("markets", [])


def numero(valor):
    if valor is None:
        return None

    try:
        return float(valor)
    except:
        return None


if st.button("🔍 Buscar mercado BTC 15M", use_container_width=True):

    try:
        mercados = buscar_mercados()

        if not mercados:
            st.warning("No hay mercados BTC 15M abiertos en este momento.")

        else:
            # Ordenar por hora de cierre
            mercados.sort(
                key=lambda m: m.get("close_time", "")
            )

            mercado = mercados[0]

            ticker = mercado.get("ticker", "Desconocido")
            close_time = mercado.get("close_time", "")

            bid = numero(
                mercado.get(
                    "yes_bid_dollars",
                    mercado.get("yes_bid")
                )
            )

            ask = numero(
                mercado.get(
                    "yes_ask_dollars",
                    mercado.get("yes_ask")
                )
            )

            st.success("✅ Mercado encontrado")

            st.subheader("Mercado actual")

            st.code(ticker)

            if close_time:
                st.write(f"⏰ Cierre: {close_time}")

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "YES BID",
                    f"${bid:.4f}" if bid is not None else "N/A"
                )

            with col2:
                st.metric(
                    "YES ASK",
                    f"${ask:.4f}" if ask is not None else "N/A"
                )

            if bid is not None and ask is not None:
                mid = (bid + ask) / 2

                st.metric(
                    "Precio medio",
                    f"${mid:.4f}"
                )

    except Exception as e:
        st.error(f"❌ Error al consultar Kalshi: {e}")
