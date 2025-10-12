from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json
import redis
import yfinance as yf
from datetime import datetime
import logging
from typing import Dict, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.user_connections: Dict[str, WebSocket] = {}  # Conexões por usuário
    
    async def connect(self, websocket: WebSocket, client_id: str, symbols: List[str]):
        await websocket.accept()
        
        # Adiciona conexão para cada símbolo
        for symbol in symbols:
            if symbol not in self.active_connections:
                self.active_connections[symbol] = []
            self.active_connections[symbol].append(websocket)
        
        # Registra conexão do usuário
        self.user_connections[client_id] = websocket
        
        logger.info(f"Cliente {client_id} conectado para símbolos: {symbols}")
    
    def disconnect(self, websocket: WebSocket, symbols: List[str]):
        # Remove de todos os símbolos
        for symbol in list(self.active_connections.keys()):
            if websocket in self.active_connections[symbol]:
                self.active_connections[symbol].remove(websocket)
                if not self.active_connections[symbol]:
                    del self.active_connections[symbol]
        
        # Remove conexão do usuário
        for client_id, conn in list(self.user_connections.items()):
            if conn == websocket:
                del self.user_connections[client_id]
                break
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast_to_symbol(self, symbol: str, message: dict):
        if symbol in self.active_connections:
            disconnected = []
            for connection in self.active_connections[symbol]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Erro ao enviar para conexão: {e}")
                    disconnected.append(connection)
            
            # Remove conexões desconectadas
            for connection in disconnected:
                self.active_connections[symbol].remove(connection)
    
    async def broadcast_to_user(self, user_id: str, message: dict):
        """Envia mensagem para um usuário específico"""
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_json(message)
            except Exception as e:
                logger.error(f"Erro ao enviar para usuário {user_id}: {e}")

