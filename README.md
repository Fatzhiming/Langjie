# Quant-BTCUSDT - 5 分钟合约策略

**项目目标**:
- 交易对：BTCUSDT
- 周期：5 分钟
- 方向：UP/DOWN 合约
- 目标胜率：60%
- 月订单数：150 个

---

## 项目结构

```
quant-btcusdt/
├── src/                    # 源代码
│   ├── main.py            # 主程序
│   ├── data.py            # 数据获取
│   ├── indicators.py      # 技术指标
│   └── execution.py       # 订单执行
├── strategies/             # 交易策略
│   ├── base.py            # 策略基类
│   ├── momentum.py        # 动量策略
│   └── mean_reversion.py  # 均值回归策略
├── tests/                  # 测试用例
│   ├── test_backtest.py   # 回测测试
│   └── test_strategy.py   # 策略测试
├── logs/                   # 日志目录
├── config.yaml            # 配置文件
├── requirements.txt       # Python 依赖
└── README.md              # 项目说明
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API

编辑 `config.yaml`:
```yaml
exchange:
  api_key: "your_api_key"
  api_secret: "your_api_secret"

trading:
  symbol: "BTCUSDT"
  timeframe: "5m"
  target_win_rate: 0.6
  target_monthly_orders: 150
```

### 3. 运行回测

```bash
python src/main.py --mode backtest
```

### 4. 实盘交易

```bash
python src/main.py --mode live
```

---

## 开发流程

本项目由龙虾工作流自动开发：

1. **司马 (研究员)** - 研究市场数据、技术指标、策略论文
2. **独孤 (开发)** - 编写策略代码、回测框架、执行逻辑
3. **诸葛 (优化)** - 优化策略参数、提升胜率、降低风险
4. **东方 (风控)** - 评估风险、设置止损、资金管理
5. **公孙 (测试)** - 测试代码、验证策略、确保稳定性

每轮循环后自动评估，跑通后固化 Skill 并推送到 GitHub。

---

## 验收标准

- [ ] 回测胜率 ≥ 60%
- [ ] 月订单数 ≥ 150 个
- [ ] 最大回撤 ≤ 20%
- [ ] 夏普比率 ≥ 1.5
- [ ] 代码测试覆盖率 ≥ 80%
- [ ] GitHub 仓库文档完整

---

## 许可证

MIT License
