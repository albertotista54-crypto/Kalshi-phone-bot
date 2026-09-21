import requests
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timezone

# =========================================================
# CONFIGURACIÓN
# =========================================================

KALSHI_API = "https://api.elections.kalshi.com/trade-api/v2"
COINBASE_API = "https://api.exchange.coinbase.com"

st.set_page_config(
    page_title="BTC 15M Smart Monitor",
    page_icon="₿",
    layout="centered"
)

st.title("₿ BTC 15M Smart Monitor")
st.caption("🔴 Solo lectura — análisis técnico, no coloca órdenes.")

# =========================================================
# FUNCIONES
# =========================================================

def numero(valor):
    if valor is None:
        return None

    try:
        return float(valor)
    except:
        return None


def buscar_mercado():
    respuesta = requests.get(
        f"{KALSHI_API}/markets",
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


def obtener_btc():
    respuesta = requests.get(
        f"{COINBASE_API}/products/BTC-USD/ticker",
        timeout=10
    )

    respuesta.raise_for_status()

    data = respuesta.json()

    return float(data["price"])


def obtener_velas():
    respuesta = requests.get(
        f"{COINBASE_API}/products/BTC-USD/candles",
        params={
            "granularity": 900
        },
        timeout=10
    )

    respuesta.raise_for_status()

    datos = respuesta.json()

    if not datos:
        return None

    df = pd.DataFrame(
        datos,
        columns=[
            "time",
            "low",
            "high",
            "open",
            "close",
            "volume"
        ]
    )

    df["time"] = pd.to_datetime(
        df["time"],
        unit="s",
        utc=True
    )

    for columna in [
        "low",
        "high",
        "open",
        "close",
        "volume"
    ]:
        df[columna] = pd.to_numeric(
            df[columna],
            errors="coerce"
        )

    df = df.sort_values("time")

    return df


def obtener_target(mercado):

    target = mercado.get("floor_strike")

    if target is None:
        target = mercado.get("custom_strike")

    if target is None:
        target = mercado.get("functional_strike")

    return numero(target)


# =========================================================
# INDICADORES
# =========================================================

def calcular_rsi(series, periodo=14):

    delta = series.diff()

    ganancias = delta.clip(lower=0)
    perdidas = -delta.clip(upper=0)

    promedio_ganancia = ganancias.rolling(
        periodo
    ).mean()

    promedio_perdida = perdidas.rolling(
        periodo
    ).mean()

    rs = promedio_ganancia / promedio_perdida

    rsi = 100 - (
        100 / (1 + rs)
    )

    return rsi


def analizar(df):

    df = df.copy()

    df["EMA9"] = df["close"].ewm(
        span=9,
        adjust=False
    ).mean()

    df["EMA21"] = df["close"].ewm(
        span=21,
        adjust=False
    ).mean()

    df["RSI"] = calcular_rsi(
        df["close"],
        14
    )

    df["cambio_3"] = (
        df["close"]
        .pct_change(3)
        * 100
    )

    df["cambio_1"] = (
        df["close"]
        .pct_change(1)
        * 100
    )

    return df


def calcular_score(df):

    ultimo = df.iloc[-1]

    score = 50

    # EMA
    if ultimo["EMA9"] > ultimo["EMA21"]:
        score += 15
    else:
        score -= 15

    # Precio vs EMA9
    if ultimo["close"] > ultimo["EMA9"]:
        score += 10
    else:
        score -= 10

    # Momentum
    if ultimo["cambio_3"] > 0:
        score += 10
    else:
        score -= 10

    # RSI
    rsi = ultimo["RSI"]

    if not np.isnan(rsi):

        if 50 <= rsi <= 70:
            score += 10

        elif 30 <= rsi < 50:
            score -= 5

        elif rsi > 70:
            score -= 5

        elif rsi < 30:
            score += 5

    score = max(
        0,
        min(100, score)
    )

    return score


def obtener_tendencia(score):

    if score >= 65:
        return "🟢 ALCISTA"

    if score <= 35:
        return "🔴 BAJISTA"

    return "🟡 NEUTRAL"


# =========================================================
# MONITOR
# =========================================================

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

        target = obtener_target(
            mercado
        )

        close_time = mercado.get(
            "close_time"
        )

        # -------------------------------------------------
        # BTC
        # -------------------------------------------------

        btc = obtener_btc()

        # -------------------------------------------------
        # VELAS
        # -------------------------------------------------

        df = obtener_velas()

        if df is None or len(df) < 30:

            st.warning(
                "Esperando suficientes velas..."
            )

            return

        df = analizar(df)

        ultimo = df.iloc[-1]

        score = calcular_score(df)

        tendencia = obtener_tendencia(
            score
        )

        # -------------------------------------------------
        # MERCADO
        # -------------------------------------------------

        st.success(
            "🟢 Mercado BTC 15M encontrado"
        )

        st.subheader(
            "Mercado actual"
        )

        st.code(ticker)

        # -------------------------------------------------
        # TIEMPO
        # -------------------------------------------------

        if close_time:

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

                segundos = int(
                    (
                        cierre - ahora
                    ).total_seconds()
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

                pass

        # -------------------------------------------------
        # BTC VS TARGET
        # -------------------------------------------------

        st.subheader(
            "₿ BTC vs Target"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "BTC",
                f"${btc:,.2f}"
            )

        with col2:

            st.metric(
                "🎯 Target",
                f"${target:,.2f}"
                if target is not None
                else "N/A"
            )

        if target is not None:

            diferencia = btc - target

            porcentaje = (
                diferencia
                / target
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
                    "🟡 BTC está exactamente en el Target"
                )

        # -------------------------------------------------
        # SEÑAL TÉCNICA
        # -------------------------------------------------

        st.subheader(
            "🧠 Análisis técnico"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Tendencia",
                tendencia
            )

        with col2:

            st.metric(
                "Fuerza técnica",
                f"{score}/100"
            )

        st.caption(
            "⚠️ Esta puntuación NO representa "
            "una probabilidad de ganar. Resume "
            "varios indicadores técnicos."
        )

        # -------------------------------------------------
        # INDICADORES
        # -------------------------------------------------

        st.subheader(
            "📊 Indicadores"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "EMA 9",
                f"${ultimo['EMA9']:,.2f}"
            )

            st.metric(
                "RSI",
                f"{ultimo['RSI']:.1f}"
                if not np.isnan(ultimo["RSI"])
                else "N/A"
            )

        with col2:

            st.metric(
                "EMA 21",
                f"${ultimo['EMA21']:,.2f}"
            )

            st.metric(
                "Momentum 3 velas",
                f"{ultimo['cambio_3']:+.3f}%"
            )

        # -------------------------------------------------
        # INTERPRETACIÓN
        # -------------------------------------------------

        st.subheader(
            "🔎 Lectura"
        )

        if (
            ultimo["EMA9"]
            > ultimo["EMA21"]
            and ultimo["close"]
            > ultimo["EMA9"]
        ):

            st.success(
                "🟢 La estructura actual favorece "
                "movimiento alcista."
            )

        elif (
            ultimo["EMA9"]
            < ultimo["EMA21"]
            and ultimo["close"]
            < ultimo["EMA9"]
        ):

            st.error(
                "🔴 La estructura actual favorece "
                "movimiento bajista."
            )

        else:

            st.warning(
                "🟡 El mercado está mezclado/neutral. "
                "No hay una señal técnica limpia."
            )

        # -------------------------------------------------
        # RSI
        # -------------------------------------------------

        rsi = ultimo["RSI"]

        if not np.isnan(rsi):

            if rsi >= 70:

                st.warning(
                    f"⚠️ RSI {rsi:.1f}: "
                    "zona elevada."
                )

            elif rsi <= 30:

                st.warning(
                    f"⚠️ RSI {rsi:.1f}: "
                    "zona baja."
                )

            else:

                st.write(
                    f"RSI actual: **{rsi:.1f}**"
                )

        # -------------------------------------------------
        # GRÁFICO
        # -------------------------------------------------

        st.subheader(
            "📈 BTC — velas de 15 minutos"
        )

        grafico = df[
            [
                "close",
                "EMA9",
                "EMA21"
            ]
        ].tail(50)

        grafico = grafico.rename(
            columns={
                "close": "BTC",
                "EMA9": "EMA 9",
                "EMA21": "EMA 21"
            }
        )

        st.line_chart(
            grafico,
            height=350
        )

        # -------------------------------------------------
        # ÚLTIMAS VELAS
        # -------------------------------------------------

        st.subheader(
            "🕯️ Últimas velas"
        )

        ultimas = df.tail(5)[
            [
                "time",
                "open",
                "high",
                "low",
                "close"
            ]
        ].copy()

        ultimas["time"] = ultimas[
            "time"
        ].dt.strftime(
            "%H:%M"
        )

        st.dataframe(
            ultimas,
            hide_index=True,
            use_container_width=True
        )

        st.caption(
            "🔄 Actualización automática cada 10 segundos"
        )

        st.caption(
            "⚠️ BTC mostrado es precio spot de Coinbase. "
            "Puede diferir del índice utilizado por Kalshi "
            "para la liquidación."
        )

    except Exception as e:

        st.error(
            f"❌ Error al consultar datos: {e}"
        )


monitor()
