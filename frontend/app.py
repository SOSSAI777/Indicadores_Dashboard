import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import asyncio
import websockets
import json
import time
import threading
from typing import Dict, Any, Optional

st.set_page_config(
    page_title="SS Consultoria e Assessoria - Indicadores Financeiros",
    page_icon="📈",
    layout="wide"
)

# Configuração
API_BASE_URL = "http://localhost:8000"

# Variáveis globais para dados em tempo real
if 'realtime_data' not in st.session_state:
    st.session_state.realtime_data = {}
if 'websocket_connected' not in st.session_state:
    st.session_state.websocket_connected = False
if 'price_history' not in st.session_state:
    st.session_state.price_history = {}
if 'current_symbol' not in st.session_state:
    st.session_state.current_symbol = None
if 'realtime_running' not in st.session_state:
    st.session_state.realtime_running = False
if 'websocket_thread' not in st.session_state:
    st.session_state.websocket_thread = None
if 'load_chart' not in st.session_state:
    st.session_state.load_chart = False
if 'selected_symbol' not in st.session_state:
    st.session_state.selected_symbol = None

st.title("📈 SS Consultoria e Assessoria - Indicadores Financeiros")
st.markdown("---")

# Funções para tempo real
def update_realtime_chart(symbol: str, historical_data: Dict) -> Optional[go.Figure]:
    """Atualiza o gráfico com dados em tempo real"""
    if not historical_data or 'data' not in historical_data or not historical_data['data']:
        return None
    
    try:
        current_data = st.session_state.realtime_data.get(symbol, {})
        df_historical = pd.DataFrame(historical_data['data'])
        df_historical['datetime'] = pd.to_datetime(df_historical['time'], unit='s')
        
        # Cria subplots para preço e volume
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=(f'{symbol} - TEMPO REAL 🔴', 'Volume'),
            row_width=[0.7, 0.3]
        )
        
        # Candlestick com dados históricos
        fig.add_trace(
            go.Candlestick(
                x=df_historical['datetime'],
                open=df_historical['open'],
                high=df_historical['high'],
                low=df_historical['low'],
                close=df_historical['close'],
                name='Histórico',
                increasing_line_color='#00C853',
                decreasing_line_color='#FF5252'
            ),
            row=1, col=1
        )
        
        # Linha do preço atual em tempo real
        if current_data.get('price'):
            current_time = datetime.now()
            
            # Adiciona linha horizontal do preço atual
            fig.add_hline(
                y=current_data['price'],
                line_dash="dash",
                line_color="yellow",
                line_width=2,
                annotation_text=f"Atual: ${current_data['price']:.4f}",
                annotation_position="top right",
                row=1, col=1
            )
            
            # Ponto do preço atual
            fig.add_trace(
                go.Scatter(
                    x=[current_time],
                    y=[current_data['price']],
                    mode='markers+text',
                    marker=dict(size=15, color='yellow', symbol='star', line=dict(width=2, color='black')),
                    text=[f"${current_data['price']:.4f}"],
                    textposition="top center",
                    textfont=dict(size=14, color='yellow'),
                    name='PREÇO ATUAL',
                    showlegend=False
                ),
                row=1, col=1
            )
        
        # Volume
        colors = ['#00C853' if close >= open_val else '#FF5252' 
                 for close, open_val in zip(df_historical['close'], df_historical['open'])]
        
        fig.add_trace(
            go.Bar(
                x=df_historical['datetime'],
                y=df_historical['volume'],
                name="Volume",
                marker_color=colors,
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # Layout do gráfico
        fig.update_layout(
            height=700,
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            showlegend=True,
            title=f"🔄 {symbol} - GRÁFICO EM TEMPO REAL",
            title_font_size=20,
            hovermode='x unified'
        )
        
        # Configura eixos
        fig.update_xaxes(title_text="Data/Hora", row=2, col=1)
        fig.update_yaxes(title_text="Preço (USD)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        
        return fig
        
    except Exception as e:
        st.error(f"Erro ao criar gráfico em tempo real: {e}")
        return None

async def websocket_listener(symbol: str):
    """Listener WebSocket para dados em tempo real"""
    try:
        async with websockets.connect(f"ws://localhost:8000/ws/realtime/{symbol}") as websocket:
            st.session_state.websocket_connected = True
            
            while (st.session_state.websocket_connected and 
                   st.session_state.current_symbol == symbol and
                   st.session_state.realtime_running):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10)
                    data = json.loads(message)
                    
                    if data.get('type') == 'price_update' and data['symbol'] == symbol:
                        st.session_state.realtime_data[symbol] = data
                        
                        # Atualiza histórico de preços
                        if symbol not in st.session_state.price_history:
                            st.session_state.price_history[symbol] = []
                        
                        price_point = {
                            'timestamp': datetime.now(),
                            'price': data['price'],
                            'volume': data.get('volume', 0)
                        }
                        
                        st.session_state.price_history[symbol].append(price_point)
                        if len(st.session_state.price_history[symbol]) > 100:
                            st.session_state.price_history[symbol] = st.session_state.price_history[symbol][-100:]
                            
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    st.error(f"Erro no WebSocket: {e}")
                    break
                    
    except Exception as e:
        st.session_state.websocket_connected = False
        st.error(f"Erro de conexão WebSocket: {e}")

def start_realtime_updates(symbol: str):
    """Inicia atualizações em tempo real em thread separada"""
    try:
        # Para qualquer atualização anterior
        stop_realtime_updates()
        
        st.session_state.current_symbol = symbol
        st.session_state.websocket_connected = True
        st.session_state.realtime_running = True
        
        # Executa WebSocket em thread separada
        def run_websocket():
            try:
                asyncio.run(websocket_listener(symbol))
            except Exception as e:
                st.session_state.websocket_connected = False
                st.session_state.realtime_running = False
        
        thread = threading.Thread(target=run_websocket, daemon=True)
        thread.start()
        st.session_state.websocket_thread = thread
        
        st.success(f"🔴 Iniciando monitoramento em tempo real para {symbol}")
        
    except Exception as e:
        st.error(f"Erro ao iniciar tempo real: {e}")

def stop_realtime_updates():
    """Para atualizações em tempo real"""
    st.session_state.websocket_connected = False
    st.session_state.current_symbol = None
    st.session_state.realtime_running = False
    if st.session_state.websocket_thread:
        st.session_state.websocket_thread = None

def fetch_chart_data(symbol: str, interval: str, period: str) -> Optional[Dict]:
    """Busca dados históricos da API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/chart/{symbol}",
            params={"interval": interval, "period": period},
            timeout=15
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erro na API: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão: {e}")
        return None
    except Exception as e:
        st.error(f"Erro inesperado: {e}")
        return None

def create_static_chart(symbol: str, historical_data: Dict, timeframe: str) -> Optional[go.Figure]:
    """Cria gráfico estático (normal)"""
    if not historical_data or 'data' not in historical_data or not historical_data['data']:
        return None
    
    try:
        df = pd.DataFrame(historical_data['data'])
        df['datetime'] = pd.to_datetime(df['time'], unit='s')
        
        # Gráfico candlestick normal
        fig = go.Figure(data=[
            go.Candlestick(
                x=df['datetime'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name="Price",
                increasing_line_color='#26a69a',
                decreasing_line_color='#ef5350'
            )
        ])
        
        fig.update_layout(
            title=f"{symbol} - {timeframe}",
            xaxis_title="Data/Hora",
            yaxis_title="Preço (USD)",
            template="plotly_dark",
            height=600,
            showlegend=True
        )
        
        return fig
    except Exception as e:
        st.error(f"Erro ao criar gráfico estático: {e}")
        return None

# Testar conexão com backend
col1, col2 = st.columns(2)

with col1:
    if st.button("🧪 Testar Conexão com Backend", use_container_width=True):
        try:
            response = requests.get(f"{API_BASE_URL}/", timeout=5)
            if response.status_code == 200:
                st.success("✅ Backend conectado com sucesso!")
            else:
                st.error(f"❌ Backend respondeu com erro: {response.status_code}")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Não foi possível conectar ao backend: {e}")

with col2:
    if st.button("📊 Testar Dados da API", use_container_width=True):
        try:
            response = requests.get(f"{API_BASE_URL}/api/symbols", timeout=5)
            if response.status_code == 200:
                data = response.json()
                st.success(f"✅ API de símbolos funcionando! {len(data.get('symbols', []))} símbolos disponíveis")
            else:
                st.error(f"❌ Erro na API: {response.status_code}")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Erro de conexão: {e}")

# Sidebar
st.sidebar.title("📊 Configurações do Gráfico")

# Busca de símbolos
search_query = st.sidebar.text_input("🔍 Buscar Ativo:", placeholder="Ex: Bitcoin, Apple, PETR4...")

# Lista de símbolos organizada por categoria
symbols_by_category = {
    "🇺🇸 Ações EUA": [
        "AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META", "NVDA", 
        "JPM", "JNJ", "V", "WMT", "PG", "DIS", "NFLX", "BA"
    ],
    "🇧🇷 Ações Brasil": [
        "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "WEGE3.SA",
        "MGLU3.SA", "B3SA3.SA", "ABEV3.SA", "RENT3.SA", "BBDC3.SA"
    ],
    "₿ Criptomoedas": [
        "BTC-USD", "ETH-USD", "ADA-USD", "DOT-USD", "SOL-USD",
        "DOGE-USD", "XRP-USD", "LTC-USD", "BNB-USD", "MATIC-USD"
    ],
    "📊 ETFs": [
        "SPY", "QQQ", "IVV", "VTI", "GLD"
    ],
    "💱 Forex": [
        "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDBRL=X", "EURBRL=X"
    ],
    "🛢️ Commodities": [
        "GC=F", "SI=F", "CL=F", "NG=F", "ZC=F"
    ]
}

# Filtro por categoria
selected_category = st.sidebar.selectbox(
    "Categoria:",
    ["Todos"] + list(symbols_by_category.keys())
)

# Seleção de símbolo
all_symbols = []
for category_symbols in symbols_by_category.values():
    all_symbols.extend(category_symbols)

if search_query:
    filtered_symbols = [s for s in all_symbols if search_query.upper() in s.upper()]
else:
    if selected_category == "Todos":
        filtered_symbols = all_symbols
    else:
        filtered_symbols = symbols_by_category[selected_category]

symbol = st.sidebar.selectbox(
    "Selecione o Símbolo:",
    filtered_symbols,
    index=0 if filtered_symbols else 0
)

# Timeframes expandidos
timeframe = st.sidebar.selectbox(
    "Timeframe:",
    ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"],
    index=5  # 1h como padrão
)

# Período automático baseado no timeframe
period_map = {
    "1m": "1d",    # 1 dia para 1 minuto
    "5m": "5d",    # 5 dias para 5 minutos
    "15m": "5d",   # 5 dias para 15 minutos
    "30m": "10d",  # 10 dias para 30 minutos
    "1h": "1mo",   # 1 mês para 1 hora
    "4h": "3mo",   # 3 meses para 4 horas
    "1d": "6mo",   # 6 meses para 1 dia
    "1w": "2y"     # 2 anos para 1 semana
}

period = period_map.get(timeframe, "6mo")

# Controles de tempo real
st.sidebar.markdown("---")
st.sidebar.subheader("⚡ Controles Tempo Real")

realtime_col1, realtime_col2 = st.sidebar.columns(2)

with realtime_col1:
    if st.button("▶️ Iniciar", use_container_width=True):
        start_realtime_updates(symbol)
        st.session_state.load_chart = True
        st.rerun()

with realtime_col2:
    if st.button("⏹️ Parar", use_container_width=True):
        stop_realtime_updates()
        st.rerun()

# Status da conexão
if st.session_state.websocket_connected and st.session_state.realtime_running:
    st.sidebar.success("🔴 TEMPO REAL ATIVO")
    st.sidebar.info(f"Monitorando: {st.session_state.current_symbol}")
else:
    st.sidebar.info("⚪ Tempo Real Inativo")

# Atalhos rápidos para ativos populares
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Ativos Populares")

popular_assets = {
    "₿ Bitcoin": "BTC-USD",
    "🔷 Ethereum": "ETH-USD", 
    "🍎 Apple": "AAPL",
    "🛢️ Petrobras": "PETR4.SA",
    "🛒 Magazine": "MGLU3.SA",
    "💰 Dólar": "USDBRL=X",
    "🥇 Ouro": "GC=F",
    "📊 S&P 500": "SPY"
}

cols = st.sidebar.columns(2)
for i, (name, asset_symbol) in enumerate(popular_assets.items()):
    with cols[i % 2]:
        if st.button(name, use_container_width=True):
            symbol = asset_symbol
            st.session_state.selected_symbol = asset_symbol
            st.session_state.load_chart = True
            stop_realtime_updates()
            st.rerun()

# Buscar e mostrar dados
if st.sidebar.button("🎯 Carregar Gráfico", type="primary", use_container_width=True):
    st.session_state.load_chart = True
    stop_realtime_updates()

# Área principal do gráfico
if st.session_state.get('load_chart'):
    with st.spinner(f"Buscando dados para {symbol}..."):
        try:
            # Busca dados históricos
            historical_data = fetch_chart_data(symbol, timeframe, period)
            
            if historical_data and 'data' in historical_data and historical_data['data']:
                
                if st.session_state.websocket_connected and st.session_state.realtime_running:
                    # MODO TEMPO REAL
                    st.warning("🔴 MODO TEMPO REAL ATIVO")
                    
                    # Atualiza gráfico uma vez
                    fig = update_realtime_chart(symbol, historical_data)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Mostra métricas atuais
                    current_data = st.session_state.realtime_data.get(symbol, {})
                    if current_data:
                        st.subheader("📊 Dados em Tempo Real")
                        
                        col1, col2, col3, col4, col5 = st.columns(5)
                        
                        with col1:
                            st.metric(
                                "Preço Atual", 
                                f"${current_data.get('price', 0):.4f}",
                                f"{current_data.get('change_percent', 0):+.2f}%"
                            )
                        with col2:
                            st.metric("Abertura", f"${current_data.get('open', 0):.4f}")
                        with col3:
                            st.metric("Alta", f"${current_data.get('high', 0):.4f}")
                        with col4:
                            st.metric("Baixa", f"${current_data.get('low', 0):.4f}")
                        with col5:
                            st.metric("Volume", f"{current_data.get('volume', 0):,}")
                    
                    # Botão para atualizar manualmente
                    if st.button("🔄 Atualizar Agora"):
                        st.rerun()
                    
                else:
                    # MODO NORMAL (ESTÁTICO)
                    fig = create_static_chart(symbol, historical_data, timeframe)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                
                # Informações do ativo (comum aos dois modos)
                if 'info' in historical_data:
                    st.markdown("---")
                    st.subheader("📋 Informações do Ativo")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Símbolo", historical_data['info'].get('symbol', symbol))
                    with col2:
                        st.metric("Nome", historical_data['info'].get('name', 'N/A'))
                    with col3:
                        st.metric("Período", f"{len(historical_data['data'])} registros")
                    with col4:
                        st.metric("Timeframe", timeframe)
                    
                    # Estatísticas básicas
                    df = pd.DataFrame(historical_data['data'])
                    if len(df) > 0:
                        st.markdown("---")
                        st.subheader("📈 Estatísticas")
                        
                        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                        
                        with stats_col1:
                            current_price = df['close'].iloc[-1]
                            st.metric("Preço Atual", f"${current_price:.4f}")
                        
                        with stats_col2:
                            price_change = df['close'].iloc[-1] - df['close'].iloc[0]
                            change_percent = (price_change / df['close'].iloc[0]) * 100
                            st.metric("Variação Total", f"${price_change:.4f}", f"{change_percent:+.2f}%")
                        
                        with stats_col3:
                            max_price = df['high'].max()
                            st.metric("Máximo", f"${max_price:.4f}")
                        
                        with stats_col4:
                            min_price = df['low'].min()
                            st.metric("Mínimo", f"${min_price:.4f}")
                
                # Tabela de dados
                with st.expander("📋 Ver Dados Brutos"):
                    df = pd.DataFrame(historical_data['data'])
                    df['datetime'] = pd.to_datetime(df['time'], unit='s')
                    st.dataframe(df[['datetime', 'open', 'high', 'low', 'close', 'volume']], use_container_width=True)
                
            else:
                st.error("❌ Nenhum dado retornado pela API")
                if historical_data:
                    st.json(historical_data)
                    
        except Exception as e:
            st.error(f"❌ Erro inesperado: {e}")

# Status dos serviços
st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Status dos Serviços")

if st.sidebar.button("🔄 Verificar Status", use_container_width=True):
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            st.sidebar.success("✅ Backend: Online")
        else:
            st.sidebar.error("❌ Backend: Offline")
    except:
        st.sidebar.error("❌ Backend: Offline")

# Informações
st.sidebar.markdown("---")
st.sidebar.info("""
**💡 Instruções:**
1. Selecione ativo e timeframe
2. Clique em "Carregar Gráfico" para modo normal
3. Clique em "Iniciar" para tempo real
4. Use "Atualizar Agora" para refresh manual

**⏰ Timeframes:**
- 1m-30m: Day trading
- 1h-4h: Swing trading  
- 1d-1w: Investimento
""")

# Mensagem inicial se nenhum gráfico foi carregado
if not st.session_state.get('load_chart') and not st.session_state.websocket_connected:
    st.info("👆 **Selecione um ativo e clique em 'Carregar Gráfico' para começar**")
    
    # Mostrar categorias disponíveis
    st.markdown("---")
    st.subheader("📂 Categorias Disponíveis")
    
    for category, symbols in symbols_by_category.items():
        with st.expander(f"{category} ({len(symbols)} ativos)"):
            cols = st.columns(3)
            for i, symbol_item in enumerate(symbols):
                with cols[i % 3]:
                    if st.button(symbol_item, key=f"cat_{category}_{symbol_item}"):
                        symbol = symbol_item
                        st.session_state.selected_symbol = symbol_item
                        st.session_state.load_chart = True
                        stop_realtime_updates()
                        st.rerun()

# Limpar estado quando mudar de símbolo
if st.session_state.get('selected_symbol') and st.session_state.selected_symbol != symbol:
    stop_realtime_updates()
    st.session_state.selected_symbol = symbol

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        <p>SS Consultoria e Assessoria - Sistema de Análise Financeira</p>
        <p>Desenvolvido com Streamlit, Plotly e FastAPI</p>
    </div>
    """,
    unsafe_allow_html=True
)