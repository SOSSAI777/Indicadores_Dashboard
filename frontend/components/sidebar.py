import streamlit as st

def render_sidebar():
    """Renderiza a sidebar com controles"""
    st.sidebar.title("📈 TradingView Clone")
    st.sidebar.markdown("---")
    
    # Seleção de símbolo
    symbols = {
        "Apple": "AAPL",
        "Google": "GOOGL", 
        "Microsoft": "MSFT",
        "Tesla": "TSLA",
        "Amazon": "AMZN",
        "Magazine Luiza": "MGLU3.SA",
        "Petrobras": "PETR4.SA",
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD"
    }
    
    selected_name = st.sidebar.selectbox(
        "Selecione o Ativo:",
        options=list(symbols.keys()),
        index=0
    )
    symbol = symbols[selected_name]
    
    # Timeframe
    timeframes = {
        "1 Minuto": "1m",
        "5 Minutos": "5m", 
        "15 Minutos": "15m",
        "1 Hora": "1h",
        "4 Horas": "4h",
        "1 Dia": "1d"
    }
    
    selected_tf_name = st.sidebar.selectbox(
        "Timeframe:",
        options=list(timeframes.keys()),
        index=5  # 1d como padrão
    )
    timeframe = timeframes[selected_tf_name]
    
    # Período baseado no timeframe
    period_options = {
        "1m": ["1d", "2d", "5d"],
        "5m": ["1d", "2d", "5d", "1mo"],
        "15m": ["5d", "1mo", "3mo"],
        "1h": ["1mo", "3mo", "6mo"],
        "4h": ["3mo", "6mo", "1y"],
        "1d": ["6mo", "1y", "2y", "5y"]
    }
    
    period = st.sidebar.selectbox(
        "Período:",
        options=period_options.get(timeframe, ["6mo"]),
        index=0
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("🎯 **MVP Fase 1**\n- Gráfico Candlestick\n- Dados Históricos\n- Múltiplos Timeframes")
    
    return symbol, timeframe, period