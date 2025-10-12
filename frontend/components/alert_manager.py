import streamlit as st
import requests
from datetime import datetime, timedelta
import json

class AlertManager:
    def __init__(self):
        self.user_id = "default_user"
        self.alert_conditions = {
            "price_above": "Preço acima de",
            "price_below": "Preço abaixo de", 
            "percent_change_up": "Variação % acima de",
            "percent_change_down": "Variação % abaixo de"
        }
    
    def render_alert_panel(self, current_symbol=None):
        """Renderiza painel de gerenciamento de alertas"""
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔔 Sistema de Alertas")
        
        # Criar novo alerta
        with st.sidebar.expander("➕ Criar Alerta", expanded=False):
            self.render_alert_creator(current_symbol)
        
        # Lista de alertas ativos
        st.sidebar.subheader("Alertas Ativos")
        self.render_active_alerts()
    
    def render_alert_creator(self, current_symbol=None):
        """Interface para criar novos alertas"""
        symbol = st.text_input("Símbolo", value=current_symbol or "AAPL")
        alert_name = st.text_input("Nome do Alerta", value=f"Alerta {symbol}")
        
        col1, col2 = st.columns(2)
        with col1:
            condition = st.selectbox(
                "Condição",
                options=list(self.alert_conditions.keys()),
                format_func=lambda x: self.alert_conditions[x]
            )
        with col2:
            value = st.number_input("Valor", min_value=0.0, value=100.0, step=0.1)
        
        # Expiração
        expires = st.checkbox("Com expiração")
        if expires:
            exp_days = st.slider("Expira em (dias)", 1, 30, 7)
            expires_at = (datetime.now() + timedelta(days=exp_days)).isoformat()
        else:
            expires_at = None
        
        if st.button("Criar Alerta", type="primary"):
            if self.create_alert(symbol, alert_name, condition, value, expires_at):
                st.success("✅ Alerta criado com sucesso!")
            else:
                st.error("❌ Erro ao criar alerta")
    
    def render_active_alerts(self):
        """Exibe alertas ativos"""
        alerts = self.get_user_alerts()
        
        if not alerts:
            st.sidebar.info("Nenhum alerta ativo")
            return
        
        for alert in alerts[:5]:  # Mostra apenas os 5 mais recentes
            self.render_alert_item(alert)
        
        if len(alerts) > 5:
            if st.sidebar.button("Ver todos os alertas"):
                st.session_state.show_all_alerts = True
        
        if st.session_state.get('show_all_alerts'):
            st.sidebar.markdown("---")
            st.sidebar.subheader("Todos os Alertas")
            for alert in alerts[5:]:
                self.render_alert_item(alert)
            
            if st.sidebar.button("Fechar lista completa"):
                st.session_state.show_all_alerts = False
    
    def render_alert_item(self, alert):
        """Renderiza um item de alerta individual"""
        col1, col2 = st.sidebar.columns([3, 1])
        
        with col1:
            status_color = {
                "active": "🟢",
                "triggered": "🔴", 
                "cancelled": "⚫",
                "expired": "⚫"
            }
            
            st.write(f"{status_color.get(alert['status'], '⚫')} **{alert['name']}**")
            st.caption(f"{alert['symbol']} - {self.alert_conditions[alert['condition']]} {alert['value']}")
            
            if alert['status'] == 'triggered':
                st.error("⚠️ Acionado!")
        
        with col2:
            if st.button("🗑️", key=f"delete_{alert['id']}"):
                if self.delete_alert(alert['id']):
                    st.experimental_rerun()
    
    def create_alert(self, symbol, name, condition, value, expires_at):
        """Cria alerta no backend"""
        try:
            alert_data = {
                "symbol": symbol.upper(),
                "name": name,
                "condition": condition,
                "value": value,
                "expires_at": expires_at
            }
            
            # Em produção, fazer requisição POST
            # response = requests.post(
            #     f"{API_BASE_URL}/api/alerts/{self.user_id}",
            #     json=alert_data
            # )
            # return response.status_code == 200
            
            # Simulação para demo
            st.success(f"Alerta {name} criado para {symbol}")
            return True
            
        except Exception as e:
            st.error(f"Erro: {e}")
            return False
    
    def get_user_alerts(self):
        """Busca alertas do usuário"""
        try:
            # Em produção, fazer requisição GET
            # response = requests.get(f"{API_BASE_URL}/api/alerts/{self.user_id}")
            # return response.json() if response.status_code == 200 else []
            
            # Dados de exemplo
            return [
                {
                    "id": "alert_1",
                    "name": "Alerta AAPL",
                    "symbol": "AAPL",
                    "condition": "price_above",
                    "value": 150.0,
                    "status": "active",
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "alert_2", 
                    "name": "Alerta TSLA",
                    "symbol": "TSLA",
                    "condition": "price_below",
                    "value": 200.0,
                    "status": "triggered",
                    "created_at": datetime.now().isoformat()
                }
            ]
        except:
            return []
    
    def delete_alert(self, alert_id):
        """Remove alerta"""
        try:
            # Em produção, fazer requisição DELETE
            # response = requests.delete(f"{API_BASE_URL}/api/alerts/{self.user_id}/{alert_id}")
            # return response.status_code == 200
            
            # Simulação para demo
            st.success("Alerta removido!")
            return True
        except:
            st.error("Erro ao remover alerta")
            return False

# Instância global
alert_manager = AlertManager()