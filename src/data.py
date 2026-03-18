"""
数据加载模块 - 从 CSV/JSON 文件加载币安数据

数据格式要求:
CSV 文件包含列：timestamp, open, high, low, close, volume
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class DataLoader:
    """数据加载器"""
    
    def __init__(self, data_dir: str = 'data'):
        """
        初始化数据加载器
        
        Args:
            data_dir: 数据文件目录
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load_csv(self, filename: str) -> pd.DataFrame:
        """
        从 CSV 文件加载数据
        
        Args:
            filename: CSV 文件名
        
        Returns:
            DataFrame 包含 OHLCV 数据
        """
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"数据文件不存在：{filepath}")
        
        df = pd.read_csv(filepath)
        
        # 确保列名正确
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"缺少必需列：{col}")
        
        # 转换时间戳
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # 按时间排序
        df.sort_index(inplace=True)
        
        return df
    
    def load_json(self, filename: str) -> pd.DataFrame:
        """
        从 JSON 文件加载数据
        
        Args:
            filename: JSON 文件名
        
        Returns:
            DataFrame 包含 OHLCV 数据
        """
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"数据文件不存在：{filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 转换为 DataFrame
        df = pd.DataFrame(data)
        
        # 确保列名正确
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"缺少必需列：{col}")
        
        # 转换时间戳
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # 按时间排序
        df.sort_index(inplace=True)
        
        return df
    
    def get_klines(self, symbol: str = 'BTCUSDT', timeframe: str = '5m') -> pd.DataFrame:
        """
        获取指定交易对和周期的 K 线数据
        
        Args:
            symbol: 交易对 (BTCUSDT)
            timeframe: 周期 (5m)
        
        Returns:
            DataFrame 包含 OHLCV 数据
        """
        # 尝试加载数据文件
        filename = f"{symbol}_{timeframe}.csv"
        
        if (self.data_dir / filename).exists():
            return self.load_csv(filename)
        
        # 尝试 JSON 格式
        filename = f"{symbol}_{timeframe}.json"
        if (self.data_dir / filename).exists():
            return self.load_json(filename)
        
        raise FileNotFoundError(
            f"未找到数据文件：{symbol}_{timeframe}.csv 或 .json\n"
            f"请将数据文件放入 {self.data_dir.absolute()} 目录"
        )
    
    def prepare_data(self, df: pd.DataFrame, indicators: List[str] = None) -> Dict:
        """
        准备策略所需数据
        
        Args:
            df: OHLCV DataFrame
            indicators: 需要计算的指标列表
        
        Returns:
            包含价格和指标的字典
        """
        data = {
            'close': df['close'].tolist(),
            'open': df['open'].tolist(),
            'high': df['high'].tolist(),
            'low': df['low'].tolist(),
            'volume': df['volume'].tolist(),
            'timestamps': df.index.tolist()
        }
        
        # 如果需要计算指标，可以在这里添加
        
        return data
    
    def split_data(self, df: pd.DataFrame, train_ratio: float = 0.7) -> tuple:
        """
        分割训练集和测试集
        
        Args:
            df: 原始数据
            train_ratio: 训练集比例
        
        Returns:
            (train_df, test_df)
        """
        split_idx = int(len(df) * train_ratio)
        
        train_df = df.iloc[:split_idx]
        test_df = df.iloc[split_idx:]
        
        return train_df, test_df
