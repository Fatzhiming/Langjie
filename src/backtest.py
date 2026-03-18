"""
回测框架 - 完整的回测系统

功能:
1. 加载历史数据
2. 模拟交易执行
3. 计算统计指标
4. 生成回测报告
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from .data import DataLoader
from strategies.base import BaseStrategy, Signal, Position


class Backtest:
    """回测引擎"""
    
    def __init__(self, config: Dict):
        """
        初始化回测引擎
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.initial_capital = config.get('initial_capital', 10000)
        self.capital = self.initial_capital
        self.positions: List[Position] = []
        self.trades = []
        self.equity_curve = []
        
        self.data_loader = DataLoader(config.get('data_dir', 'data'))
    
    def run(self, strategy: BaseStrategy, data: pd.DataFrame) -> Dict:
        """
        运行回测
        
        Args:
            strategy: 策略实例
            data: OHLCV 数据
        
        Returns:
            回测统计结果
        """
        print(f"🚀 开始回测...")
        print(f"初始资金：${self.initial_capital}")
        print(f"数据范围：{data.index[0]} 到 {data.index[-1]}")
        print(f"数据条数：{len(data)}")
        
        # 准备数据
        data_dict = self.data_loader.prepare_data(data)
        
        # 遍历数据
        for i in range(len(data)):
            current_time = data.index[i]
            current_price = data['close'].iloc[i]
            
            # 更新持仓（检查止损止盈）
            closed_positions = strategy.update_positions(current_price)
            for cp in closed_positions:
                self._close_position(cp['position'], cp['close_price'], cp['reason'])
            
            # 生成信号
            # 使用截至当前的数据
            current_data = {
                'close': data_dict['close'][:i+1],
                'symbol': 'BTCUSDT'
            }
            
            signal = strategy.generate_signal(current_data)
            
            # 执行交易
            if signal and strategy.should_enter(signal):
                position_size = strategy.calculate_position_size(signal, self.capital)
                
                if position_size >= self.config.get('min_order_size', 10):
                    position = Position(
                        symbol=signal.symbol,
                        direction=signal.direction,
                        entry_price=signal.price,
                        entry_time=current_time,
                        size=position_size,
                        stop_loss=strategy.create_stop_loss(signal.price, signal.direction),
                        take_profit=strategy.create_take_profit(signal.price, signal.direction)
                    )
                    
                    strategy.positions.append(position)
                    self.capital -= position_size  # 简化：假设全额占用
            
            # 记录权益曲线
            total_value = self.capital + sum(
                self._calculate_position_value(p, current_price) 
                for p in strategy.positions
            )
            self.equity_curve.append({
                'timestamp': current_time,
                'equity': total_value,
                'positions': len(strategy.positions)
            })
        
        # 平仓所有剩余持仓
        final_price = data['close'].iloc[-1]
        for pos in strategy.positions[:]:
            self._close_position(pos, final_price, 'END_OF_BACKTEST')
        
        # 生成统计
        stats = self._calculate_stats()
        
        print(f"\n✅ 回测完成！")
        print(f"最终资金：${self.capital:.2f}")
        print(f"总收益率：{stats['total_return']*100:.2f}%")
        print(f"胜率：{stats['win_rate']*100:.2f}%")
        print(f"夏普比率：{stats['sharpe_ratio']:.2f}")
        print(f"最大回撤：{stats['max_drawdown']*100:.2f}%")
        
        return stats
    
    def _close_position(self, position: Position, close_price: float, reason: str):
        """平仓"""
        pnl = self._calculate_pnl(position, close_price)
        
        trade = {
            'symbol': position.symbol,
            'direction': position.direction,
            'entry_price': position.entry_price,
            'entry_time': position.entry_time,
            'close_price': close_price,
            'close_time': datetime.now(),
            'size': position.size,
            'pnl': pnl,
            'close_reason': reason
        }
        
        self.trades.append(trade)
        self.capital += position.size + pnl  # 返还本金 + 盈亏
    
    def _calculate_pnl(self, position: Position, close_price: float) -> float:
        """计算盈亏"""
        if position.direction == 'UP':
            pnl = (close_price - position.entry_price) / position.entry_price * position.size
        else:
            pnl = (position.entry_price - close_price) / position.entry_price * position.size
        
        # 扣除手续费（假设 0.1%）
        commission = position.size * 0.001 * 2  # 开仓 + 平仓
        return pnl - commission
    
    def _calculate_position_value(self, position: Position, current_price: float) -> float:
        """计算持仓价值"""
        if position.direction == 'UP':
            return position.size * (1 + (current_price - position.entry_price) / position.entry_price)
        else:
            return position.size * (1 + (position.entry_price - current_price) / position.entry_price)
    
    def _calculate_stats(self) -> Dict:
        """计算统计指标"""
        if len(self.trades) == 0:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_return': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0
            }
        
        # 基本统计
        total_trades = len(self.trades)
        winning_trades = sum(1 for t in self.trades if t['pnl'] > 0)
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades
        
        # 盈亏
        total_pnl = sum(t['pnl'] for t in self.trades)
        total_return = total_pnl / self.initial_capital
        
        wins = [t['pnl'] for t in self.trades if t['pnl'] > 0]
        losses = [t['pnl'] for t in self.trades if t['pnl'] < 0]
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = abs(np.mean(losses)) if losses else 0
        
        # 盈亏比
        profit_factor = abs(sum(wins) / sum(losses)) if losses else 0
        
        # 最大回撤
        max_drawdown = self._calculate_max_drawdown()
        
        # 夏普比率
        sharpe_ratio = self._calculate_sharpe_ratio()
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_return': total_return,
            'total_pnl': total_pnl,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'final_capital': self.capital
        }
    
    def _calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        if len(self.equity_curve) < 2:
            return 0.0
        
        equities = [e['equity'] for e in self.equity_curve]
        peak = equities[0]
        max_dd = 0.0
        
        for equity in equities:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd
    
    def _calculate_sharpe_ratio(self) -> float:
        """计算夏普比率"""
        if len(self.equity_curve) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(self.equity_curve)):
            prev_equity = self.equity_curve[i-1]['equity']
            curr_equity = self.equity_curve[i]['equity']
            ret = (curr_equity - prev_equity) / prev_equity
            returns.append(ret)
        
        if len(returns) < 2:
            return 0.0
        
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        # 年化（假设 5 分钟数据，一年约 105120 根 K 线）
        annualization_factor = np.sqrt(105120)
        sharpe = (avg_return / std_return) * annualization_factor
        
        return sharpe
    
    def generate_report(self, save_path: str = None) -> str:
        """生成回测报告"""
        stats = self._calculate_stats()
        
        report = f"""
# 回测报告

## 基本信息
- 初始资金：${self.initial_capital:,.2f}
- 最终资金：${stats['final_capital']:,.2f}
- 数据范围：{self.equity_curve[0]['timestamp']} 到 {self.equity_curve[-1]['timestamp']}

## 性能指标
- 总收益率：{stats['total_return']*100:.2f}%
- 总盈亏：${stats['total_pnl']:.2f}
- 最大回撤：{stats['max_drawdown']*100:.2f}%
- 夏普比率：{stats['sharpe_ratio']:.2f}

## 交易统计
- 总交易数：{stats['total_trades']}
- 盈利交易：{stats['winning_trades']}
- 亏损交易：{stats['losing_trades']}
- 胜率：{stats['win_rate']*100:.2f}%
- 平均盈利：${stats['avg_win']:.2f}
- 平均亏损：${stats['avg_loss']:.2f}
- 盈亏比：{stats['profit_factor']:.2f}

## 验收标准对比
| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 胜率 | ≥60% | {stats['win_rate']*100:.1f}% | {'✅' if stats['win_rate'] >= 0.6 else '❌'} |
| 月订单 | ≥150 | {stats['total_trades']} | {'✅' if stats['total_trades'] >= 150 else '❌'} |
| 最大回撤 | ≤20% | {stats['max_drawdown']*100:.1f}% | {'✅' if stats['max_drawdown'] <= 0.2 else '❌'} |
| 夏普比率 | ≥1.5 | {stats['sharpe_ratio']:.2f} | {'✅' if stats['sharpe_ratio'] >= 1.5 else '❌'} |
"""
        
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 回测报告已保存：{save_path}")
        
        return report
