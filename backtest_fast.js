/**
 * 高效回测 - 带进度输出
 */

const fs = require('fs');

const DATA_FILE = 'E:\\Langjie\\data\\BTCUSDT\\5m\\BTCUSDT_5m_2019-01-01.csv';
const OUTPUT_FILE = 'E:\\Langjie\\King\\projects\\quant-btcusdt\\logs\\backtest_result.md';

console.log('🦞 高效回测启动');
console.log(`📊 数据：${DATA_FILE}\n`);

// 快速回测
function fastBacktest() {
  console.log('📂 读取数据...');
  const content = fs.readFileSync(DATA_FILE, 'utf-8');
  const lines = content.trim().split('\n').slice(1);
  console.log(`✅ 数据量：${lines.length.toLocaleString()} 行`);
  
  // 解析数据
  const prices = [];
  const timestamps = [];
  
  console.log('\n📈 解析价格数据...');
  for (let i = 0; i < lines.length; i++) {
    const parts = lines[i].split(',');
    prices.push(parseFloat(parts[4])); // close
    timestamps.push(parts[0]);
    
    if (i % 100000 === 0) {
      process.stdout.write(`\r进度：${((i / lines.length) * 100).toFixed(1)}%`);
    }
  }
  console.log('\r进度：100%          \n');
  
  // 策略参数
  const FAST = 5;
  const SLOW = 10;
  const RSI_PERIOD = 14;
  const RSI_OVERBOUGHT = 70;
  const RSI_OVERSOLD = 30;
  
  console.log('🚀 运行回测...');
  console.log(`策略：动量 (${FAST}/${SLOW}) + RSI (${RSI_PERIOD})\n`);
  
  let trades = 0;
  let wins = 0;
  let position = null;
  
  // 回测循环
  for (let i = SLOW + 2; i < prices.length; i++) {
    // 平仓逻辑（持有 1 根 K 线）
    if (position) {
      const pnl = position.direction === 'UP' 
        ? (prices[i] - position.price) / position.price
        : (position.price - prices[i]) / position.price;
      
      if (pnl > 0) wins++;
      trades++;
      position = null;
      continue;
    }
    
    // 开仓信号
    const fastMA = prices.slice(i - FAST, i).reduce((a, b) => a + b, 0) / FAST;
    const slowMA = prices.slice(i - SLOW, i).reduce((a, b) => a + b, 0) / SLOW;
    
    // RSI 计算（简化版）
    let gains = 0, losses = 0;
    for (let j = i - RSI_PERIOD; j < i; j++) {
      const delta = prices[j] - prices[j - 1];
      if (delta > 0) gains += delta;
      else losses -= delta;
    }
    const rsi = losses === 0 ? 100 : 100 - (100 / (1 + gains / losses));
    
    // 开仓条件
    if (fastMA > slowMA && rsi < RSI_OVERBOUGHT) {
      position = { direction: 'UP', price: prices[i-1], time: timestamps[i-1] };
    } else if (fastMA < slowMA && rsi > RSI_OVERSOLD) {
      position = { direction: 'DOWN', price: prices[i-1], time: timestamps[i-1] };
    }
    
    if (i % 100000 === 0) {
      process.stdout.write(`\r回测进度：${((i / prices.length) * 100).toFixed(1)}% (交易：${trades})`);
    }
  }
  console.log('\r回测进度：100%              \n');
  
  // 统计
  const winRate = trades > 0 ? (wins / trades) : 0;
  const days = (prices.length / 288); // 5 分钟数据，每天 288 根 K 线
  const monthlyOrders = (trades / days) * 30;
  
  console.log('📊 回测结果:\n');
  console.log(`总交易数：${trades}`);
  console.log(`盈利：${wins}`);
  console.log(`亏损：${trades - wins}`);
  console.log(`胜率：${(winRate * 100).toFixed(2)}%`);
  console.log(`回测天数：${days.toFixed(0)} 天 (${(days/365).toFixed(1)} 年)`);
  console.log(`月订单数：${Math.round(monthlyOrders)}`);
  console.log(`\n验收标准:`);
  console.log(`  胜率≥60%: ${winRate >= 0.6 ? '✅' : '❌'} (${(winRate * 100).toFixed(2)}%)`);
  console.log(`  月订单≥150: ${monthlyOrders >= 150 ? '✅' : '❌'} (${Math.round(monthlyOrders)})`);
  
  // 生成报告
  const report = `# 真实回测报告

**数据**: ${lines.length.toLocaleString()} 行 5 分钟 K 线  
**时间**: ${timestamps[0]} 到 ${timestamps[timestamps.length - 1]}  
**策略**: 动量 (${FAST}/${SLOW}) + RSI (${RSI_PERIOD})

## 结果

| 指标 | 值 | 目标 | 状态 |
|------|-----|------|------|
| 胜率 | ${(winRate * 100).toFixed(2)}% | ≥60% | ${winRate >= 0.6 ? '✅' : '❌'} |
| 月订单 | ${Math.round(monthlyOrders)} | ≥150 | ${monthlyOrders >= 150 ? '✅' : '❌'} |
| 总交易 | ${trades} | - | - |
| 回测天数 | ${days.toFixed(0)} | ~2600 | - |

## 结论

${winRate >= 0.6 && monthlyOrders >= 150 ? '✅ 验收通过' : '❌ 需要优化'}
`;
  
  fs.writeFileSync(OUTPUT_FILE, report);
  console.log(`\n📄 报告：${OUTPUT_FILE}`);
  
  return { winRate, monthlyOrders, trades, wins };
}

// 运行
const result = fastBacktest();
console.log('\n###RESULT###', JSON.stringify(result));
