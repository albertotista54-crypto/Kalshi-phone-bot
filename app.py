import requests
import streamlit as st
from datetime import datetime, timezone

API = "https://api.elections.kalshi.com/trade-api/v2"

st.set_page_config(
    page_title="Kalshi BTC 15M",
    page_icon="₿"
)

st.title("₿ Kalshi BTC 15M Monitor")
st.caption("🔴 Solo lectura — no coloca órdenes.")


# -----------------------------
# Buscar mercado BTC 15M
# -----------------------------

def buscar_mercado():

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

    mercados = respuesta.json().get("markets", [])

    if not mercados:
        return None

    mercados.sort(
        key=lambda m: m.get("close_time", "")
    )

    return mercados[0]


# -----------------------------
# Convertir precio
# -----------------------------

def precio(mercado, nombre_dolares, nombre_normal):

    valor = mercado.get(
        nombre_dolares,
        mercado.get(nombre_normal)
    )

    if valor is None:
        return None

    try:
        return float(valor)
    except:
        return None


# -----------------------------
# Historial
# -----------------------------

if "historial" not in st.session_state:
    st.session_state.historial = []

if "ticker_anterior" not in st.session_state:
    st.session_state.ticker_anterior = None


# -----------------------------
# Monitor automático
# -----------------------------

@st.fragment(run_every="10s")
def monitor():

    try:

        mercado = buscar_mercado()

        if mercado is None:
            st.warning(
                "⚠️ No hay un mercado BTC 15M abierto."
            )
            return

        ticker = mercado.get(
            "ticker",
            "N/A"
        )

        close_time = mercado.get(
            "close_time",
            "N/A"
        )

        bid = precio(
            mercado,
            "yes_bid_dollars",
            "yes_bid"
        )

        ask = precio(
            mercado,
            "yes_ask_dollars",
            "yes_ask"
        )

        # -----------------------------
        # Detectar cambio de mercado
        # -----------------------------

        if (
            st.session_state.ticker_anterior
            != ticker
        ):

            st.session_state.historial = []

            st.session_state.ticker_anterior = ticker


        # -----------------------------
        # Precio medio
        # -----------------------------

        medio = None

        if bid is not None and ask is not None:

            medio = (bid + ask) / 2


        # -----------------------------
        # Guardar historial
        # -----------------------------

        if medio is not None:

            hora = datetime.now(
                timezone.utc
            ).strftime("%H:%M:%S")

            st.session_state.historial.append(
                {
                    "hora": hora,
                    "precio": medio
                }
            )

            # Guardar solamente los últimos
            # 60 registros
            st.session_state.historial = (
                st.session_state.historial[-60:]
            )


        # -----------------------------
        # Encabezado
        # -----------------------------

        st.success(
            "🟢 Mercado BTC 15M encontrado"
        )

        st.subheader("Mercado actual")

        st.code(ticker)


        # -----------------------------
        # Tiempo restante
        # -----------------------------

        if close_time != "N/A":

            try:

                cierre = datetime.fromisoformat(
                    close_time.replace(
                        "Z",
                        "+00:00"
                    )
                )

                ahora = datetime.now(
                    timezone.utc
                )

                restante = (
                    cierre - ahora
                )

                segundos = int(
                    restante.total_seconds()
                )

                if segundos > 0:

                    minutos = segundos // 60
                    seg = segundos % 60

                    st.info(
                        f"⏰ Tiempo restante: "
                        f"{minutos:02d}:{seg:02d}"
                    )

                else:

                    st.warning(
                        "⏰ Mercado cerrando..."
                    )

            except:

                st.write(
                    f"⏰ Cierre: {close_time}"
                )


        # -----------------------------
        # Precios
        # -----------------------------

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "🟢 YES",
                f"${medio:.4f}"
                if medio is not None
                else "N/A"
            )

        with col2:

            if medio is not None:

                no = 1 - medio

                st.metric(
                    "🔴 NO",
                    f"${no:.4f}"
                )

            else:

                st.metric(
                    "🔴 NO",
                    "N/A"
                )


        # -----------------------------
        # Bid / Ask
        # -----------------------------

        st.subheader("Mercado")

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "YES BID",
                f"${bid:.4f}"
                if bid is not None
                else "N/A"
            )

        with col2:

            st.metric(
                "YES ASK",
                f"${ask:.4f}"
                if ask is not None
                else "N/A"
            )


        # -----------------------------
        # Gráfico
        # -----------------------------

        st.subheader(
            "📈 Movimiento de YES"
        )

        if st.session_state.historial:

            datos = st.session_state.historial

            precios = [
                x["precio"]
                for x in datos
            ]

            st.line_chart(
                precios,
                height=300
            )

            st.caption(
                f"Registros: {len(precios)} "
                f"• Actualización cada 10 segundos"
            )

        else:

            st.info(
                "Esperando datos para crear el gráfico..."
            )


        # -----------------------------
        # Último precio
        # -----------------------------

        if medio is not None:

            st.subheader(
                "📊 Último precio"
            )

            st.write(
                f"YES: **${medio:.4f}**"
            )

            st.write(
                f"NO: **${1 - medio:.4f}**"
            )


        st.caption(
            "🔄 Actualización automática cada 10 segundos"
        )


    except Exception as e:

        st.error(
            f"❌ Error al consultar Kalshi: {e}"
        )


monitor()
