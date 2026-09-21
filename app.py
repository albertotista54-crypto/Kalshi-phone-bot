import requests
import streamlit as st
from datetime import datetime, timezone

# =========================
# CONFIGURACIÓN
# =========================

API = "https://api.elections.kalshi.com/trade-api/v2"
BTC_API = "https://api.coinbase.com/v2/prices/BTC-USD/spot"

st.set_page_config(
    page_title="Kalshi BTC 15M Monitor",
    page_icon="₿",
    layout="centered"
)

st.title("₿ Kalshi BTC 15M Monitor")
st.caption("🔴 Solo lectura — no coloca órdenes.")

# =========================
# FUNCIONES
# =========================

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

    # Elegimos el mercado que cierre primero
    mercados.sort(key=lambda m: m.get("close_time", ""))

    return mercados[0]


def numero(valor):
    if valor is None:
        return None

    try:
        return float(valor)
    except:
        return None


def obtener_btc():
    respuesta = requests.get(
        BTC_API,
        timeout=10
    )

    respuesta.raise_for_status()

    data = respuesta.json()

    return float(data["data"]["amount"])


def obtener_target(mercado):
    # Campo principal utilizado por los mercados BTC
    target = mercado.get("floor_strike")

    if target is None:
        target = mercado.get("custom_strike")

    if target is None:
        target = mercado.get("functional_strike")

    return numero(target)


def texto_condicion(mercado):
    strike_type = mercado.get("strike_type")

    yes_subtitle = mercado.get("yes_sub_title")

    if yes_subtitle:
        return yes_subtitle

    condiciones = {
        "greater": "BTC termina por encima del Target",
        "greater_or_equal": "BTC termina en o por encima del Target",
        "less": "BTC termina por debajo del Target",
        "less_or_equal": "BTC termina en o por debajo del Target",
        "between": "BTC termina dentro del rango"
    }

    return condiciones.get(
        strike_type,
        "Revisar reglas del mercado"
    )


# =========================
# HISTORIAL
# =========================

if "historial" not in st.session_state:
    st.session_state.historial = []

if "ticker_anterior" not in st.session_state:
    st.session_state.ticker_anterior = None


# =========================
# MONITOR
# =========================

