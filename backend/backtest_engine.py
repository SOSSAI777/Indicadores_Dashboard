import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class StrategyType(Enum):
    SMA_CROSSOVER = "sma_crossover"
    RSI_OVERBOUGHT_OVERSOLD = "rsi_overbought_oversold"
    MEAN_REVERSION = "mean_reversion"

class BacktestEngine:
    def __init__(self):
        self.commission_rate = 0.001  # 0.1% de comissão
    
    def run_backtest(self, strategy_config: Dict, historical_data: pd.DataFrame) -> Dict:
        """Executa backtest baseado na estratégia e dados fornecidos"""
        try:
            strategy_type = strategy_config['strategy_type']
            
            if strategy_type == StrategyType.SMA_CROSSOVER.value:
                return self._sma_crossover_strategy(strategy_config, historical_data)
            elif strategy_type == StrategyType.RSI_OVERBOUGHT_OVERSOLD.value:
                return self._rsi_strategy(strategy_config, historical_data)
            elif strategy_type == StrategyType.MEAN_REVERSION.value:
                return self._mean_reversion_strategy(strategy_config, historical_data)
            else:
                raise ValueError(f"Estratégia não suportada: {strategy_type}")
                
        except Exception as e:
            logger.error(f"Erro no backtest: {e}")
            return {"error": str(e)}
    
    def _sma_crossover_strategy(self, config: Dict, data: pd.DataFrame) -> Dict:
        """Estratégia de crossover de médias móveis"""
        fast_sma = data['close'].rolling(window=config.get('fast_period', 20)).mean()
        slow_sma = data['close'].rolling(window=config.get('slow_period', 50)).mean()
        
        signals = []
        position = 0  # 0: sem posição, 1: comprado, -1: vendido
        trades = []
        equity = [config.get('initial_capital', 10000)]
        
        for i in range(1, len(data)):
            # Gera sinal
            if fast_sma.iloc[i] > slow_sma.iloc[i] and fast_sma.iloc[i-1] <= slow_sma.iloc[i-1]:
                signal = "BUY"
            elif fast_sma.iloc[i] < slow_sma.iloc[i] and fast_sma.iloc[i-1] >= slow_sma.iloc[i-1]:
                signal = "SELL" 
            else:
                signal = "HOLD"
            
            # Executa trades
            if signal == "BUY" and position <= 0:
                if position == -1:
                    # Fecha posição short
                    trades.append({
                        'type': 'BUY',
                        'price': data['close'].iloc[i],
                        'size': 1,
                        'timestamp': data.index[i],
                        'close_trade': True
                    })
                
                # Abre posição long
                trades.append({
                    'type': 'BUY',
                    'price': data['close'].iloc[i],
                    'size': 1,
                    'timestamp': data.index[i],
                    'close_trade': False
                })
                position = 1
                
            elif signal == "SELL" and position >= 0:
                if position == 1:
                    # Fecha posição long
                    trades.append({
                        'type': 'SELL',
                        'price': data['close'].iloc[i],
                        'size': 1,
                        'timestamp': data.index[i],
                        'close_trade': True
                    })
                
                # Abre posição short
                trades.append({
                    'type': 'SELL',
                    'price': data['close'].iloc[i],
                    'size': 1,
                    'timestamp': data.index[i],
                    'close_trade': False
                })
                position = -1
            
            # Calcula equity
            if trades:
                current_equity = self._calculate_equity(equity[-1], trades, data['close'].iloc[i])
                equity.append(current_equity)
            else:
                equity.append(equity[-1])
            
            signals.append({
                'timestamp': data.index[i],
                'signal': signal,
                'fast_sma': fast_sma.iloc[i],
                'slow_sma': slow_sma.iloc[i],
                'price': data['close'].iloc[i]
            })
        
        return self._generate_backtest_results(equity, trades, signals, config)
    
    def _rsi_strategy(self, config: Dict, data: pd.DataFrame) -> Dict:
        """Estratégia baseada em RSI overbought/oversold"""
        # Calcula RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        oversold = config.get('oversold', 30)
        overbought = config.get('overbought', 70)
        
        signals = []
        position = 0
        trades = []
        equity = [config.get('initial_capital', 10000)]
        
        for i in range(1, len(data)):
            if rsi.iloc[i] < oversold and position != 1:
                signal = "BUY"
            elif rsi.iloc[i] > overbought and position != -1:
                signal = "SELL"
            else:
                signal = "HOLD"
            
            # Lógica de trading similar à estratégia SMA
            # ... (implementação similar à anterior)
            
            signals.append({
                'timestamp': data.index[i],
                'signal': signal,
                'rsi': rsi.iloc[i],
                'price': data['close'].iloc[i]
            })
        
        return self._generate_backtest_results(equity, trades, signals, config)
    
    def _mean_reversion_strategy(self, config: Dict, data: pd.DataFrame) -> Dict:
        """Estratégia de mean reversion usando Bollinger Bands"""
        window = config.get('window', 20)
        num_std = config.get('num_std', 2)
        
        sma = data['close'].rolling(window=window).mean()
        std = data['close'].rolling(window=window).std()
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        
        signals = []
        # ... implementação similar às outras estratégias
        
        return self._generate_backtest_results([10000], [], signals, config)
    
    def _calculate_equity(self, initial_equity: float, trades: List[Dict], current_price: float) -> float:
        """Calcula equity atual baseado nos trades e preço atual"""
        # Implementação simplificada
        if not trades:
            return initial_equity
        
        # Calcula P&L baseado na última posição aberta
        last_trade = trades[-1]
        if not last_trade.get('close_trade', False):
            if last_trade['type'] == 'BUY':
                pl = (current_price - last_trade['price']) * last_trade['size']
            else:
                pl = (last_trade['price'] - current_price) * last_trade['size']
            
            return initial_equity + pl
        else:
            return initial_equity
    
    def _generate_backtest_results(self, equity: List[float], trades: List[Dict], 
                                 signals: List[Dict], config: Dict) -> Dict:
        """Gera resultados consolidados do backtest"""
        total_return = (equity[-1] - equity[0]) / equity[0] * 100
        max_drawdown = self._calculate_max_drawdown(equity)
        sharpe_ratio = self._calculate_sharpe_ratio(equity)
        
        return {
            "summary": {
                "initial_capital": equity[0],
                "final_equity": equity[-1],
                "total_return_percent": round(total_return, 2),
                "total_trades": len(trades),
                "winning_trades": len([t for t in trades if t.get('pnl', 0) > 0]),
                "losing_trades": len([t for t in trades if t.get('pnl', 0) < 0]),
                "max_drawdown_percent": round(max_drawdown, 2),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "strategy_type": config['strategy_type']
            },
            "equity_curve": equity,
            "trades": trades[:100],  # Limita para performance
            "signals": signals[:100]  # Limita para performance
        }
    
    def _calculate_max_drawdown(self, equity: List[float]) -> float:
        """Calcula máximo drawdown"""
        peak = equity[0]
        max_dd = 0
        
        for value in equity:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def _calculate_sharpe_ratio(self, equity: List[float]) -> float:
        """Calcula Sharpe ratio simplificado"""
        returns = []
        for i in range(1, len(equity)):
            returns.append((equity[i] - equity[i-1]) / equity[i-1])
        
        if not returns:
            return 0
        
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        return avg_return / std_return * np.sqrt(252) if std_return > 0 else 0

# Instância global
backtest_engine = BacktestEngine()