import yfinance as yf
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DataService:
    def __init__(self):
        self.available_symbols = {
            # Ações Americanas
            'AAPL': 'Apple Inc.',
            'GOOGL': 'Alphabet Inc. (Google)',
            'MSFT': 'Microsoft Corporation',
            'TSLA': 'Tesla Inc.',
            'AMZN': 'Amazon.com Inc.',
            'META': 'Meta Platforms Inc. (Facebook)',
            'NVDA': 'NVIDIA Corporation',
            'JPM': 'JPMorgan Chase & Co.',
            'JNJ': 'Johnson & Johnson',
            'V': 'Visa Inc.',
            'WMT': 'Walmart Inc.',
            'PG': 'Procter & Gamble Co.',
            'DIS': 'Walt Disney Co.',
            'NFLX': 'Netflix Inc.',
            'BA': 'Boeing Co.',
            
            # Ações Brasileiras
            'PETR4.SA': 'Petrobras PN',
            'VALE3.SA': 'Vale ON',
            'ITUB4.SA': 'Itaú Unibanco PN',
            'BBDC4.SA': 'Bradesco PN',
            'WEGE3.SA': 'Weg ON',
            'MGLU3.SA': 'Magazine Luiza',
            'B3SA3.SA': 'B3 Brasil Bolsa Balcão',
            'ABEV3.SA': 'Ambev ON',
            'RENT3.SA': 'Localiza ON',
            'BBDC3.SA': 'Bradesco ON',
            
            # Criptomoedas
            'BTC-USD': 'Bitcoin USD',
            'ETH-USD': 'Ethereum USD',
            'ADA-USD': 'Cardano USD',
            'DOT-USD': 'Polkadot USD',
            'SOL-USD': 'Solana USD',
            'DOGE-USD': 'Dogecoin USD',
            'XRP-USD': 'Ripple USD',
            'LTC-USD': 'Litecoin USD',
            'BNB-USD': 'Binance Coin USD',
            'MATIC-USD': 'Polygon USD',
            
            # ETFs
            'SPY': 'SPDR S&P 500 ETF',
            'QQQ': 'Invesco QQQ Trust',
            'IVV': 'iShares Core S&P 500 ETF',
            'VTI': 'Vanguard Total Stock Market ETF',
            'GLD': 'SPDR Gold Shares',
            
            # Forex
            'EURUSD=X': 'Euro/US Dollar',
            'GBPUSD=X': 'British Pound/US Dollar',
            'USDJPY=X': 'US Dollar/Japanese Yen',
            'USDBRL=X': 'US Dollar/Brazilian Real',
            'EURBRL=X': 'Euro/Brazilian Real',
            
            # Commodities
            'GC=F': 'Gold Futures',
            'SI=F': 'Silver Futures',
            'CL=F': 'Crude Oil Futures',
            'NG=F': 'Natural Gas Futures',
            'ZC=F': 'Corn Futures'
        }
    
    def get_available_symbols(self):
        """Retorna lista de símbolos disponíveis"""
        return self.available_symbols
    
    def get_historical_data(self, symbol: str, interval: str = "1d", period: str = "6mo"):
        """
        Busca dados históricos do Yahoo Finance
        AGORA SUPORTA PERÍODOS LONGOS: max, 10y, 20y, etc.
        """
        try:
            # Validação do símbolo
            if symbol not in self.available_symbols:
                return {"error": f"Símbolo {symbol} não disponível"}
            
            # PERÍODOS DISPONÍVEIS EXPANDIDOS - NOVO
            valid_periods_long = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "20y", "max"]
            valid_periods_short = ["1d", "5d", "1mo", "3mo", "6mo", "1y"]
            
            # TIMEFRAMES DISPONÍVEIS - EXPANDIDO
            valid_intervals_long = ["1d", "1wk", "1mo", "3mo"]  # Para dados históricos longos
            valid_intervals_short = ["1m", "2m", "5m", "15m", "30m", "1h", "1d"]  # Para dados recentes
            
            # Se período é longo, ajusta intervalo automaticamente se necessário
            if period in ["5y", "10y", "20y", "max"] and interval not in valid_intervals_long:
                interval = "1d"  # Padrão diário para dados longos
                logger.info(f"Ajustando intervalo para '1d' para período longo {period}")
            
            # Para timeframes muito curtos, ajusta período automaticamente
            if interval in ["1m", "2m", "5m", "15m", "30m"]:
                if period not in ["1d", "2d", "5d", "7d"]:
                    period = "5d"  # Período padrão para timeframes curtos
                    logger.info(f"Ajustando período para '5d' para intervalo curto {interval}")
            
            # Download dos dados
            logger.info(f"Buscando dados: {symbol}, intervalo: {interval}, período: {period}")
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                return {"error": f"Nenhum dado encontrado para {symbol} no timeframe {interval}"}
            
            return self._format_chart_data(data, symbol, period)
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados para {symbol}: {e}")
            return {"error": f"Erro interno: {str(e)}"}
    
    def _format_chart_data(self, data: pd.DataFrame, symbol: str, period: str):
        """Formata dados para o formato do TradingView"""
        formatted_data = []
        
        for index, row in data.iterrows():
            # Converte timestamp para formato UNIX
            timestamp = int(index.timestamp()) if hasattr(index, 'timestamp') else int(pd.Timestamp(index).timestamp())
            
            formatted_data.append({
                "time": timestamp,
                "open": round(float(row['Open']), 4),
                "high": round(float(row['High']), 4),
                "low": round(float(row['Low']), 4),
                "close": round(float(row['Close']), 4),
                "volume": int(row['Volume']) if pd.notna(row['Volume']) else 0
            })
        
        # Informações adicionais do símbolo - EXPANDIDO
        info = {
            "symbol": symbol,
            "name": self.available_symbols.get(symbol, "Unknown"),
            "period": period,
            "data_points": len(formatted_data),
            "date_range": {
                "start": data.index[0].strftime("%Y-%m-%d") if not data.empty else "N/A",
                "end": data.index[-1].strftime("%Y-%m-%d") if not data.empty else "N/A"
            },
            "last_update": datetime.now().isoformat()
        }
        
        return {
            "info": info,
            "data": formatted_data
        }
    
    # NOVOS MÉTODOS PARA DADOS HISTÓRICOS LONGOS
    def get_extended_history(self, symbol: str, years: int = 10):
        """Busca dados históricos estendidos por anos específicos"""
        try:
            if years == 1:
                period = "1y"
            elif years == 2:
                period = "2y"
            elif years == 5:
                period = "5y"
            elif years == 10:
                period = "10y"
            elif years == 20:
                period = "20y"
            else:
                period = "max"  # Máximo disponível
            
            logger.info(f"Buscando dados estendidos: {symbol} por {years} anos ({period})")
            return self.get_historical_data(symbol, "1d", period)
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados estendidos: {str(e)}")
            return {"error": f"Erro ao buscar dados estendidos: {str(e)}"}
    
    def get_max_history(self, symbol: str):
        """Busca máximo histórico disponível"""
        try:
            logger.info(f"Buscando máximo histórico para: {symbol}")
            return self.get_historical_data(symbol, "1d", "max")
        except Exception as e:
            return {"error": f"Erro ao buscar máximo histórico: {str(e)}"}
    
    def get_available_periods(self):
        """Retorna períodos disponíveis para dados históricos - NOVO"""
        return {
            "short_term": {
                "name": "Curto Prazo",
                "periods": ["1d", "5d", "1mo", "3mo"],
                "description": "Dados recentes para trading diário"
            },
            "medium_term": {
                "name": "Médio Prazo", 
                "periods": ["6mo", "1y", "2y"],
                "description": "Dados para swing trading"
            },
            "long_term": {
                "name": "Longo Prazo",
                "periods": ["5y", "10y", "20y", "max"],
                "description": "Dados históricos para análise de longo prazo"
            },
            "custom_years": {
                "name": "Anos Personalizados",
                "periods": [1, 2, 5, 10, 20, "max"],
                "description": "Selecione anos específicos"
            }
        }
    
    def get_symbol_info(self, symbol: str):
        """Retorna informações detalhadas do símbolo"""
        try:
            if symbol not in self.available_symbols:
                return {"error": "Símbolo não encontrado"}
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                "symbol": symbol,
                "name": self.available_symbols[symbol],
                "sector": info.get('sector', 'N/A'),
                "industry": info.get('industry', 'N/A'),
                "market_cap": info.get('marketCap', 'N/A'),
                "description": info.get('longBusinessSummary', 'N/A')[:200] + "..." if info.get('longBusinessSummary') else 'N/A'
            }
        except Exception as e:
            return {"error": f"Erro ao buscar informações: {str(e)}"}
    
    def get_historical_data_with_indicators(self, symbol: str, interval: str = "1d", period: str = "6mo", selected_indicators: list = None):
        """Busca dados históricos com indicadores técnicos"""
        try:
            # Busca dados base
            result = self.get_historical_data(symbol, interval, period)
            
            if "error" in result:
                return result
            
            # Para simplificar o teste, vamos retornar os dados sem indicadores por enquanto
            result['indicators'] = {}
            result['indicator_config'] = {
                "moving_averages": {
                    "SMA 20": {"type": "sma", "period": 20, "color": "#2962FF"},
                    "SMA 50": {"type": "sma", "period": 50, "color": "#FF6D00"},
                    "EMA 12": {"type": "ema", "period": 12, "color": "#00C853"},
                    "EMA 26": {"type": "ema", "period": 26, "color": "#AA00FF"}
                },
                "oscillators": {
                    "RSI 14": {"type": "rsi", "period": 14, "color": "#FF4081", "overbought": 70, "oversold": 30},
                    "MACD": {"type": "macd", "fast": 12, "slow": 26, "signal": 9},
                    "Stochastic": {"type": "stochastic", "k_period": 14, "d_period": 3}
                },
                "bands": {
                    "Bollinger Bands": {"type": "bollinger", "period": 20, "std": 2}
                }
            }
            
            return result
            
        except Exception as e:
            return {"error": f"Erro ao calcular indicadores: {str(e)}"}
    
    def get_multiple_timeframes(self, symbol: str):
        """Retorna dados para múltiplos timeframes"""
        timeframes = {
            "1m": {"interval": "1m", "period": "1d"},
            "5m": {"interval": "5m", "period": "5d"},
            "15m": {"interval": "15m", "period": "5d"},
            "30m": {"interval": "30m", "period": "10d"},
            "1h": {"interval": "1h", "period": "1mo"},
            "4h": {"interval": "60m", "period": "3mo"},
            "1d": {"interval": "1d", "period": "6mo"},
            "1w": {"interval": "1wk", "period": "2y"},
            "1M": {"interval": "1mo", "period": "5y"}  # NOVO: mensal com 5 anos
        }
        
        result = {}
        for tf_name, tf_config in timeframes.items():
            result[tf_name] = self.get_historical_data(
                symbol, 
                tf_config["interval"], 
                tf_config["period"]
            )
        
        return result
    
    def search_symbols(self, query: str):
        """Busca símbolos por nome ou código"""
        query = query.upper()
        results = {}
        
        for symbol, name in self.available_symbols.items():
            if query in symbol or query in name.upper():
                results[symbol] = name
        
        return results