class RealTimeDataService:
    def __init__(self, websocket_manager: WebSocketManager):
        self.ws_manager = websocket_manager
        self.symbol_cache = {}
        self.price_history = {}  # Histórico de preços para cada símbolo
        self.last_update = {}    # Última atualização por símbolo
        
    async def start_real_time_updates(self):
        """Inicia atualizações em tempo real para todos os símbolos ativos"""
        logger.info("🚀 Iniciando serviço de tempo real...")
        
        while True:
            try:
                active_symbols = list(self.ws_manager.active_connections.keys())
                
                if active_symbols:
                    logger.debug(f"Atualizando {len(active_symbols)} símbolos ativos: {active_symbols}")
                    await self.update_multiple_symbols(active_symbols)
                else:
                    # Sem símbolos ativos, aguarda antes de verificar novamente
                    await asyncio.sleep(10)
                    continue
                
                # Intervalo dinâmico baseado no número de símbolos
                update_interval = max(2, 10 // max(1, len(active_symbols)))
                await asyncio.sleep(update_interval)
                
            except Exception as e:
                logger.error(f"Erro no serviço de tempo real: {e}")
                await asyncio.sleep(10)
    
    async def update_multiple_symbols(self, symbols: List[str]):
        """Atualiza múltiplos símbolos de forma eficiente"""
        tasks = []
        for symbol in symbols:
            # Verifica se precisa atualizar (evita atualizações muito frequentes)
            if self._should_update(symbol):
                task = self.update_symbol_data(symbol)
                tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log de erros individuais
            for symbol, result in zip(symbols, results):
                if isinstance(result, Exception):
                    logger.error(f"Erro ao atualizar {symbol}: {result}")
    
    def _should_update(self, symbol: str) -> bool:
        """Verifica se o símbolo precisa ser atualizado"""
        if symbol not in self.last_update:
            return True
        
        last_update = self.last_update[symbol]
        time_since_update = (datetime.now() - last_update).total_seconds()
        
        # Atualiza mais frequentemente para criptomoedas
        if any(crypto in symbol for crypto in ['BTC', 'ETH', 'ADA', 'SOL', 'XRP']):
            return time_since_update >= 3  # 3 segundos para cripto
        else:
            return time_since_update >= 5  # 5 segundos para outros
    
    async def update_symbol_data(self, symbol: str):
        """Atualiza dados para um símbolo específico com maior precisão"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Busca dados mais recentes com intervalo apropriado
            interval = "1m"  # 1 minuto para maior precisão
            period = "1d"    # Último dia
            
            data = ticker.history(period=period, interval=interval)
            
            if not data.empty:
                latest = data.iloc[-1]
                
                # Calcula variação percentual em relação ao anterior
                if len(data) > 1:
                    previous_close = data.iloc[-2]['Close']
                    change = latest['Close'] - previous_close
                    change_percent = (change / previous_close) * 100
                else:
                    # Se só tem um ponto, usa abertura como referência
                    change = latest['Close'] - latest['Open']
                    change_percent = (change / latest['Open']) * 100
                
                # Calcula variação do dia
                if len(data) > 0:
                    day_open = data.iloc[0]['Open']
                    day_change = latest['Close'] - day_open
                    day_change_percent = (day_change / day_open) * 100
                else:
                    day_change = 0
                    day_change_percent = 0
                
                # Mantém histórico de preços
                if symbol not in self.price_history:
                    self.price_history[symbol] = []
                
                current_time = datetime.now()
                price_point = {
                    'timestamp': current_time.isoformat(),
                    'price': float(latest['Close']),
                    'volume': int(latest['Volume']),
                    'open': float(latest['Open']),
                    'high': float(latest['High']),
                    'low': float(latest['Low'])
                }
                
                self.price_history[symbol].append(price_point)
                
                # Mantém apenas os últimos 100 pontos
                if len(self.price_history[symbol]) > 100:
                    self.price_history[symbol] = self.price_history[symbol][-100:]
                
                # Calcula estatísticas do histórico
                price_trend = self._calculate_price_trend(symbol)
                volume_trend = self._calculate_volume_trend(symbol)
                
                message = {
                    "type": "price_update",
                    "symbol": symbol,
                    "price": round(float(latest['Close']), 4),
                    "open": round(float(latest['Open']), 4),
                    "high": round(float(latest['High']), 4),
                    "low": round(float(latest['Low']), 4),
                    "change": round(float(change), 4),
                    "change_percent": round(float(change_percent), 4),
                    "day_change": round(float(day_change), 4),
                    "day_change_percent": round(float(day_change_percent), 4),
                    "volume": int(latest['Volume']),
                    "timestamp": current_time.isoformat(),
                    "price_history": self.price_history[symbol][-20:],  # Últimos 20 pontos
                    "trend": price_trend,
                    "volume_trend": volume_trend,
                    "update_id": f"{symbol}_{current_time.timestamp()}"
                }
                
                # Envia para todas as conexões interessadas
                await self.ws_manager.broadcast_to_symbol(symbol, message)
                
                # Atualiza cache e timestamp
                self.symbol_cache[symbol] = message
                self.last_update[symbol] = current_time
                
                logger.debug(f"✅ {symbol} atualizado: ${latest['Close']:.4f} ({change_percent:+.2f}%)")
                
            else:
                logger.warning(f"⚠️  Nenhum dado encontrado para {symbol}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar {symbol}: {e}")
    
    def _calculate_price_trend(self, symbol: str) -> str:
        """Calcula tendência de preço baseada no histórico recente"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < 5:
            return "neutral"
        
        prices = [point['price'] for point in self.price_history[symbol][-10:]]  # Últimos 10 pontos
        if len(prices) < 2:
            return "neutral"
        
        # Regressão linear simples para determinar tendência
        x = np.arange(len(prices))
        y = np.array(prices)
        
        try:
            slope = np.polyfit(x, y, 1)[0]
            
            if slope > 0.001:  # Tendência de alta
                return "up"
            elif slope < -0.001:  # Tendência de baixa
                return "down"
            else:
                return "neutral"
        except:
            return "neutral"
    
    def _calculate_volume_trend(self, symbol: str) -> str:
        """Calcula tendência de volume"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < 5:
            return "neutral"
        
        volumes = [point['volume'] for point in self.price_history[symbol][-10:]]
        if len(volumes) < 2:
            return "neutral"
        
        current_volume = volumes[-1]
        avg_volume = np.mean(volumes[:-1])  # Média dos volumes anteriores
        
        if current_volume > avg_volume * 1.5:
            return "high"
        elif current_volume < avg_volume * 0.5:
            return "low"
        else:
            return "normal"
    
    def get_cached_data(self, symbol: str):
        """Retorna dados em cache para um símbolo"""
        return self.symbol_cache.get(symbol)
    
    def get_symbol_statistics(self, symbol: str) -> Dict:
        """Retorna estatísticas detalhadas do símbolo"""
        if symbol not in self.price_history or not self.price_history[symbol]:
            return {}
        
        prices = [point['price'] for point in self.price_history[symbol]]
        volumes = [point['volume'] for point in self.price_history[symbol]]
        
        return {
            "current_price": prices[-1] if prices else 0,
            "price_change_1h": self._calculate_percentage_change(prices, 12),  # ~1 hora em dados de 5min
            "price_change_24h": self._calculate_percentage_change(prices, 288),  # ~24 horas
            "volume_24h": sum(volumes[-288:]) if len(volumes) >= 288 else sum(volumes),
            "high_24h": max(prices[-288:]) if len(prices) >= 288 else max(prices) if prices else 0,
            "low_24h": min(prices[-288:]) if len(prices) >= 288 else min(prices) if prices else 0,
            "volatility": self._calculate_volatility(prices)
        }
    
    def _calculate_percentage_change(self, prices: List[float], periods: int) -> float:
        """Calcula variação percentual em N períodos"""
        if len(prices) < periods + 1:
            return 0.0
        
        old_price = prices[-periods-1]
        current_price = prices[-1]
        
        return ((current_price - old_price) / old_price) * 100
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calcula volatilidade (desvio padrão dos retornos)"""
        if len(prices) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(prices)):
            returns.append((prices[i] - prices[i-1]) / prices[i-1])
        
        return np.std(returns) * 100  # Volatilidade em percentual

# Instâncias globais
websocket_manager = WebSocketManager()
realtime_service = RealTimeDataService(websocket_manager)