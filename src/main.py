"""
主程序 - 量化交易系统入口

功能:
1. 加载配置
2. 初始化策略
3. 运行回测或实盘
4. 记录日志和统计
"""

import yaml
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from strategies.base import BaseStrategy
from strategies.momentum import MomentumStrategy
from .data import DataLoader
from .backtest import Backtest


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TradingSystem:
    """交易系统主类"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        初始化交易系统
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self.load_config(config_path)
        self.strategies: List[BaseStrategy] = []
        self.positions = []
        self.trades = []
        self.capital = self.config['backtest']['initial_capital']
        
        logger.info(f"交易系统初始化完成")
        logger.info(f"初始资金：${self.capital}")
    
    def load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"配置加载完成：{config_path}")
        return config
    
    def initialize_strategies(self):
        """初始化所有策略"""
        strategy_configs = {
            'momentum': MomentumStrategy
        }
        
        active_strategies = self.config['strategy']['active_strategies']
        
        for strategy_name in active_strategies:
            if strategy_name in strategy_configs:
                strategy_config = self.config['strategy'].get(strategy_name, {})
                strategy = strategy_configs[strategy_name](strategy_config)
                self.strategies.append(strategy)
                logger.info(f"策略已加载：{strategy_name}")
    
    def run_backtest(self):
        """运行回测"""
        logger.info("开始回测...")
        
        try:
            # 加载数据
            data_dir = self.config.get('exchange', {}).get('data_dir', 'data')
            data_loader = DataLoader(data_dir if data_dir else 'data')
            symbol = self.config['trading']['symbol']
            timeframe = self.config['trading']['timeframe']
            
            logger.info(f"加载数据：{symbol} {timeframe}")
            logger.info(f"数据源：{data_dir}")
            data = data_loader.get_klines(symbol, timeframe, data_source=data_dir)
            
            # 初始化策略
            strategy_config = self.config['strategy'].get('momentum', {})
            strategy = MomentumStrategy(strategy_config)
            
            # 运行回测
            backtest = Backtest(self.config['backtest'])
            stats = backtest.run(strategy, data)
            
            # 生成报告
            report_path = 'logs/backtest_report.md'
            backtest.generate_report(report_path)
            
            logger.info(f"回测完成")
            logger.info(f"胜率：{stats['win_rate']*100:.2f}%")
            logger.info(f"总收益：{stats['total_return']*100:.2f}%")
            
            return stats
            
        except FileNotFoundError as e:
            logger.warning(f"数据文件未找到：{e}")
            logger.info("请使用示例数据运行回测")
            
            # 返回示例统计
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'total_return': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'message': '请提供数据文件后重新运行'
            }
    
    def run_live(self):
        """运行实盘交易"""
        logger.info("开始实盘交易...")
        
        # TODO: 连接交易所 API
        # TODO: 实时获取数据
        # TODO: 执行交易
        
        logger.info("实盘交易运行中...")
    
    def generate_report(self) -> Dict:
        """生成交易报告"""
        total_trades = len(self.trades)
        winning_trades = sum(1 for t in self.trades if t.get('pnl', 0) > 0)
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        report = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'win_rate': win_rate,
            'total_pnl': sum(t.get('pnl', 0) for t in self.trades),
            'target_win_rate': self.config['trading']['target_win_rate'],
            'target_monthly_orders': self.config['trading']['target_monthly_orders']
        }
        
        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='BTCUSDT 量化交易系统')
    parser.add_argument('--mode', choices=['backtest', 'live'], default='backtest',
                       help='运行模式：backtest 或 live')
    parser.add_argument('--config', default='config.yaml', help='配置文件路径')
    
    args = parser.parse_args()
    
    # 创建交易系统
    system = TradingSystem(args.config)
    system.initialize_strategies()
    
    # 运行
    if args.mode == 'backtest':
        stats = system.run_backtest()
        report = system.generate_report()
        
        print("\n" + "="*50)
        print("交易报告")
        print("="*50)
        print(f"总交易数：{report['total_trades']}")
        print(f"胜率：{report['win_rate']*100:.1f}%")
        print(f"总盈亏：${report['total_pnl']:.2f}")
        print(f"目标胜率：{report['target_win_rate']*100:.0f}%")
        print("="*50)
        
    elif args.mode == 'live':
        system.run_live()


if __name__ == '__main__':
    main()
