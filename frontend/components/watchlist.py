import streamlit as st
import requests
from datetime import datetime

class WatchlistManager:
    def __init__(self):
        self.user_id = "default_user"  # Em produção, usar ID real do usuário
    
    def render_watchlist_panel(self):
        """Renderiza o painel da watchlist"""
        st.sidebar.markdown("---")
        st.sidebar.subheader("⭐ Watchlist")
        
        # Busca watchlist
        watchlist = self.get_watchlist()
        
        # Adicionar símbolo
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            new_symbol = st.text_input("Símbolo", placeholder="Ex: TSLA", key="new_symbol")
        with col2:
            if st.button("➕", help="Adicionar à watchlist"):
                if new_symbol:
                    self.add_to_watchlist(new_symbol)
                    st.experimental_rerun()
        
        # Lista de símbolos
        if watchlist:
            for item in watchlist:
                self.render_watchlist_item(item)
        else:
            st.sidebar.info("Adicione símbolos à sua watchlist")
    
    def render_watchlist_item(self, item: dict):
        """Renderiza um item da watchlist"""
        symbol = item['symbol']
        name = item['name']
        
        # Busca dados em tempo real (simulado)
        price_data = self.get_realtime_price(symbol)
        
        col1, col2, col3 = st.sidebar.columns([3, 2, 1])
        
        with col1:
            st.write(f"**{symbol}**")
            st.caption(name[:15] + "..." if len(name) > 15 else name)
        
        with col2:
            if price_data:
                price = price_data.get('price', 'N/A')
                change = price_data.get('change', 0)
                change_color = "green" if change >= 0 else "red"
                
                st.write(f"${price}")
                st.write(f":{change_color}[{change:+.2f}%]")
        
        with col3:
            if st.button("❌", key=f"remove_{symbol}"):
                self.remove_from_watchlist(symbol)
                st.experimental_rerun()
        
        st.sidebar.markdown("---")
    
    def get_watchlist(self) -> list:
        """Busca watchlist do backend"""
        try:
            # Em produção, fazer requisição HTTP
            # response = requests.get(f"{API_BASE_URL}/api/watchlist/{self.user_id}")
            # return response.json() if response.status_code == 200 else []
            
            # Simulação para demo
            return [
                {"symbol": "AAPL", "name": "Apple Inc.", "added_at": datetime.now().isoformat()},
                {"symbol": "GOOGL", "name": "Alphabet Inc.", "added_at": datetime.now().isoformat()},
                {"symbol": "TSLA", "name": "Tesla Inc.", "added_at": datetime.now().isoformat()}
            ]
        except:
            return []
    
    def add_to_watchlist(self, symbol: str):
        """Adiciona símbolo à watchlist"""
        try:
            # Em produção, fazer requisição POST
            # response = requests.post(f"{API_BASE_URL}/api/watchlist/{self.user_id}", 
            #                        json={"symbol": symbol})
            # return response.status_code == 200
            
            # Simulação para demo
            st.success(f"✅ {symbol} adicionado à watchlist!")
            return True
        except:
            st.error(f"❌ Erro ao adicionar {symbol}")
            return False
    
    def remove_from_watchlist(self, symbol: str):
        """Remove símbolo da watchlist"""
        try:
            # Em produção, fazer requisição DELETE
            # response = requests.delete(f"{API_BASE_URL}/api/watchlist/{self.user_id}/{symbol}")
            # return response.status_code == 200
            
            # Simulação para demo
            st.success(f"✅ {symbol} removido da watchlist!")
            return True
        except:
            st.error(f"❌ Erro ao remover {symbol}")
            return False
    
    def get_realtime_price(self, symbol: str) -> dict:
        """Busca preço em tempo real (simulado)"""
        # Em produção, usar WebSocket ou API
        import random
        return {
            "price": round(100 + random.uniform(-10, 10), 2),
            "change": round(random.uniform(-5, 5), 2),
            "volume": random.randint(1000000, 5000000)
        }

# Instância global
watchlist_manager = WatchlistManager()