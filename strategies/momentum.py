"""
动量策略 - 基于价格动量进行交易

策略逻辑:
1. 计算过去 N 根 K 线的价格变化率
2. 当动量超过阈值时，跟随动量方向交易
3. 使用 RSI 确认超买超卖状态
"""

from datetime import datetime
from typing import Optional, Dict, List
import numpy as np

from .base import BaseStrategy, Signal, Position


class MomentumStrategy(BaseStrategy):
    """动量策略"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.lookback_period = config.get('lookback_period', 20)
        self.momentum_threshold = config.get('threshold', 1.0)
        self.rsi_period = config.get('rsi_period', 14)
        self.rsi_overbought = config.get('rsi_overbought', 70)
        self.rsi_oversold = config.get('rsi_oversold', 30)
    
    def calculate_momentum(self, prices: List[float]) -> float:
        """
        计算价格动量（变化率）
        
        Args:
            prices: 价格列表（从旧到新）
        
        Returns:
            动量值（百分比）
        """
        if len(prices) < self.lookback_period + 1:
            return 0.0
        
        current_price = prices[-1]
        past_price = prices[-self.lookback_period - 1]
        
        momentum = ((current_price - past_price) / past_price) * 100
        return momentum
    
    def calculate_rsi(self, prices: List[float]) -> float:
        """
        计算 RSI 指标
        
        Args:
            prices: 价格列表
        
        Returns:
            RSI 值 (0-100)
        """
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
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_signal(self, data: Dict) -> Optional[Signal]:
        """
        生成交易信号
        
        逻辑:
        1. 计算动量（使用上一根 K 线及之前的数据）
        2. 计算 RSI
        3. 动量 > 阈值 且 RSI < 70 → UP 信号
        4. 动量 < -阈值 且 RSI > 30 → DOWN 信号
        
        注意：使用 i-1 时刻的数据，避免未来函数
        """
        prices = data.get('close', [])
        
        if len(prices) < self.lookback_period + 1:
            return None
        
        momentum = self.calculate_momentum(prices)
        rsi = self.calculate_rsi(prices)
        
        # 使用上一根 K 线的收盘价作为信号价格（模拟实盘：下一根 K 线开盘开仓）
        signal_price = prices[-1]
        
        # 计算置信度
        confidence = min(abs(momentum) / self.momentum_threshold, 1.0)
        
        # 生成信号
        if momentum > self.momentum_threshold and rsi < self.rsi_overbought:
            # 正向动量，且未超买 → UP
            return Signal(
                timestamp=datetime.now(),
                symbol=data.get('symbol', 'BTCUSDT'),
                direction='UP',
                price=signal_price,
                confidence=confidence,
                reason=f'Momentum: {momentum:.2f}%, RSI: {rsi:.1f}'
            )
        
        elif momentum < -self.momentum_threshold and rsi > self.rsi_oversold:
            # 负向动量，且未超卖 → DOWN
            return Signal(
                timestamp=datetime.now(),
                symbol=data.get('symbol', 'BTCUSDT'),
                direction='DOWN',
                price=signal_price,
                confidence=confidence,
                reason=f'Momentum: {momentum:.2f}%, RSI: {rsi:.1f}'
            )
        
        return None
    
    def calculate_position_size(self, signal: Signal, capital: float) -> float:
        """
        根据信号置信度计算仓位大小
        
        置信度越高，仓位越大
        """
        base_size = capital * 0.1  # 基础仓位 10%
        
        # 根据置信度调整
        size = base_size * signal.confidence
        
        # 限制在合理范围内
        max_size = self.config.get('max_position_size', 1000)
        min_size = self.config.get('min_order_size', 10)
        
        return max(min_size, min(size, max_size))
