import streamlit as st
import plotly.graph_objects as go
import plotly.subplots as sp
from typing import List, Dict
import requests

class MultiChartManager:
    def __init__(self):
        self.max_charts = 4
        self.layouts = {
            "1x1": [1, 1],
            "2x1": [2, 1], 
            "1x2": [1, 2],
            "2x2": [2, 2],
            "3x1": [3, 1],
            "1x3": [1, 3]
        }
    
    def render_controls(self):
        """Renderiza controles de múltiplos gráficos"""
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Múltiplos Gráficos")
        
        # Layout selection
        layout = st.sidebar.selectbox(
            "Layout",
            options=list(self.layouts.keys()),
            index=3  # 2x2 como padrão
        )
        
        # Número de gráficos baseado no layout
        rows, cols = self.layouts[layout]
        max_charts = rows * cols
        
        # Configuração de símbolos por gráfico
        chart_configs = []
        for i in range(max_charts):
            with st.sidebar.expander(f"Gráfico {i+1}", expanded=i==0):
                symbol = st.text_input(f"Símbolo {i+1}", value="AAPL" if i==0 else "", key=f"symbol_{i}")
                timeframe = st.selectbox(
                    "Timeframe",
                    ["1m", "5m", "15m", "1h", "4h", "1d"],
                    index=5,
                    key=f"tf_{i}"
                )
                if symbol:
                    chart_configs.append({"symbol": symbol, "timeframe": timeframe})
        
        return layout, chart_configs
    
    def render_multi_charts(self, layout: str, chart_configs: List[Dict]):
        """Renderiza múltiplos gráficos no layout especificado"""
        if not chart_configs:
            st.warning("Configure pelo menos um gráfico na sidebar")
            return
        
        rows, cols = self.layouts[layout]
        
        # Cria subplots
        fig = sp.make_subplots(
            rows=rows, 
            cols=cols,
            subplot_titles=[f"{config['symbol']} - {config['timeframe']}" for config in chart_configs],
            vertical_spacing=0.08,
            horizontal_spacing=0.05
        )
        
        # Adiciona cada gráfico
        for i, config in enumerate(chart_configs):
            if i >= rows * cols:
                break
                
            row = (i // cols) + 1
            col = (i % cols) + 1
            
            # Busca dados
            data = self.fetch_chart_data(config['symbol'], config['timeframe'])
            
            if data and 'data' in data:
                df = self.dataframe_from_chart_data(data)
                
                # Adiciona candlestick
                fig.add_trace(
                    go.Candlestick(
                        x=df['datetime'],
                        open=df['open'],
                        high=df['high'],
                        low=df['low'], 
                        close=df['close'],
                        name=config['symbol'],
                        showlegend=False
                    ),
                    row=row, col=col
                )
        
        # Configura layout
        fig.update_layout(
            height=200 * rows,
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            showlegend=False,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        # Ajusta eixos
        for i in range(1, rows * cols + 1):
            fig.update_xaxes(title_text="", row=(i-1)//cols + 1, col=(i-1)%cols + 1)
            fig.update_yaxes(title_text="Preço", row=(i-1)//cols + 1, col=(i-1)%cols + 1)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def fetch_chart_data(self, symbol: str, timeframe: str):
        """Busca dados para um gráfico individual"""
        try:
            # Mapeia timeframe para period
            period_map = {
                "1m": "1d", "5m": "5d", "15m": "5d",
                "1h": "1mo", "4h": "3mo", "1d": "6mo"
            }
            
            params = {
                "interval": timeframe,
                "period": period_map.get(timeframe, "6mo")
            }
            
            # Em produção, usar API real
            # response = requests.get(f"{API_BASE_URL}/api/chart/{symbol}", params=params)
            # return response.json() if response.status_code == 200 else None
            
            # Simulação - retorna dados mock
            return self.generate_mock_data(symbol, timeframe)
            
        except Exception as e:
            st.error(f"Erro ao buscar dados para {symbol}: {e}")
            return None
    
    def dataframe_from_chart_data(self, data):
        """Converte dados da API para DataFrame"""
        import pandas as pd
        df = pd.DataFrame(data['data'])
        df['datetime'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    def generate_mock_data(self, symbol, timeframe):
        """Gera dados mock para demonstração"""
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        
        # Gera datas
        if timeframe == "1d":
            dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        else:
            dates = pd.date_range(end=datetime.now(), periods=200, freq='H')
        
        # Gera preços mock
        prices = [100]
        for i in range(1, len(dates)):
            change = np.random.normal(0, 2)
            prices.append(max(10, prices[-1] + change))
        
        data = []
        for i, date in enumerate(dates):
            price = prices[i]
            data.append({
                "time": int(date.timestamp()),
                "open": price * (1 + np.random.normal(0, 0.01)),
                "high": price * (1 + abs(np.random.normal(0, 0.02))),
                "low": price * (1 - abs(np.random.normal(0, 0.02))),
                "close": price,
                "volume": np.random.randint(1000000, 5000000)
            })
        
        return {
            "info": {"symbol": symbol, "name": f"Mock {symbol}"},
            "data": data
        }

# Instância global
multi_chart_manager = MultiChartManager()