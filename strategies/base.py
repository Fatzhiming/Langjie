"""
策略基类 - 所有交易策略的父类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict


@dataclass
class Signal:
    """交易信号"""
    timestamp: datetime
    symbol: str
    direction: str  # "UP" or "DOWN"
    price: float
    confidence: float  # 0.0 - 1.0
    reason: str


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    direction: str
    entry_price: float
    entry_time: datetime
    size: float
    hold_period: int = 1  # 持仓 K 线数（默认 1 根）
    hold_count: int = 0   # 已持仓 K 线数
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.name = self.__class__.__name__
        self.signals: List[Signal] = []
        self.positions: List[Position] = []
    
    @abstractmethod
    def generate_signal(self, data: Dict) -> Optional[Signal]:
        """
        根据市场数据生成交易信号
        
        Args:
            data: 市场数据（包含 OHLCV、指标等）
        
        Returns:
            Signal 对象，如果没有信号则返回 None
        """
        pass
    
    @abstractmethod
    def calculate_position_size(self, signal: Signal, capital: float) -> float:
        """
        计算仓位大小
        
        Args:
            signal: 交易信号
            capital: 可用资金
        
        Returns:
            仓位大小 (USDT)
        """
        pass
    
    def should_enter(self, signal: Signal) -> bool:
        """
        判断是否应该开仓
        
        Args:
            signal: 交易信号
        
        Returns:
            True/False
        """
        # 检查信号置信度
        if signal.confidence < self.config.get('min_confidence', 0.6):
            return False
        
        # 检查是否已有同方向持仓
        for pos in self.positions:
            if pos.symbol == signal.symbol and pos.direction == signal.direction:
                return False
        
        return True
    
    def create_position(self, signal: Signal, size: float, hold_period: int = 1) -> Position:
        """
        创建持仓
        
        Args:
            signal: 交易信号
            size: 仓位大小
            hold_period: 持仓 K 线数（默认 1 根）
        
        Returns:
            Position 对象
        """
        return Position(
            symbol=signal.symbol,
            direction=signal.direction,
            entry_price=signal.price,
            entry_time=signal.timestamp,
            size=size,
            hold_period=hold_period,
            hold_count=0
        )
    
    def create_stop_loss(self, entry_price: float, direction: str) -> float:
        """
        创建止损价格
        
        Args:
            entry_price: 入场价格
            direction: 方向 (UP/DOWN)
        
        Returns:
            止损价格
        """
        sl_pct = self.config.get('stop_loss_pct', 0.02)
        
        if direction == 'UP':
            return entry_price * (1 - sl_pct)
        else:
            return entry_price * (1 + sl_pct)
    
    def create_take_profit(self, entry_price: float, direction: str) -> float:
        """
        创建止盈价格
        
        Args:
            entry_price: 入场价格
            direction: 方向 (UP/DOWN)
        
        Returns:
            止盈价格
        """
        tp_pct = self.config.get('take_profit_pct', 0.03)
        
        if direction == 'UP':
            return entry_price * (1 + tp_pct)
        else:
            return entry_price * (1 - tp_pct)
    
    def update_positions(self, current_price: float, current_time: datetime = None) -> List[Dict]:
        """
        更新持仓状态，检查是否需要平仓
        
        Args:
            current_price: 当前价格
            current_time: 当前时间（用于计算持仓时间）
        
        Returns:
            需要平仓的列表
        """
        to_close = []
        
        for pos in self.positions[:]:
            should_close = False
            close_reason = ""
            
            # 增加持仓计数
            pos.hold_count += 1
            
            # 检查持仓时间（固定 N 根 K 线后平仓）
            if pos.hold_count >= pos.hold_period:
                should_close = True
                close_reason = f"TIME_EXIT_{pos.hold_period}K"
            
            # 检查止损（如果设置了）
            if pos.stop_loss and not should_close:
                if pos.direction == 'UP' and current_price <= pos.stop_loss:
                    should_close = True
                    close_reason = "STOP_LOSS"
                elif pos.direction == 'DOWN' and current_price >= pos.stop_loss:
                    should_close = True
                    close_reason = "STOP_LOSS"
            
            # 检查止盈（如果设置了）
            if pos.take_profit and not should_close:
                if pos.direction == 'UP' and current_price >= pos.take_profit:
                    should_close = True
                    close_reason = "TAKE_PROFIT"
                elif pos.direction == 'DOWN' and current_price <= pos.take_profit:
                    should_close = True
                    close_reason = "TAKE_PROFIT"
            
            if should_close:
                to_close.append({
                    'position': pos,
                    'close_price': current_price,
                    'reason': close_reason,
                    'hold_period': pos.hold_period,
                    'hold_count': pos.hold_count
                })
                self.positions.remove(pos)
        
        return to_close
    
    def get_stats(self) -> Dict:
        """获取策略统计信息"""
        return {
            'name': self.name,
            'active_signals': len(self.signals),
            'active_positions': len(self.positions)
        }
