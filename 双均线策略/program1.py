# 导入必要的库
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端，避免Tkinter错误
import matplotlib.pyplot as plt
import os
import tempfile
import akshare as ak
import webbrowser
import time

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 1. 获取数据
# 使用akshare获取贵州茅台的真实历史数据
print("正在加载贵州茅台股票数据...")

try:
    # 尝试使用不同的akshare函数获取贵州茅台(600519)的日K线数据
    print("正在调用akshare API获取贵州茅台数据...")
    
    # 添加重试机制
    max_retries = 3
    retry_count = 0
    success = False # 用于标记是否成功获取数据
    
    while retry_count < max_retries and not success:
        try:
            # 尝试使用stock_zh_a_daily函数
            print(f"尝试使用stock_zh_a_daily函数 (尝试 {retry_count + 1}/{max_retries})...")
            # 使用前复权数据
            data = ak.stock_zh_a_daily(symbol='sh600519', start_date='20200101', end_date='20230101', adjust='qfq') # 前复权
            success = True
        except Exception as e: # 捕获所有异常
            print(f"获取贵州茅台数据时出错: {e}")
            retry_count += 1
            if retry_count < max_retries:
                print(f"等待3秒后重试...")
                time.sleep(3)
    
    if not success:
        # 尝试使用另一个函数
        retry_count = 0
        while retry_count < max_retries and not success: # 重试机制
            try:
                print(f"尝试使用stock_zh_a_hist函数 (尝试 {retry_count + 1}/{max_retries})...")
                data = ak.stock_zh_a_hist(symbol='600519', period='daily', start_date='20200101', end_date='20230101', adjust='qfq') # 前复权
                success = True
            except Exception as e:
                print(f"获取贵州茅台数据时出错: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    print(f"等待3秒后重试...")
                    time.sleep(3)
    
    if not success:
        raise Exception("多次尝试后仍然无法获取贵州茅台数据")
    
    # 打印数据前几行，了解数据结构
    print("akshare返回的数据前5行:")
    print(data.head())
    
    # 检查数据列名
    print(f"akshare返回的列名: {list(data.columns)}") # 打印所有列名，确认是否包含日期列
    
    # 转换日期格式并设置为索引
    if 'date' in data.columns:
        data['date'] = pd.to_datetime(data['date']) 
        data.set_index('date', inplace=True) # 将date列转换为 datetime 类型，并设为索引
    elif 'trade_date' in data.columns:
        data['trade_date'] = pd.to_datetime(data['trade_date'])
        data.set_index('trade_date', inplace=True)
    elif '日期' in data.columns:
        data['日期'] = pd.to_datetime(data['日期'])
        data.set_index('日期', inplace=True)
    else:
        # 直接使用第一列作为日期列
        date_column = data.columns[0]
        print(f"使用{date_column}作为日期列")
        data[date_column] = pd.to_datetime(data[date_column])
        data.set_index(date_column, inplace=True)
    # 数据清洗的核心步骤。智能识别日期列，并将其转换为 datetime 类型，最后设为 DataFrame 的索引（方便按日期查询）
    
    # 重命名列以匹配预期格式
    data.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
        'amount': 'Volume',
        '开盘': 'Open',
        '最高': 'High',
        '最低': 'Low',
        '收盘': 'Close',
        '成交量': 'Volume'
    }, inplace=True) # 统一命名大写格式
    
    # 移除不需要的列
    columns_to_keep = ['Open', 'High', 'Low', 'Close', 'Volume']
    data = data[columns_to_keep] # 只保留策略最核心需要的 OHLCV（开盘、最高、最低、收盘、成交量）数据，去掉其他无关列
    
    # 确保所有必要的列都存在
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required_columns:
        if col not in data.columns:
            print(f"缺少列: {col}，使用模拟数据")
            raise Exception(f"缺少必要的列: {col}")
    # 防御性编程。检查数据是否完整，如果缺少关键列（比如没有收盘价），则直接报错并进入异常处理流程。
    
    # 添加Adj Close列（使用前复权数据）
    # 对于前复权数据，收盘价已经是复权后的价格，所以Adj Close列直接等于Close列
    data['Adj Close'] = data['Close']
    print("使用前复权数据进行分析")
    # 对于A股长期回测，复权很重要。确保价格是和回测时是一致的。
    
    print("贵州茅台真实数据获取成功")
    print(f"数据形状: {data.shape}") # 打印数据形状，确认是否包含所有必要的列
    print(f"数据日期范围: {data.index.min()} 到 {data.index.max()}") # 打印数据日期范围，确认是否包含所有必要的日期
    print(f"数据列: {list(data.columns)}") # 打印所有列名，确认是否包含所有必要的列
    print(f"初始价格: ¥{data['Close'].iloc[0]:.2f}") # 打印初始收盘价，确认是否和预期一致
    print(f"最终价格: ¥{data['Close'].iloc[-1]:.2f}") # 打印最终收盘价，确认是否和预期一致
    print(f"价格范围: ¥{data['Close'].min():.2f} - ¥{data['Close'].max():.2f}") # 打印价格范围，确认是否和预期一致
