import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

class BacktestInterface:
    def __init__(self):
        self.strategy_types = {
            "sma_crossover": "SMA Crossover",
            "rsi_overbought_oversold": "RSI Overbought/Oversold", 
            "mean_reversion": "Mean Reversion"
        }
    
    def render_backtest_panel(self):
        """Renderiza painel de backtest completo"""
        st.markdown("---")
        st.header("🤖 Backtest de Estratégias")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            self.render_strategy_config()
        
        with col2:
            if st.session_state.get('backtest_results'):
                self.render_backtest_results()
    
    def render_strategy_config(self):
        """Renderiza configuração da estratégia"""
        st.subheader("Configuração da Estratégia")
        
        # Seleção de estratégia
        strategy = st.selectbox(
            "Estratégia",
            options=list(self.strategy_types.keys()),
            format_func=lambda x: self.strategy_types[x]
        )
        
        # Parâmetros comuns
        symbol = st.text_input("Símbolo", value="AAPL")
        initial_capital = st.number_input("Capital Inicial (USD)", 
                                        min_value=1000, value=10000, step=1000)
        
        # Parâmetros específicos por estratégia
        if strategy == "sma_crossover":
            col1, col2 = st.columns(2)
            with col1:
                fast_period = st.number_input("SMA Rápida", min_value=5, value=20)
            with col2:
                slow_period = st.number_input("SMA Lenta", min_value=10, value=50)
            
            strategy_config = {
                "strategy_type": strategy,
                "fast_period": fast_period,
                "slow_period": slow_period,
                "initial_capital": initial_capital
            }
            
        elif strategy == "rsi_overbought_oversold":
            col1, col2 = st.columns(2)
            with col1:
                oversold = st.number_input("Oversold", min_value=10, value=30)
            with col2:
                overbought = st.number_input("Overbought", min_value=50, value=70)
            
            strategy_config = {
                "strategy_type": strategy,
                "oversold": oversold,
                "overbought": overbought,
                "initial_capital": initial_capital
            }
            
        elif strategy == "mean_reversion":
            col1, col2 = st.columns(2)
            with col1:
                window = st.number_input("Janela", min_value=10, value=20)
            with col2:
                num_std = st.number_input("Desvio Padrão", min_value=1, value=2)
            
            strategy_config = {
                "strategy_type": strategy,
                "window": window,
                "num_std": num_std,
                "initial_capital": initial_capital
            }
        
        # Período do backtest
        st.subheader("Período do Teste")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Data Início", 
                                     value=datetime.now() - timedelta(days=365))
        with col2:
            end_date = st.date_input("Data Fim", value=datetime.now())
        
        # Executar backtest
        if st.button("▶️ Executar Backtest", type="primary", use_container_width=True):
            with st.spinner("Executando backtest..."):
                results = self.run_backtest(strategy_config, symbol, start_date, end_date)
                st.session_state.backtest_results = results
        
        # Informações
        with st.expander("ℹ️ Sobre as Estratégias"):
            st.markdown("""
            **SMA Crossover**: Compra quando SMA rápida cruza acima da lenta, venda quando cruza abaixo.
            
            **RSI**: Compra quando RSI < 30 (oversold), venda quando RSI > 70 (overbought).
            
            **Mean Reversion**: Compra quando preço está 2 desvios abaixo da média, venda quando está 2 desvios acima.
            """)
    
    def render_backtest_results(self):
        """Renderiza resultados do backtest"""
        results = st.session_state.backtest_results
        
        if 'error' in results:
            st.error(f"Erro no backtest: {results['error']}")
            return
        
        summary = results['summary']
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Retorno Total", f"{summary['total_return_percent']}%")
        
        with col2:
            st.metric("Capital Final", f"${summary['final_equity']:,.0f}")
        
        with col3:
            st.metric("Max Drawdown", f"{summary['max_drawdown_percent']}%")
        
        with col4:
            st.metric("Sharpe Ratio", f"{summary['sharpe_ratio']:.2f}")
        
        # Gráfico de equity curve
        st.subheader("Curva de Equity")
        if 'equity_curve' in results:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=results['equity_curve'],
                mode='lines',
                name='Equity',
                line=dict(color='#00FF00')
            ))
            
            fig.update_layout(
                template="plotly_dark",
                height=300,
                showlegend=False,
                margin=dict(l=0, r=0, t=0, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Estatísticas de trades
        st.subheader("Estatísticas de Trades")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Trades", summary['total_trades'])
        
        with col2:
            if summary['total_trades'] > 0:
                win_rate = (summary['winning_trades'] / summary['total_trades']) * 100
                st.metric("Win Rate", f"{win_rate:.1f}%")
            else:
                st.metric("Win Rate", "0%")
        
        with col3:
            st.metric("Trades Lucrativos", summary['winning_trades'])
    
    def run_backtest(self, strategy_config, symbol, start_date, end_date):
        """Executa backtest no backend"""
        try:
            # Em produção, fazer requisição POST para o backend
            # backtest_data = {
            #     "strategy_config": strategy_config,
            #     "symbol": symbol,
            #     "start_date": start_date.isoformat(),
            #     "end_date": end_date.isoformat()
            # }
            # response = requests.post(f"{API_BASE_URL}/api/backtest", json=backtest_data)
            # return response.json() if response.status_code == 200 else {"error": "API error"}
            
            # Simulação para demo
            return self.generate_mock_results(strategy_config)
            
        except Exception as e:
            return {"error": str(e)}
    
    def generate_mock_results(self, strategy_config):
        """Gera resultados mock para demonstração"""
        import random
        import numpy as np
        
        # Gera equity curve mock
        initial_capital = strategy_config.get('initial_capital', 10000)
        equity = [initial_capital]
        
        for i in range(100):
            change = random.uniform(-0.02, 0.03)  # -2% to +3%
            new_equity = equity[-1] * (1 + change)
            equity.append(new_equity)
        
        return {
            "summary": {
                "initial_capital": initial_capital,
                "final_equity": equity[-1],
                "total_return_percent": round((equity[-1] - initial_capital) / initial_capital * 100, 2),
                "total_trades": 42,
                "winning_trades": 23,
                "losing_trades": 19,
                "max_drawdown_percent": round(abs(min(equity) - max(equity)) / max(equity) * 100, 2),
                "sharpe_ratio": round(random.uniform(0.5, 2.0), 2),
                "strategy_type": strategy_config['strategy_type']
            },
            "equity_curve": equity,
            "trades": [],
            "signals": []
        }

# Instância global
backtest_interface = BacktestInterface()