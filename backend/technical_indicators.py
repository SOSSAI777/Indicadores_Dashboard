import pandas as pd
import numpy as np
from typing import Dict, List, Optional

class TechnicalIndicators:
    @staticmethod
    def calculate_sma(data: pd.DataFrame, period: int = 20) -> pd.Series:
        """Simple Moving Average"""
        return data['close'].rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(data: pd.DataFrame, period: int = 20) -> pd.Series:
        """Exponential Moving Average"""
        return data['close'].ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """MACD Indicator"""
        ema_fast = data['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = data['close'].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_bollinger_bands(data: pd.DataFrame, period: int = 20, std: int = 2) -> Dict:
        """Bollinger Bands"""
        sma = data['close'].rolling(window=period).mean()
        rolling_std = data['close'].rolling(window=period).std()
        
        upper_band = sma + (rolling_std * std)
        lower_band = sma - (rolling_std * std)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }
    
    @staticmethod
    def calculate_stochastic(data: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict:
        """Stochastic Oscillator"""
        low_min = data['low'].rolling(window=k_period).min()
        high_max = data['high'].rolling(window=k_period).max()
        
        k_line = 100 * ((data['close'] - low_min) / (high_max - low_min))
        d_line = k_line.rolling(window=d_period).mean()
        
        return {
            'k': k_line,
            'd': d_line
        }
    
    def calculate_all_indicators(self, data: pd.DataFrame, symbol: str) -> Dict:
        """Calcula todos os indicadores para um dataset"""
        if data.empty:
            return {}
        
        df = data.copy()
        results = {}
        
        # SMA
        results['sma_20'] = self.calculate_sma(df, 20)
        results['sma_50'] = self.calculate_sma(df, 50)
        
        # EMA
        results['ema_12'] = self.calculate_ema(df, 12)
        results['ema_26'] = self.calculate_ema(df, 26)
        
        # RSI
        results['rsi_14'] = self.calculate_rsi(df, 14)
        
        # MACD
        macd_data = self.calculate_macd(df)
        results.update(macd_data)
        
        # Bollinger Bands
        bb_data = self.calculate_bollinger_bands(df)
        results.update(bb_data)
        
        # Stochastic
        stoch_data = self.calculate_stochastic(df)
        results.update(stoch_data)
        
        # Volume SMA
        results['volume_sma_20'] = df['volume'].rolling(window=20).mean()
        
        return results
    
    def get_indicator_config(self) -> Dict:
        """Retorna configuração dos indicadores"""
        return {
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