except Exception as e: # 捕获所有异常
    print(f"获取贵州茅台数据时出错: {e}")
    print("使用模拟数据作为备份")
    # 生成模拟数据作为备份
    dates = pd.date_range('2020-01-01', '2023-01-01', freq='B')
    base_price = 1100.0
    np.random.seed(42) # 固定随机种子，确保模拟数据可重复
    close_prices = base_price + np.cumsum(np.random.randn(len(dates)) * 20) # 生成随机收盘价，模拟真实股票价格趋势
    close_prices = np.maximum(close_prices, 800) # 确保收盘价不低于800，避免价格异常
    data = pd.DataFrame({'Close': close_prices}, index=dates) # 创建DataFrame，包含收盘价列
    data['Open'] = data['Close'] * 0.997 # 模拟开盘价，与收盘价相差0.3%
    data['High'] = data['Close'] * 1.01 # 模拟最高价，与收盘价相差1%
    data['Low'] = data['Close'] * 0.99 # 模拟最低价，与收盘价相差0.3%
    data['Volume'] = np.random.randint(100000, 1000000, len(dates)) # 模拟成交量，确保在合理范围内
    data['Adj Close'] = data['Close'] 

# 2. 计算技术指标 (双均线)
# 短期均线 (如 10日) 和 长期均线 (如 30日)
short_window = 10
long_window = 30

# 使用 pandas 的 rolling 函数计算移动平均线
data['Short_MA'] = data['Close'].rolling(window=short_window).mean() # 计算短期均线，用于判断趋势
data['Long_MA'] = data['Close'].rolling(window=long_window).mean() # 计算长期均线，用于判断趋势

# 3. 生成交易信号
# 当短期均线上穿长期均线时，产生买入信号 (信号为 1)
# 当短期均线下穿长期均线时，产生卖出信号 (信号为 0)
# 我们使用 shift(1) 是为了避免"未来函数"，即今天的信号只能基于昨天的数据生成。

# 初始化信号列
data['Signal'] = 0.0

# 买入信号：昨天短均 < 长均，今天短均 > 长均
# 使用布尔索引来设置信号值
data.loc[data.index[short_window:], 'Signal'] = np.where(
    data.loc[data.index[short_window:], 'Short_MA'] > data.loc[data.index[short_window:], 'Long_MA'], 1.0, 0.0) # 生成交易信号，短期均线上穿长期均线时为1，否则为0

# 持仓状态：信号的变化率 (diff) 不为 0 的地方就是交易点
# 例如：昨天信号为 0，今天信号为 1，那么这就是一个买入点 (diff = 1)
# 例如：昨天信号为 1，今天信号为 0，那么这就是一个卖出点 (diff = -1)
data['Position'] = data['Signal'].diff() # 计算信号的变化率，即持仓状态

# 4. 回测引擎 (模拟交易)
# 假设我们有 100,000 美元初始资金
initial_capital = 100000.0

# 检查data是否为空
if data.empty:
    print("数据为空，无法进行回测")
    exit()

positions = pd.DataFrame(index=data.index).fillna(0.0)  # 记录持仓状态，1表示持仓，-1表示空仓
portfolio = pd.DataFrame(index=data.index).fillna(0.0)  # 记录资产组合，包括持仓股票价值和现金

# 基于信号进行交易
cash = initial_capital  # 初始现金
shares = 0  # 初始股票持仓量

for i in range(len(data)): # 遍历每个时间点
    if i >= short_window: # 确保有足够的历史数据来计算移动平均线
        # 买入信号
        if data['Position'].iloc[i] == 1.0: # 当持仓状态为1时，说明是买入点
            # 用全部现金买入
            shares = cash / data['Close'].iloc[i] # 计算购买的股票数量，确保不会出现小数
            cash = 0 # 现金减少，等于购买股票的总金额
        # 卖出信号
        elif data['Position'].iloc[i] == -1.0: # 当持仓状态为-1时，说明是卖出点
            # 卖出全部股票
            cash = shares * data['Close'].iloc[i] # 计算卖出股票的总金额
            shares = 0 # 股票持仓量减少，等于卖出股票的数量 ，现金增加，等于卖出股票的总金额

    # 记录持仓和资产
    positions.loc[data.index[i], 'AAPL'] = shares # 记录当前时间点的股票持仓量
    portfolio.loc[data.index[i], 'positions'] = shares * data['Close'].iloc[i] # 记录当前时间点的股票价值
    portfolio.loc[data.index[i], 'cash'] = cash # 记录当前时间点的现金
    portfolio.loc[data.index[i], 'total'] = cash + shares * data['Close'].iloc[i] # 记录当前时间点的资产组合价值

