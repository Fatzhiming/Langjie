"""
策略测试
"""

import pytest
from datetime import datetime
from strategies.momentum import MomentumStrategy
from strategies.base import Signal


class TestMomentumStrategy:
    """动量策略测试"""
    
    @pytest.fixture
    def config(self):
        return {
            'lookback_period': 20,
            'threshold': 1.0,
            'rsi_period': 14,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.03
        }
    
    @pytest.fixture
    def strategy(self, config):
        return MomentumStrategy(config)
    
    def test_calculate_momentum(self, strategy):
        """测试动量计算"""
        # 价格上涨 10%
        prices = [100, 102, 104, 106, 108, 110]
        momentum = strategy.calculate_momentum(prices)
        
        assert momentum > 0
        assert abs(momentum - 10.0) < 0.1  # 约 10%
    
    def test_calculate_rsi(self, strategy):
        """测试 RSI 计算"""
        prices = list(range(100, 120))  # 持续上涨
        rsi = strategy.calculate_rsi(prices)
        
        assert 0 <= rsi <= 100
        assert rsi > 50  # 上涨趋势，RSI 应>50
    
    def test_generate_signal_up(self, strategy):
        """测试生成 UP 信号"""
        # 模拟强劲上涨数据
        data = {
            'symbol': 'BTCUSDT',
            'close': list(range(100, 150))  # 持续上涨
        }
        
        signal = strategy.generate_signal(data)
        
        if signal:
            assert signal.direction == 'UP'
            assert 0 <= signal.confidence <= 1
    
    def test_generate_signal_down(self, strategy):
        """测试生成 DOWN 信号"""
        # 模拟强劲下跌数据
        data = {
            'symbol': 'BTCUSDT',
            'close': list(range(150, 100, -1))  # 持续下跌
        }
        
        signal = strategy.generate_signal(data)
        
        if signal:
            assert signal.direction == 'DOWN'
    
    def test_should_enter(self, strategy):
        """测试开仓判断"""
        signal = Signal(
            timestamp=datetime.now(),
            symbol='BTCUSDT',
            direction='UP',
            price=50000,
            confidence=0.8,
            reason='Test'
        )
        
        # 置信度足够，应该开仓
        assert strategy.should_enter(signal) == True
        
        # 置信度不足，不应该开仓
        signal.confidence = 0.3
        assert strategy.should_enter(signal) == False
    
    def test_create_stop_loss(self, strategy):
        """测试止损价格计算"""
        entry_price = 50000
        
        # UP 方向止损
        sl_up = strategy.create_stop_loss(entry_price, 'UP')
        assert sl_up < entry_price
        assert abs(sl_up - entry_price * 0.98) < 1
        
        # DOWN 方向止损
        sl_down = strategy.create_stop_loss(entry_price, 'DOWN')
        assert sl_down > entry_price
        assert abs(sl_down - entry_price * 1.02) < 1
    
    def test_create_take_profit(self, strategy):
        """测试止盈价格计算"""
        entry_price = 50000
        
        # UP 方向止盈
        tp_up = strategy.create_take_profit(entry_price, 'UP')
        assert tp_up > entry_price
        assert abs(tp_up - entry_price * 1.03) < 1
        
        # DOWN 方向止盈
        tp_down = strategy.create_take_profit(entry_price, 'DOWN')
        assert tp_down < entry_price
        assert abs(tp_down - entry_price * 0.97) < 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
