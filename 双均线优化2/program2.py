# 导入必要的库
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端，避免Tkinter错误
import matplotlib.pyplot as plt
import os
import webbrowser
import time
from itertools import product
import akshare as ak

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

class EnhancedDoubleMA:
    def __init__(self):
        self.data = None
        self.results = {}
    
    def get_data(self, start_date='20200101', end_date='20230101'): # 获取贵州茅台股票数据
        """获取股票数据"""
        print("正在加载贵州茅台股票数据...")
        
        try:
            # 尝试使用不同的akshare函数获取贵州茅台(600519)的日K线数据
            print("正在调用akshare API获取贵州茅台数据...") 
            
            # 添加重试机制
            max_retries = 3
            retry_count = 0
            success = False # 用于标记是否成功获取数据
            
            while retry_count < max_retries and not success: # 重试机制
                try:
                    # 尝试使用stock_zh_a_daily函数
                    print(f"尝试使用stock_zh_a_daily函数 (尝试 {retry_count + 1}/{max_retries})...")
                    # 使用前复权数据
                    data = ak.stock_zh_a_daily(symbol='sh600519', start_date=start_date, end_date=end_date, adjust='qfq') # 前复权
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
                        data = ak.stock_zh_a_hist(symbol='600519', period='daily', start_date=start_date, end_date=end_date, adjust='qfq') # 前复权
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
            
            self.data = data
            return data
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
            
            print("使用模拟数据进行分析")
            print(f"数据形状: {data.shape}")
            print(f"数据日期范围: {data.index.min()} 到 {data.index.max()}")
            print(f"数据列: {list(data.columns)}")
            print(f"初始价格: ¥{data['Close'].iloc[0]:.2f}")
            print(f"最终价格: ¥{data['Close'].iloc[-1]:.2f}")
            print(f"价格范围: ¥{data['Close'].min():.2f} - ¥{data['Close'].max():.2f}")
            
            self.data = data
            return data
    
    def calculate_indicators(self, short_window, long_window):
        """计算技术指标"""
        data = self.data.copy() # 复制数据，避免修改原始数据
        
        # 计算移动平均线
        data['Short_MA'] = data['Close'].rolling(window=short_window).mean() # 计算短期移动平均线
        data['Long_MA'] = data['Close'].rolling(window=long_window).mean() # 计算长期移动平均线
        
        # 计算MACD指标
        exp1 = data['Close'].ewm(span=12, adjust=False).mean() # 计算短期指数移动平均线
        exp2 = data['Close'].ewm(span=26, adjust=False).mean() # 计算长期指数移动平均线
        data['MACD'] = exp1 - exp2 # 计算MACD线
        data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean() # 计算信号线
        
        # 计算RSI指标
        delta = data['Close'].diff() # 收盘价相对于前一天的变化量
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean() # 保留正数，负数变0，只关注赚了多少
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean() # 保留负数的绝对值，正数变0，只关注损失了多少
        rs = gain / loss # 计算相对Strength相对强度
        data['RSI'] = 100 - (100 / (1 + rs)) # 比率数值“压缩”到 0 到 100 之间的一个固定范围
        # 计算RSI值，直接反映了多空双方的力量对比
        # 如果 rs > 1，说明平均收益大于平均损失，市场处于多头（买方）强势状态。
        # 如果 rs < 1，说明平均损失大于平均收益，市场处于空头（卖方）强势状态。
        # 如果 rs = 1，说明平均收益和平均损失相等，市场处于平衡状态。
        
        return data
    
    def generate_signals(self, data, short_window, long_window):
        """生成交易信号"""
        # 初始化信号列
        data['Signal'] = 0.0
        
        # 基础双均线信号
        data.loc[data.index[long_window:], 'Signal'] = np.where(
            data.loc[data.index[long_window:], 'Short_MA'] > data.loc[data.index[long_window:], 'Long_MA'], 1.0, 0.0) # 短期移动平均线大于长期移动平均线，生成买入信号
        # 确定“多头”思维，只在趋势向上的时候考虑买入
        
        # 增强信号：结合MACD和RSI
        macd_condition = (data.loc[data.index[long_window:], 'MACD'] > data.loc[data.index[long_window:], 'Signal_Line']) # MACD线大于信号线
        data.loc[data.index[long_window:], 'Signal'] = np.where(
            (data.loc[data.index[long_window:], 'Short_MA'] > data.loc[data.index[long_window:], 'Long_MA']) & macd_condition, 1.0, 0.0) # 短期移动平均线大于长期移动平均线，且MACD线大于信号线，生成买入信号
        # 新增加了一个条件
        
        # 增强信号：RSI过滤
        rsi_condition = (data.loc[data.index[long_window:], 'RSI'] < 70)  # 避免在超买区域买入
        data.loc[data.index[long_window:], 'Signal'] = np.where(
            (data.loc[data.index[long_window:], 'Signal'] == 1.0) & rsi_condition, 1.0, 0.0) # 短期移动平均线大于长期移动平均线，且MACD线大于信号线，且RSI值小于70，生成买入信号
        # 对信号的二次筛选，价格在大幅上涨后已经处于超买状态（RSI>70），此时回调风险很大，RSI过滤器会阻止你在这种高风险区域买入，从而避免追高
        
        # 计算持仓状态
        data['Position'] = data['Signal'].diff() # 计算持仓状态，1.0表示买入，-1.0表示卖出
        
        return data
    
    def backtest(self, data, initial_capital=100000.0, transaction_cost_rate=0.001, stop_loss=0.08, take_profit=0.2): 
        """回测策略"""
        positions = pd.DataFrame(index=data.index).fillna(0.0) 
        portfolio = pd.DataFrame(index=data.index).fillna(0.0) 
        
        cash = initial_capital
        shares = 0
        entry_price = 0
        
        # 找到长均线第一个有效值的索引位置，防御性检查，避免在长均线未形成有效数据时计算持仓状态
        first_valid_idx = data['Long_MA'].first_valid_index() 
        if first_valid_idx is not None:
            first_valid_pos = data.index.get_loc(first_valid_idx)
        else:
            first_valid_pos = 0
        
        for i in range(len(data)):
            if i >= first_valid_pos:
                # 买入信号
                if data['Position'].iloc[i] == 1.0:
                    # 用全部现金买入
                    shares = cash / data['Close'].iloc[i] # 计算购买的股票数量
                    cash = 0
                    entry_price = data['Close'].iloc[i] # 更新入口价格
                # 卖出信号
                elif data['Position'].iloc[i] == -1.0:
                    # 卖出全部股票
                    cash = shares * data['Close'].iloc[i] # 计算卖出股票后的现金
                    shares = 0 # 更新持仓数量
                    entry_price = 0 # 更新入口价格
                # 止损信号
                elif shares > 0 and data['Close'].iloc[i] < entry_price * (1 - stop_loss):
                    # 触发止损
                    cash = shares * data['Close'].iloc[i] # 计算止损后的现金
                    shares = 0 # 更新持仓数量
                    entry_price = 0 # 更新入口价格
                    print(f"触发止损，价格: ¥{data['Close'].iloc[i]:.2f}")
                # 止盈信号
                elif shares > 0 and data['Close'].iloc[i] > entry_price * (1 + take_profit):
                    # 触发止盈
                    cash = shares * data['Close'].iloc[i] # 计算止盈后的现金
                    shares = 0 # 更新持仓数量
                    entry_price = 0 # 更新入口价格
                    print(f"触发止盈，价格: ¥{data['Close'].iloc[i]:.2f}")
            
            # 记录持仓和资产
            positions.loc[data.index[i], 'AAPL'] = shares # 更新持仓数量
            portfolio.loc[data.index[i], 'positions'] = shares * data['Close'].iloc[i] # 更新持仓资产
            portfolio.loc[data.index[i], 'cash'] = cash # 更新现金资产
            portfolio.loc[data.index[i], 'total'] = cash + shares * data['Close'].iloc[i] # 更新总资产
        
        # 计算交易成本
        trades = data['Position'] != 0
        total_trades = trades.sum()
        
        total_cost = 0
        for i in range(len(data)):
            if i >= first_valid_pos and data['Position'].iloc[i] != 0:
                trade_amount = abs(data['Close'].iloc[i] * positions['AAPL'].iloc[i]) # 计算交易金额
                total_cost += trade_amount * transaction_cost_rate # 计算交易成本
        
        # 计算最终资产
        final_value = portfolio['total'].iloc[-1] - total_cost
        
        # 计算绩效指标
        portfolio['returns'] = portfolio['total'].pct_change().fillna(0) # 计算每日收益率=(当前总资产 - 上一日总资产) / 上一日总资产，填充缺失值为0
        sharpe_ratio = np.sqrt(252) * portfolio['returns'].mean() / portfolio['returns'].std() if portfolio['returns'].std() > 0 else 0 # 计算夏普比率=sqrt(252) * 日收益率 / 日标准差，避免除以0
        
        portfolio['cummax'] = portfolio['total'].cummax().ffill() # 计算累计最大值，填充缺失值为前值
        portfolio['drawdown'] = (portfolio['total'] - portfolio['cummax']) / portfolio['cummax'].ffill() # 计算回撤=(当前总资产 - 累计最大值) / 累计最大值，填充缺失值为前值
        max_drawdown = portfolio['drawdown'].min() # 计算最大回撤=回撤的最小值
        
        return {
            'final_value': final_value,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades,
            'total_cost': total_cost,
            'portfolio': portfolio,
            'positions': positions
        }
    
    def optimize_parameters(self, short_windows=[5, 10, 15, 20], long_windows=[20, 30, 40, 50]):
        """优化参数"""
        best_params = None
        best_sharpe = -np.inf
        
        print("正在优化参数...")
        
        for short_window, long_window in product(short_windows, long_windows): # 遍历所有参数组合，自动生成笛卡尔乘积
            if short_window >= long_window:
                continue # 短期均线必须小于长期均线
            
            print(f"测试参数: 短期均线={short_window}, 长期均线={long_window}")
            
            # 计算指标
            data_with_indicators = self.calculate_indicators(short_window, long_window) # 调用计算指标的函数，传入当前的均线参数，计算出均线、MACD、RSI等数据
            
            # 生成信号
            data_with_signals = self.generate_signals(data_with_indicators, short_window, long_window) # 基于刚才算好的指标，生成买入（1）和卖出（0）的信号
            
            # 回测
            result = self.backtest(data_with_signals)  # 调用回测函数，传入信号数据，计算出最终资产、夏普比率、最大回撤等指标
            
            # 记录结果
            self.results[(short_window, long_window)] = result  # 记录当前参数组合的回测结果，存入一个大的字典中，键为(短期均线, 长期均线)
            
            # 更新最佳参数
            if result['sharpe_ratio'] > best_sharpe:
                best_sharpe = result['sharpe_ratio']
                best_params = (short_window, long_window)
                print(f"找到更好的参数: 短期均线={short_window}, 长期均线={long_window}, 夏普比率={best_sharpe:.2f}")
            # 动态比较过程
        
        print(f"最佳参数: 短期均线={best_params[0]}, 长期均线={best_params[1]}, 夏普比率={best_sharpe:.2f}")
        return best_params
    
    def run_best_strategy(self, best_params):
        """运行最佳策略"""
        short_window, long_window = best_params # 从最佳参数中提取短期均线和长期均线
        
        # 计算指标
        data_with_indicators = self.calculate_indicators(short_window, long_window) # 调用计算指标的函数，传入当前的均线参数，计算出均线、MACD、RSI等数据
        
        # 生成信号
        data_with_signals = self.generate_signals(data_with_indicators, short_window, long_window) # 基于刚才算好的指标，生成买入（1）和卖出（0）的信号
        
        # 回测
        result = self.backtest(data_with_signals) # 调用回测函数，传入信号数据，计算出最终资产、夏普比率、最大回撤等指标
        
        # 可视化结果
        self.visualize_results(data_with_signals, result['portfolio'], short_window, long_window)  # 调用可视化函数，传入信号数据和回测结果，绘制股价、均线、MACD、回测曲线等图像
        
        return result
    
    def visualize_results(self, data, portfolio, short_window, long_window):
        """可视化结果"""
        plt.figure(figsize=(14, 12))
        
        # 子图1：股价与均线
        plt.subplot(3, 1, 1)
        plt.plot(data['Close'], label='股价', alpha=0.5)
        plt.plot(data['Short_MA'], label=f'{short_window}日均线', alpha=0.7)
        plt.plot(data['Long_MA'], label=f'{long_window}日均线', alpha=0.7)
        plt.title(f'贵州茅台股价与双均线策略 (短期={short_window}, 长期={long_window})')
        plt.legend()
        
        # 标记买入点 (绿色 ^)
        buy_signals = data[data['Position'] == 1]
        plt.plot(buy_signals.index, buy_signals['Close'],
                 '^', markersize=10, color='g', label='买入信号')
        
        # 标记卖出点 (红色 v)
        sell_signals = data[data['Position'] == -1]
        plt.plot(sell_signals.index, sell_signals['Close'],
                 'v', markersize=10, color='r', label='卖出信号')
        
        # 子图2：MACD
        plt.subplot(3, 1, 2)
        plt.plot(data['MACD'], label='MACD', alpha=0.7)
        plt.plot(data['Signal_Line'], label='Signal Line', alpha=0.7)
        plt.axhline(y=0, color='gray', linestyle='--')
        plt.title('MACD指标')
        plt.legend()
        
        # 子图3：回测曲线
        plt.subplot(3, 1, 3)
        plt.plot(portfolio['total'], label='策略净值')
        plt.title('策略净值曲线')
        plt.legend() # 添加图例，说明策略净值曲线的含义
        
        plt.tight_layout() # 调整子图间距，防止重叠
        
        # 保存图像为文件
        image_path = f'贵州茅台策略回测结果_{short_window}_{long_window}.png'
        plt.savefig(image_path, dpi=100, bbox_inches='tight')
        print(f"图像已保存为: {image_path}")

if __name__ == "__main__": # 主函数，当脚本直接运行时执行
    # 初始化策略
    strategy = EnhancedDoubleMA()
    
    # 获取数据
    strategy.get_data()
    
    # 优化参数
    best_params = strategy.optimize_parameters()
    
    # 运行最佳策略
    result = strategy.run_best_strategy(best_params)
    
    # 打印结果
    print("\n策略回测结果:")
    print(f"最终资产 (扣除成本后): ${result['final_value']:.2f}")
    print(f"夏普比率: {result['sharpe_ratio']:.2f}")
    print(f"最大回撤: {result['max_drawdown']:.2%}")
    print(f"总共进行了 {result['total_trades']} 次交易")
    print(f"预估交易成本: ${result['total_cost']:.2f}")