@st.fragment(run_every="10s")
def monitor():

    try:

        mercado = buscar_mercado()

        if mercado is None:
            st.warning("⚠️ No hay un mercado BTC 15M abierto.")
            return

        ticker = mercado.get("ticker", "N/A")

        # =========================
        # TARGET
        # =========================

        target = obtener_target(mercado)

        # =========================
        # PRECIOS KALSHI
        # =========================

        yes_bid = numero(
            mercado.get("yes_bid_dollars")
        )

        yes_ask = numero(
            mercado.get("yes_ask_dollars")
        )

        no_bid = numero(
            mercado.get("no_bid_dollars")
        )

        no_ask = numero(
            mercado.get("no_ask_dollars")
        )

        last_price = numero(
            mercado.get("last_price_dollars")
        )

        # Precio medio YES
        yes_medio = None

        if yes_bid is not None and yes_ask is not None:
            yes_medio = (yes_bid + yes_ask) / 2

        # =========================
        # CAMBIO DE MERCADO
        # =========================

        if st.session_state.ticker_anterior != ticker:

            st.session_state.historial = []
            st.session_state.ticker_anterior = ticker

        # =========================
        # BTC
        # =========================

        btc = None

        try:
            btc = obtener_btc()
        except:
            pass

        # =========================
        # HISTORIAL
        # =========================

        if btc is not None:

            hora = datetime.now(
                timezone.utc
            ).strftime("%H:%M:%S")

            st.session_state.historial.append({
                "hora": hora,
                "btc": btc
            })

            st.session_state.historial = (
                st.session_state.historial[-120:]
            )

        # =========================
        # ENCABEZADO
        # =========================

        st.success("🟢 Mercado BTC 15M encontrado")

        st.subheader("Mercado actual")

        st.code(ticker)

        # =========================
        # TIEMPO RESTANTE
        # =========================

        close_time = mercado.get(
            "close_time"
        )

        if close_time:

            try:

                cierre = datetime.fromisoformat(
                    close_time.replace("Z", "+00:00")
                )

                ahora = datetime.now(timezone.utc)

                restante = cierre - ahora

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

        # =========================
        # BTC Y TARGET
        # =========================

        st.subheader("₿ BTC vs Target")

        col1, col2 = st.columns(2)

        with col1:

            if btc is not None:

                st.metric(
                    "BTC referencia",
                    f"${btc:,.2f}"
                )

            else:

                st.metric(
                    "BTC referencia",
                    "N/A"
                )

        with col2:

            if target is not None:

                st.metric(
                    "🎯 Target",
                    f"${target:,.2f}"
                )

            else:

                st.metric(
                    "🎯 Target",
                    "N/A"
                )

        # =========================
        # DISTANCIA
        # =========================

        if btc is not None and target is not None:

            diferencia = btc - target

            porcentaje = (
                diferencia / target
            ) * 100

            if diferencia > 0:

                st.success(
                    f"🟢 BTC está "
                    f"${abs(diferencia):,.2f} "
                    f"POR ENCIMA del Target "
                    f"({porcentaje:+.3f}%)"
                )

            elif diferencia < 0:

                st.error(
                    f"🔴 BTC está "
                    f"${abs(diferencia):,.2f} "
                    f"POR DEBAJO del Target "
                    f"({porcentaje:+.3f}%)"
                )

            else:

                st.warning(
                    "🟡 BTC está exactamente "
                    "en el Target"
                )

        # =========================
        # CONDICIÓN YES
        # =========================

        st.subheader("📌 Condición del mercado")

        st.write(
            texto_condicion(mercado)
        )

        # =========================
        # YES / NO
        # =========================

        st.subheader("📊 Mercado")

        col1, col2 = st.columns(2)

        with col1:

            if yes_medio is not None:

                st.metric(
                    "🟢 YES",
                    f"${yes_medio:.4f}"
                )

            else:

                st.metric(
                    "🟢 YES",
                    "N/A"
                )

        with col2:

            if no_bid is not None and no_ask is not None:

                no_medio = (
                    no_bid + no_ask
                ) / 2

                st.metric(
                    "🔴 NO",
                    f"${no_medio:.4f}"
                )

            elif yes_medio is not None:

                st.metric(
                    "🔴 NO",
                    f"${1 - yes_medio:.4f}"
                )

            else:

                st.metric(
                    "🔴 NO",
                    "N/A"
                )

        # =========================
        # BID / ASK
        # =========================

        st.subheader("📖 Precios")

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "YES BID",
                f"${yes_bid:.4f}"
                if yes_bid is not None
                else "N/A"
            )

        with col2:

            st.metric(
                "YES ASK",
                f"${yes_ask:.4f}"
                if yes_ask is not None
                else "N/A"
            )

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "NO BID",
                f"${no_bid:.4f}"
                if no_bid is not None
                else "N/A"
            )

        with col2:

            st.metric(
                "NO ASK",
                f"${no_ask:.4f}"
                if no_ask is not None
                else "N/A"
            )

        # =========================
        # ÚLTIMO PRECIO
        # =========================

        if last_price is not None:

            st.metric(
                "Última operación",
                f"${last_price:.4f}"
            )

        # =========================
        # GRÁFICO BTC
        # =========================

        st.subheader("📈 Movimiento de BTC")

        if st.session_state.historial:

            datos = st.session_state.historial

            precios = [
                x["btc"]
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
                "Esperando datos de BTC..."
            )

        # =========================
        # RESUMEN
        # =========================

        st.subheader("🔎 Resumen")

        if btc is not None and target is not None:

            diferencia = btc - target

            if diferencia > 0:

                st.write(
                    "🟢 BTC actualmente está "
                    "**por encima** del Target."
                )

            elif diferencia < 0:

                st.write(
                    "🔴 BTC actualmente está "
                    "**por debajo** del Target."
                )

            else:

                st.write(
                    "🟡 BTC está exactamente "
                    "en el Target."
                )

        if yes_medio is not None:

            st.write(
                f"Precio medio de YES: "
                f"**${yes_medio:.4f}**"
            )

            st.caption(
                "El precio de YES refleja la valoración "
                "actual del mercado; no es una garantía "
                "del resultado."
            )

        st.caption(
            "🔄 Actualización automática cada 10 segundos"
        )

        st.caption(
            "⚠️ El precio BTC mostrado es una referencia "
            "spot y puede diferir del índice utilizado "
            "para la liquidación de Kalshi."
        )

    except Exception as e:

        st.error(
            f"❌ Error al consultar datos: {e}"
        )


monitor()