# 5. 加入交易成本 (手续费和滑点 - 这是体现专业性的关键！)
# 假设每次交易 (买入或卖出) 的总成本是 0.1% (包括手续费和滑点)
transaction_cost_rate = 0.001 # 交易成本率，0.1%

# 计算交易次数 (只要有开仓或平仓就算一次)
trades = data['Position'] != 0 # 交易信号，当持仓状态发生变化时为True
total_trades = trades.sum() # 计算交易次数，即持仓状态变化的次数

# 计算总手续费 (基于交易金额计算)
total_cost = 0
for i in range(len(data)):
    if i >= short_window and data['Position'].iloc[i] != 0: # 当持仓状态发生变化时，说明是交易点
        trade_amount = abs(data['Close'].iloc[i] * positions['AAPL'].iloc[i]) # 计算交易金额，等于股票价值加上现金
        total_cost += trade_amount * transaction_cost_rate # 计算交易成本，等于交易金额乘以交易成本率

print(f"总共进行了 {total_trades} 次交易，预估交易成本: ${total_cost:.2f}")

# 从最终资产中扣除成本
final_value = portfolio['total'].iloc[-1] - total_cost # 计算最终资产，等于资产组合价值减去交易成本
print(f"最终资产 (扣除成本后): ${final_value:.2f}")

# 6. 绩效分析 (计算夏普比率、最大回撤等)
# 计算日收益率
portfolio['returns'] = portfolio['total'].pct_change() # 计算资产组合价值的日收益率，用于后续绩效分析

# 计算夏普比率 (年化)
# 假设无风险利率为 0，每年 252 个交易日
sharpe_ratio = np.sqrt(252) * portfolio['returns'].mean() / portfolio['returns'].std() # 计算夏普比率，等于资产组合价值的日收益率的年化均值除以资产组合价值的日收益率的年化标准差
print(f"夏普比率: {sharpe_ratio:.2f}")

# 计算最大回撤
portfolio['cummax'] = portfolio['total'].cummax() # 计算资产组合价值的累计最大值，用于计算回撤
portfolio['drawdown'] = (portfolio['total'] - portfolio['cummax']) / portfolio['cummax'] # 计算资产组合价值的回撤，等于当前资产组合价值减去累计最大值，再除以累计最大值
max_drawdown = portfolio['drawdown'].min() # 计算最大回撤，等于所有回撤中的最小值
print(f"最大回撤: {max_drawdown:.2%}")

# 7. 可视化结果
plt.figure(figsize=(14, 8))

# 子图1：股价与均线
plt.subplot(2, 1, 1)
plt.plot(data['Close'], label='股价', alpha=0.5)
plt.plot(data['Short_MA'], label='10日均线', alpha=0.7)
plt.plot(data['Long_MA'], label='30日均线', alpha=0.7)
plt.title('贵州茅台股价与双均线策略')
plt.legend()

# 标记买入点 (绿色 ^)
buy_signals = data[data['Position'] == 1]
plt.plot(buy_signals.index, buy_signals['Close'],
         '^', markersize=10, color='g', label='买入信号')

# 标记卖出点 (红色 v)
sell_signals = data[data['Position'] == -1]
plt.plot(sell_signals.index, sell_signals['Close'],
         'v', markersize=10, color='r', label='卖出信号')

# 子图2：回测曲线
plt.subplot(2, 1, 2)
plt.plot(portfolio['total'], label='策略净值')
plt.title('策略净值曲线')
plt.legend()

plt.tight_layout()
# 保存图像为文件
image_path = '贵州茅台策略回测结果.png'
plt.savefig(image_path, dpi=100, bbox_inches='tight')
print(f"图像已保存为: {image_path}")

# 尝试在浏览器中打开图像
try:
    absolute_path = os.path.abspath(image_path)
    webbrowser.open(f'file://{absolute_path}')
    print("图像已在浏览器中打开")
except Exception as e:
    print(f"无法在浏览器中打开图像: {e}")
    print("您可以在当前目录中手动查看生成的图像文件")