import asyncio
import json
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class AlertCondition(Enum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PERCENT_CHANGE_UP = "percent_change_up"
    PERCENT_CHANGE_DOWN = "percent_change_down"
    RSI_OVERBOUGHT = "rsi_overbought"
    RSI_OVERSOLD = "rsi_oversold"

class AlertStatus(Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class AlertService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.alert_key_prefix = "alert:"
        self.user_alerts_prefix = "user_alerts:"
    
    def create_alert(self, user_id: str, alert_data: Dict) -> Optional[Dict]:
        """Cria um novo alerta"""
        try:
            alert_id = f"alert_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            
            alert = {
                "id": alert_id,
                "user_id": user_id,
                "symbol": alert_data['symbol'],
                "condition": alert_data['condition'],
                "value": float(alert_data['value']),
                "name": alert_data.get('name', f"Alerta {alert_data['symbol']}"),
                "status": AlertStatus.ACTIVE.value,
                "created_at": datetime.now().isoformat(),
                "expires_at": alert_data.get('expires_at'),
                "notification_count": 0,
                "last_triggered": None
            }
            
            # Salva no Redis
            alert_key = f"{self.alert_key_prefix}{alert_id}"
            self.redis.set(alert_key, json.dumps(alert))
            
            # Adiciona à lista do usuário
            user_alerts_key = f"{self.user_alerts_prefix}{user_id}"
            self.redis.sadd(user_alerts_key, alert_id)
            
            # Adiciona ao set de símbolos monitorados
            symbol_alerts_key = f"symbol_alerts:{alert_data['symbol']}"
            self.redis.sadd(symbol_alerts_key, alert_id)
            
            logger.info(f"Alerta criado: {alert_id} para {alert_data['symbol']}")
            return alert
            
        except Exception as e:
            logger.error(f"Erro ao criar alerta: {e}")
            return None
    
    def get_user_alerts(self, user_id: str) -> List[Dict]:
        """Recupera todos os alertas do usuário"""
        try:
            user_alerts_key = f"{self.user_alerts_prefix}{user_id}"
            alert_ids = self.redis.smembers(user_alerts_key)
            
            alerts = []
            for alert_id in alert_ids:
                alert_key = f"{self.alert_key_prefix}{alert_id.decode()}"
                alert_data = self.redis.get(alert_key)
                if alert_data:
                    alerts.append(json.loads(alert_data))
            
            return sorted(alerts, key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"Erro ao buscar alertas: {e}")
            return []
    
    def get_alert(self, alert_id: str) -> Optional[Dict]:
        """Recupera um alerta específico pelo ID"""
        try:
            alert_key = f"{self.alert_key_prefix}{alert_id}"
            alert_data = self.redis.get(alert_key)
            if alert_data:
                return json.loads(alert_data)
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar alerta {alert_id}: {e}")
            return None
    
    def update_alert_status(self, alert_id: str, status: AlertStatus, trigger_data: Dict = None) -> bool:
        """Atualiza status do alerta"""
        try:
            alert_key = f"{self.alert_key_prefix}{alert_id}"
            alert_data = self.redis.get(alert_key)
            
            if alert_data:
                alert = json.loads(alert_data)
                alert['status'] = status.value
                
                if status == AlertStatus.TRIGGERED:
                    alert['last_triggered'] = datetime.now().isoformat()
                    alert['notification_count'] += 1
                    if trigger_data:
                        alert['trigger_data'] = trigger_data
                
                self.redis.set(alert_key, json.dumps(alert))
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erro ao atualizar alerta: {e}")
            return False
    
    def delete_alert(self, user_id: str, alert_id: str) -> bool:
        """Remove alerta"""
        try:
            alert_key = f"{self.alert_key_prefix}{alert_id}"
            alert_data = self.redis.get(alert_key)
            
            if alert_data:
                alert = json.loads(alert_data)
                symbol = alert['symbol']
                
                # Remove das listas
                self.redis.delete(alert_key)
                self.redis.srem(f"{self.user_alerts_prefix}{user_id}", alert_id)
                self.redis.srem(f"symbol_alerts:{symbol}", alert_id)
                
                logger.info(f"Alerta deletado: {alert_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erro ao deletar alerta: {e}")
            return False
    
    def check_alerts_for_symbol(self, symbol: str, current_data: Dict) -> List[Dict]:
        """Verifica alertas para um símbolo específico"""
        try:
            symbol_alerts_key = f"symbol_alerts:{symbol}"
            alert_ids = self.redis.smembers(symbol_alerts_key)
            
            triggered_alerts = []
            
            for alert_id in alert_ids:
                alert_id_str = alert_id.decode()
                alert_key = f"{self.alert_key_prefix}{alert_id_str}"
                alert_data = self.redis.get(alert_key)
                
                if alert_data:
                    alert = json.loads(alert_data)
                    
                    if alert['status'] != AlertStatus.ACTIVE.value:
                        continue
                    
                    # Verifica expiração
                    if alert.get('expires_at'):
                        expires = datetime.fromisoformat(alert['expires_at'])
                        if datetime.now() > expires:
                            self.update_alert_status(alert['id'], AlertStatus.EXPIRED)
                            continue
                    
                    # Verifica condições
                    if self._check_alert_condition(alert, current_data):
                        triggered_alerts.append(alert)
                        self.update_alert_status(alert['id'], AlertStatus.TRIGGERED, current_data)
            
            return triggered_alerts
            
        except Exception as e:
            logger.error(f"Erro ao verificar alertas: {e}")
            return []
    
    def _check_alert_condition(self, alert: Dict, current_data: Dict) -> bool:
        """Verifica condição específica do alerta"""
        current_price = current_data.get('price')
        if current_price is None:
            return False
        
        condition = alert['condition']
        threshold = alert['value']
        
        try:
            if condition == AlertCondition.PRICE_ABOVE.value:
                return float(current_price) > threshold
            elif condition == AlertCondition.PRICE_BELOW.value:
                return float(current_price) < threshold
            elif condition == AlertCondition.PERCENT_CHANGE_UP.value:
                change_percent = current_data.get('change_percent')
                if change_percent is not None:
                    return float(change_percent) > threshold
            elif condition == AlertCondition.PERCENT_CHANGE_DOWN.value:
                change_percent = current_data.get('change_percent')
                if change_percent is not None:
                    return float(change_percent) < threshold
            elif condition == AlertCondition.RSI_OVERBOUGHT.value:
                rsi = current_data.get('rsi')
                if rsi is not None:
                    return float(rsi) > threshold
            elif condition == AlertCondition.RSI_OVERSOLD.value:
                rsi = current_data.get('rsi')
                if rsi is not None:
                    return float(rsi) < threshold
        
        except (ValueError, TypeError) as e:
            logger.error(f"Erro ao verificar condição do alerta: {e}")
        
        return False
    
    def get_expired_alerts(self) -> List[Dict]:
        """Recupera alertas expirados"""
        try:
            # Busca todos os alertas ativos e verifica expiração
            expired_alerts = []
            pattern = f"{self.alert_key_prefix}*"
            
            for key in self.redis.scan_iter(match=pattern):
                alert_data = self.redis.get(key)
                if alert_data:
                    alert = json.loads(alert_data)
                    if (alert['status'] == AlertStatus.ACTIVE.value and 
                        alert.get('expires_at')):
                        expires = datetime.fromisoformat(alert['expires_at'])
                        if datetime.now() > expires:
                            expired_alerts.append(alert)
            
            return expired_alerts
            
        except Exception as e:
            logger.error(f"Erro ao buscar alertas expirados: {e}")
            return []
    
    def cleanup_expired_alerts(self) -> int:
        """Limpa alertas expirados e retorna quantidade removida"""
        try:
            expired_alerts = self.get_expired_alerts()
            count = 0
            
            for alert in expired_alerts:
                if self.update_alert_status(alert['id'], AlertStatus.EXPIRED):
                    count += 1
            
            logger.info(f"Limpeza de alertas expirados: {count} alertas atualizados")
            return count
            
        except Exception as e:
            logger.error(f"Erro na limpeza de alertas expirados: {e}")
            return 0

class AlertNotifier:
    def __init__(self, websocket_manager, alert_service: AlertService):
        self.ws_manager = websocket_manager
        self.alert_service = alert_service
    
    async def notify_triggered_alert(self, alert: Dict, current_data: Dict):
        """Notifica usuário sobre alerta acionado"""
        try:
            message = {
                "type": "alert_triggered",
                "alert_id": alert['id'],
                "alert_name": alert['name'],
                "symbol": alert['symbol'],
                "condition": alert['condition'],
                "threshold": alert['value'],
                "current_price": current_data.get('price'),
                "current_change": current_data.get('change_percent'),
                "timestamp": datetime.now().isoformat()
            }
            
            # Envia via WebSocket para o usuário
            user_id = alert['user_id']
            await self.ws_manager.broadcast_to_user(user_id, message)
            
            # Log da notificação
            logger.info(f"Alerta acionado: {alert['name']} para {alert['symbol']}")
            
        except Exception as e:
            logger.error(f"Erro ao notificar alerta: {e}")
    
    async def process_symbol_data(self, symbol: str, market_data: Dict):
        """Processa dados de mercado e verifica alertas"""
        try:
            triggered_alerts = self.alert_service.check_alerts_for_symbol(symbol, market_data)
            
            for alert in triggered_alerts:
                await self.notify_triggered_alert(alert, market_data)
            
            return len(triggered_alerts)
            
        except Exception as e:
            logger.error(f"Erro ao processar dados para {symbol}: {e}")
            return 0

class AlertManager:
    """Manager principal para coordenar o serviço de alertas"""
    
    def __init__(self, redis_client: redis.Redis, websocket_manager = None):
        self.alert_service = AlertService(redis_client)
        self.notifier = AlertNotifier(websocket_manager, self.alert_service)
        self._running = False
    
    async def start(self):
        """Inicia o manager de alertas"""
        self._running = True
        logger.info("Alert Manager iniciado")
        
        # Limpeza inicial de alertas expirados
        self.alert_service.cleanup_expired_alerts()
    
    async def stop(self):
        """Para o manager de alertas"""
        self._running = False
        logger.info("Alert Manager parado")
    
    async def process_market_data(self, symbol: str, market_data: Dict):
        """Processa dados de mercado para verificação de alertas"""
        if not self._running:
            return
        
        try:
            count = await self.notifier.process_symbol_data(symbol, market_data)
            if count > 0:
                logger.debug(f"Processados {count} alertas para {symbol}")
        except Exception as e:
            logger.error(f"Erro ao processar dados de mercado: {e}")
    
    def create_alert(self, user_id: str, alert_data: Dict) -> Optional[Dict]:
        """Cria um novo alerta"""
        return self.alert_service.create_alert(user_id, alert_data)
    
    def get_user_alerts(self, user_id: str) -> List[Dict]:
        """Recupera alertas do usuário"""
        return self.alert_service.get_user_alerts(user_id)
    
    def delete_alert(self, user_id: str, alert_id: str) -> bool:
        """Remove um alerta"""
        return self.alert_service.delete_alert(user_id, alert_id)
    
    async def run_periodic_cleanup(self, interval: int = 3600):
        """Executa limpeza periódica de alertas expirados"""
        while self._running:
            try:
                await asyncio.sleep(interval)
                cleaned_count = self.alert_service.cleanup_expired_alerts()
                if cleaned_count > 0:
                    logger.info(f"Limpeza periódica: {cleaned_count} alertas expirados")
            except Exception as e:
                logger.error(f"Erro na limpeza periódica: {e}")

# Exemplo de uso
if __name__ == "__main__":
    # Configuração básica de logging
    logging.basicConfig(level=logging.INFO)
    
    # Cliente Redis (exemplo)
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    # Cria o alert manager
    alert_manager = AlertManager(redis_client)
    
    # Exemplo de criação de alerta
    alert_data = {
        'symbol': 'BTCUSDT',
        'condition': AlertCondition.PRICE_ABOVE.value,
        'value': 50000.0,
        'name': 'BTC acima de 50k'
    }
    
    # Para usar em produção:
    # asyncio.run(alert_manager.start())