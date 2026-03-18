"""
动量 +RSI 组合策略

核心逻辑:
1. 动量判断方向（5 周期 vs 10 周期）
2. RSI 过滤极端情况
3. 开盘开仓，持有 1 根 K 线
"""

from strategies.base import BaseStrategy, Signal
from typing import Optional, Dict
import numpy as np


class MomentumRSIStrategy(BaseStrategy):
    """动量+RSI 组合策略"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.trend_fast = config.get('trend_fast', 5)  # 快速趋势周期
        self.trend_slow = config.get('trend_slow', 10)  # 慢速趋势周期
        self.rsi_period = config.get('rsi_period', 14)  # RSI 周期
        self.rsi_overbought = config.get('rsi_overbought', 70)  # RSI 超买线
        self.rsi_oversold = config.get('rsi_oversold', 30)  # RSI 超卖线
    
    def calculate_momentum(self, prices: list) -> int:
        """计算动量方向"""
        if len(prices) < self.trend_slow + 1:
            return 0
        
        fast_ma = np.mean(prices[-self.trend_fast:])
        slow_ma = np.mean(prices[-self.trend_slow:])
        
        if fast_ma > slow_ma:
            return 1  # 上涨趋势
        elif fast_ma < slow_ma:
            return -1  # 下跌趋势
        else:
            return 0  # 震荡
    
    def calculate_rsi(self, prices: list) -> float:
        """计算 RSI"""
        if len(prices) < self.rsi_period + 1:
            return 50.0
        
        deltas = np.diff(prices[-self.rsi_period - 1:])
        gains = deltas[deltas > 0]
        losses = -deltas[deltas < 0]
        
        avg_gain = np.mean(gains) if len(gains) > 0 else 0
        avg_loss = np.mean(losses) if len(losses) > 0 else 1
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def generate_signal(self, data: Dict) -> Optional[Signal]:
        """
        生成交易信号
        
        开仓条件:
        1. 动量判断方向
        2. RSI 过滤极端
        3. 开盘开仓（用前一根 K 线数据）
        """
        prices = data.get('close', [])
        
        if len(prices) < self.trend_slow + 2:
            return None
        
        # 使用截至前一根 K 线的数据（避免未来函数）
        momentum = self.calculate_momentum(prices[:-1])
        rsi = self.calculate_rsi(prices[:-1])
        current_price = prices[-2]  # 前一根 K 线的收盘价作为开盘价
        
        # 开仓条件
        if momentum == 1 and rsi < self.rsi_overbought:
            # 上涨趋势且未超买 → 开多
            return Signal(
                timestamp=data.get('timestamp'),
                symbol=data.get('symbol', 'BTCUSDT'),
                direction='UP',
                price=current_price,
                confidence=min(1.0, (self.rsi_overbought - rsi) / 40),
                reason=f'Momentum: {momentum}, RSI: {rsi:.1f}'
            )
        
        elif momentum == -1 and rsi > self.rsi_oversold:
            # 下跌趋势且未超卖 → 开空
            return Signal(
                timestamp=data.get('timestamp'),
                symbol=data.get('symbol', 'BTCUSDT'),
                direction='DOWN',
                price=current_price,
                confidence=min(1.0, (rsi - self.rsi_oversold) / 40),
                reason=f'Momentum: {momentum}, RSI: {rsi:.1f}'
            )
        
        return None
    
    def calculate_position_size(self, signal: Signal, capital: float) -> float:
        """计算仓位大小（固定仓位）"""
        return min(capital * 0.1, 1000)  # 10% 仓位，最大 1000 USDT
