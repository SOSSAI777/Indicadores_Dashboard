import plotly.graph_objects as go
import plotly.subplots as sp
import pandas as pd
from datetime import datetime

def create_candlestick_chart(data, symbol, timeframe):
    """Cria gráfico candlestick com Plotly"""
    
    if not data or 'data' not in data or not data['data']:
        return go.Figure().add_annotation(
            text="❌ Nenhum dado disponível",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=20)
        )
    
    # Prepara dados
    df = pd.DataFrame(data['data'])
    df['datetime'] = pd.to_datetime(df['time'], unit='s')
    
    # Cria subplots
    fig = sp.make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(f'{symbol} - {timeframe}', 'Volume'),
        row_width=[0.7, 0.3]
    )
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df['datetime'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Price',
            increasing_line_color='#26a69a',  # Verde
            decreasing_line_color='#ef5350'   # Vermelho
        ),
        row=1, col=1
    )
    
    # Volume
    colors = ['#26a69a' if close >= open else '#ef5350' 
              for close, open in zip(df['close'], df['open'])]
    
    fig.add_trace(
        go.Bar(
            x=df['datetime'],
            y=df['volume'],
            name="Volume",
            marker_color=colors,
            opacity=0.7
        ),
        row=2, col=1
    )
    
    # Layout
    fig.update_layout(
        height=700,
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        showlegend=False,
        margin=dict(l=50, r=50, t=80, b=50),
        title=f"TradingView Clone - {data['info']['name']} ({symbol})",
        font=dict(family="Arial, sans-serif", size=12, color="#fff")
    )
    
    # Configura eixos
    fig.update_xaxes(title_text="Data/Hora", row=2, col=1)
    fig.update_yaxes(title_text="Preço (USD)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    return fig

def display_chart_info(data):
    """Exibe informações sobre os dados do gráfico"""
    if not data or 'info' not in data:
        return
    
    info = data['info']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Símbolo", info['symbol'])
    
    with col2:
        st.metric("Nome", info['name'])
    
    with col3:
        st.metric("Pontos de Dados", info['data_points'])
    
    with col4:
        st.metric("Última Atualização", 
                 pd.to_datetime(info['last_update']).strftime("%d/%m/%Y %H:%M"))