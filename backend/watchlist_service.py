import json
import redis
from typing import Dict, List, Optional
from datetime import datetime

class WatchlistService:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.watchlist_key_prefix = "watchlist:"
    
    def get_user_watchlist(self, user_id: str) -> List[Dict]:
        """Recupera watchlist do usuário"""
        try:
            key = f"{self.watchlist_key_prefix}{user_id}"
            data = self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            else:
                # Watchlist padrão
                default_watchlist = [
                    {"symbol": "AAPL", "name": "Apple Inc.", "added_at": datetime.now().isoformat()},
                    {"symbol": "GOOGL", "name": "Alphabet Inc.", "added_at": datetime.now().isoformat()},
                    {"symbol": "MSFT", "name": "Microsoft", "added_at": datetime.now().isoformat()}
                ]
                self.save_user_watchlist(user_id, default_watchlist)
                return default_watchlist
                
        except Exception as e:
            print(f"Erro ao buscar watchlist: {e}")
            return []
    
    def save_user_watchlist(self, user_id: str, watchlist: List[Dict]) -> bool:
        """Salva watchlist do usuário"""
        try:
            key = f"{self.watchlist_key_prefix}{user_id}"
            self.redis_client.set(key, json.dumps(watchlist))
            return True
        except Exception as e:
            print(f"Erro ao salvar watchlist: {e}")
            return False
    
    def add_to_watchlist(self, user_id: str, symbol: str, name: str) -> bool:
        """Adiciona símbolo à watchlist"""
        watchlist = self.get_user_watchlist(user_id)
        
        # Verifica se já existe
        if any(item['symbol'] == symbol for item in watchlist):
            return False
        
        # Adiciona novo item
        watchlist.append({
            "symbol": symbol,
            "name": name,
            "added_at": datetime.now().isoformat()
        })
        
        return self.save_user_watchlist(user_id, watchlist)
    
    def remove_from_watchlist(self, user_id: str, symbol: str) -> bool:
        """Remove símbolo da watchlist"""
        watchlist = self.get_user_watchlist(user_id)
        
        # Filtra o item a ser removido
        new_watchlist = [item for item in watchlist if item['symbol'] != symbol]
        
        if len(new_watchlist) == len(watchlist):
            return False  # Símbolo não encontrado
        
        return self.save_user_watchlist(user_id, new_watchlist)
    
    def update_watchlist_order(self, user_id: str, new_order: List[str]) -> bool:
        """Atualiza ordem da watchlist"""
        watchlist = self.get_user_watchlist(user_id)
        
        # Reorganiza baseado na nova ordem
        symbol_to_item = {item['symbol']: item for item in watchlist}
        reordered_watchlist = []
        
        for symbol in new_order:
            if symbol in symbol_to_item:
                reordered_watchlist.append(symbol_to_item[symbol])
        
        # Adiciona quaisquer itens que não estejam na nova ordem
        for item in watchlist:
            if item['symbol'] not in new_order:
                reordered_watchlist.append(item)
        
        return self.save_user_watchlist(user_id, reordered_watchlist)

# Instância global
watchlist_service = WatchlistService()