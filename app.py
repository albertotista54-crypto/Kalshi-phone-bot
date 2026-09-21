import os, time
import requests
import streamlit as st

API="https://external-api.kalshi.com/trade-api/v2"

st.set_page_config(page_title="Kalshi Monitor", page_icon="📊", layout="centered")
st.title("📊 Kalshi Market Monitor")
st.caption("Solo lectura — no coloca órdenes.")

ticker=st.text_input("Ticker del mercado", placeholder="Ej: INXU-26SEP20-T6850").strip().upper()
seconds=st.slider("Actualización", 5, 60, 10)

def get_market(t):
    r=requests.get(f"{API}/markets/{t}", timeout=8)
    r.raise_for_status()
    return r.json().get("market", r.json())

if st.button("▶️ Iniciar monitor", use_container_width=True):
    if not ticker:
        st.error("Escribe un ticker.")
    else:
        try:
            m=get_market(ticker)
            bid=m.get("yes_bid_dollars", m.get("yes_bid"))
            ask=m.get("yes_ask_dollars", m.get("yes_ask"))
            if bid is None or ask is None:
                st.warning("El mercado no tiene bid/ask disponibles.")
            else:
                bid=float(bid); ask=float(ask); mid=(bid+ask)/2
                c1,c2,c3=st.columns(3)
                c1.metric("YES bid", f"{bid*100:.2f}¢")
                c2.metric("YES ask", f"{ask*100:.2f}¢")
                c3.metric("YES medio", f"{mid*100:.2f}¢")
                st.info("📡 Datos recibidos correctamente. Usa el gráfico de Kalshi para confirmar el contexto; esta señal no predice el resultado.")
        except Exception as e:
            st.error(f"No se pudo consultar el mercado: {e}")

st.divider()
st.subheader("Cómo usarlo")
st.write("1. Abre un mercado en Kalshi y copia su ticker. 2. Pégalo arriba. 3. Pulsa Iniciar monitor.")
st.caption("Este proyecto consulta datos públicos. No necesita tus claves privadas mientras solo lea datos públicos.")
