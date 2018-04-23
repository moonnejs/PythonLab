# encoding: UTF-8

'''
本文件包含了CTA引擎中的双合约策略开发用模板
'''
import copy
import talib
import datetime
import numpy as np
from collections import OrderedDict,defaultdict
from ctaBase import *
from vtObject import *
from vtConstant import *
from tools.peakdetect import *

########################################################################
class CtaTemplate(object):
    """CTA策略模板"""
    
    # 策略类的名称和作者
    author = EMPTY_UNICODE
    className = 'CtaTemplate'
    
    # MongoDB数据库的名称，K线数据库默认为1分钟
    tickDbName = TICK_DB_NAME
    barDbName  = MINUTE_DB_NAME

    productClass = EMPTY_STRING             # 产品类型（只有IB接口需要）
    currency = EMPTY_STRING                 # 货币（只有IB接口需
    
    # 策略的基本参数
    name = EMPTY_UNICODE                    # 策略实例名称
    vtSymbol = EMPTY_STRING                 # 交易的合约vt系统代码    
    symbolList = []                         # 所有需要订阅的合约
    crossSize = {}                          # 盘口撮合量
    
    # 策略的基本变量，由引擎管理
    inited = False                          # 是否进行了初始化
    trading = False                         # 是否启动交易，由引擎管理
    backtesting = False                     # 回测模式
    
    # 策略内部管理的仓位
    pos = defaultdict(int)	            # 总投机方向
    tpos0L = defaultdict(int)	            # 今持多仓
    tpos0S = defaultdict(int)	            # 今持空仓
    ypos0L = defaultdict(int)	            # 昨持多仓
    ypos0S = defaultdict(int)	            # 昨持空仓
    
    # 参数列表，保存了参数的名称
    baseparamList = ['name',
                     'author',
                     'className',
                     'capital',
                     'symbolList',
                     'vtSymbol']
    
    # 变量列表，保存了变量的名称
    basevarList   = ['inited',
                     'trading',
                     'pos']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        self.ctaEngine = ctaEngine

        self.productClass = EMPTY_STRING   # 产品类型（只有IB接口需要）
        self.currency = EMPTY_STRING       # 货币（只有IB接口需

        # 策略的基本变量，由引擎管理
        self.capital = 0                   # 策略使用资金
        self.inited = False                # 是否进行了初始化
        self.trading = False               # 是否启动交易，由引擎管理
        self.backtesting = False           # 回测模式

        self.bar = None                    # K线对象
        self.barMinute = EMPTY_INT         # K线当前的分钟

        self.vtSymbol1 = None              # 第二个合约
        self.orderID   = None              # 上一笔订单
        self.tradeDate = None              # 当前交易日
        
        # 仓位信息
        self.pos = defaultdict(int)	   # 总投机方向
        self.tpos0L = defaultdict(int)	   # 今持多仓
        self.tpos0S = defaultdict(int)	   # 今持空仓
        self.ypos0L = defaultdict(int)	   # 昨持多仓
        self.ypos0S = defaultdict(int)	   # 昨持空仓

        # 定义尾盘，判断是否要进行交易
        self.endOfDay = False
        self.buySig   = False
        self.shortSig = False
        self.coverSig = False
        self.sellSig  = False

        # 默认交易价格
        self.longPrice = EMPTY_FLOAT       # 多头开仓价
        self.shortPrice = EMPTY_FLOAT      # 空头开仓价

        # 默认技术指标列表
        self.am = ArrayManager(size=100)

        # 回测需要
        self.crossSize = {}                # 盘口撮合量
        
        # 参数和状态
        self.varList = self.basevarList+self.varList
        self.paramList = self.baseparamList+self.paramList

        # 设置策略的参数
        self.onUpdate(setting)
        

    #----------------------------------------------------------------------
    def onUpdate(self,setting):
        """刷新策略"""
        # 按输入字典更新
        if setting:
            d = self.__dict__
            for key in self.paramList:
                if key in setting:
                    d[key] = setting[key]

        # 所有需要订阅的合约
        self.symbolList = eval(str(self.symbolList))
        self.symbolList = self.symbolList if self.symbolList != [] else\
                          [str(self.vtSymbol)] if self.vtSymbol1 is None else\
                          [str(self.vtSymbol),str(self.vtSymbol1)]

        self.vtSymbol = str(self.vtSymbol)
        
        # 初始化仓位信息
        for symbol in self.symbolList:
	    self.pos[symbol]    = 0
	    self.ypos0L[symbol] = 0
	    self.tpos0L[symbol] = 0
	    self.ypos0S[symbol] = 0
	    self.tpos0S[symbol] = 0
            self.crossSize[symbol] = 100

    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略初始化' %self.name)
        self.inited = True
        self.putEvent()
    
    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略启动' %self.name)
        self.trading = True
        self.putEvent()
    
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略停止' %self.name)
        self.trading = False
        self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        # 判断交易日更新
        if not self.tradeDate == tick.date:
            self.output(u'当前交易日 ：'+tick.date)
            self.tradeDate = tick.date
            for symbol in self.symbolList:
		self.ypos0L[symbol] += self.tpos0L[symbol]
		self.tpos0L[symbol] = 0
		self.ypos0S[symbol] += self.tpos0S[symbol]
		self.tpos0S[symbol] = 0

    #----------------------------------------------------------------------
    def getCtaIndictor(self):
        """计算指标数据"""
        pass

    #----------------------------------------------------------------------
    def getCtaSignal(self):
        """计算交易信号"""
        pass

    #----------------------------------------------------------------------
    def execSignal(self,volume):
        """简易交易信号执行"""
        pos = self.pos[self.vtSymbol]
        endOfDay = self.endOfDay
        # 挂单未成交
        if not self.orderID is None:
            self.cancelOrder(self.orderID)

        # 当前无仓位
        if pos == 0 and not self.endOfDay:
            # 买开，卖开    
            if self.shortSig:
                self.orderID = self.short(self.shortPrice, volume)
            elif self.buySig:
                self.orderID = self.buy(self.longPrice, volume)

        # 持有多头仓位
        elif pos > 0 and (self.sellSig or self.endOfDay):
                self.orderID = self.sell(self.shortPrice, pos)

        elif pos < 0 and (self.coverSig or self.endOfDay):
                self.orderID = self.cover(self.longPrice, -pos)

    #----------------------------------------------------------------------
    def onOrderCancel(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        if order.orderID == self.orderID:
            self.orderID = None

    #----------------------------------------------------------------------
    def onOrderTrade(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        if order.orderID == self.orderID:
            self.orderID = None

    #----------------------------------------------------------------------
    def onOrder(self, order, log = False):
        """收到委托变化推送（必须由用户继承实现）"""
        if order is None:
            return
        offset = order.offset
        status = order.status
        if status == u'已撤销':
            self.onOrderCancel(order)
        elif status == u'全部成交' or status == u'部成部撤':
            self.onOrderTrade(order)
        if log:
            self.output(' '.join([offset,status]))
            self.output('')

    #----------------------------------------------------------------------
    def onStopOrder(self, order, log = False):
        """收到委托变化推送（必须由用户继承实现）"""
        if order is None:
            return

    #----------------------------------------------------------------------
    def onTrade(self, trade, log=False):
        """收到成交推送（必须由用户继承实现）"""
        if trade is None:
            return
        price     = trade.price
        volume    = trade.volume
        symbol    = trade.vtSymbol
        offset    = trade.offset
        direction = trade.direction 
        if direction == u'多':
	    self.pos[symbol] += volume
            if offset == u'开仓':
	        self.tpos0L[symbol] += volume
            elif offset == u'平今':
	        self.tpos0S[symbol] -= volume
            elif offset == u'平仓' or offset == u'平昨':
	        self.ypos0S[symbol] -= volume
        elif direction == u'空':
	    self.pos[symbol] -= volume
            if offset == u'开仓':
	        self.tpos0S[symbol] += volume
            elif offset == u'平仓' or offset == u'平昨':
	        self.ypos0L[symbol] -= volume
            elif offset == u'平今':
	        self.tpos0L[symbol] -= volume
        if log:
            self.output(trade.tradeTime
	    +u' 合约|' + str(symbol)
	    +u'|{}{}成交|'.format(direction,offset) + str(price)
	    +u'|手数|' + str(volume))
	    self.output(u' ')
    
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        self.bar = bar
        if self.tradeDate != bar.date:
            self.tradeDate = bar.date

        # 记录数据
        if not self.am.updateBar(bar):
            return

        # 计算指标
        self.getCtaIndictor(bar)

        # 计算信号
        self.getCtaSignal(bar)

        # 简易信号执行
        self.execSignal(self.V)

        # 发出状态更新事件
        self.putEvent()
    
    #----------------------------------------------------------------------
    def onXminBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        self.bar = bar
        if self.tradeDate != bar.date:
            self.tradeDate = bar.date

        # 记录数据
        if not self.am.updateBar(bar):
            return

        # 计算指标
        self.getCtaIndictor(bar)

        # 计算信号
        self.getCtaSignal(bar)

        # 简易信号执行
        self.execSignal(self.V)

        # 发出状态更新事件
        self.putEvent()
    
    #----------------------------------------------------------------------
    def sell_y(self, price, volume, symbol='', stop=False):
        """卖平"""
        symbol = self.vtSymbol if symbol == '' else symbol
	return self.sendOrder(CTAORDER_SELL, price, volume, symbol, stop)       

    #----------------------------------------------------------------------
    def sell_t(self, price, volume, symbol='', stop=False):
        """卖平"""
        symbol = self.vtSymbol if symbol == '' else symbol
	return self.sendOrder(CTAORDER_SELL_TODAY, price, volume, symbol, stop)       

    #----------------------------------------------------------------------
    def sell1_y(self, price, volume, symbol='', stop=False):
        """卖平"""
        symbol = self.vtSymbol1 if symbol == '' else symbol
	return self.sendOrder(CTAORDER_SELL, price, volume, symbol, stop)       

    #----------------------------------------------------------------------
    def sell1_t(self, price, volume, symbol='', stop=False):
        """卖平"""
        symbol = self.vtSymbol1 if symbol == '' else symbol
	return self.sendOrder(CTAORDER_SELL_TODAY, price, volume, symbol, stop)       

    #----------------------------------------------------------------------
    def cover1_t(self, price, volume, symbol='', stop=False):
        """卖平"""
        symbol = self.vtSymbol1 if symbol == '' else symbol
	return self.sendOrder(CTAORDER_COVER_TODAY, price, volume, symbol, stop)       

    #----------------------------------------------------------------------
    def buy(self, price, volume, symbol='', stop=False):
        """买开"""
        symbol = self.vtSymbol if symbol == '' else symbol
        return self.sendOrder(CTAORDER_BUY, price, volume, symbol, stop)
    
    #----------------------------------------------------------------------
    def short(self, price, volume, symbol='', stop=False):
        """卖开"""
        symbol = self.vtSymbol if symbol == '' else symbol
        return self.sendOrder(CTAORDER_SHORT, price, volume, symbol, stop)          
 
    #----------------------------------------------------------------------
    def sell(self, price, volume, symbol='', stop=False):
        """卖平"""
        symbol = self.vtSymbol if symbol == '' else symbol
        tpos0L = self.tpos0L.get(symbol)
        ypos0L = self.ypos0L.get(symbol)
	if tpos0L >= volume:
	    return self.sendOrder(CTAORDER_SELL_TODAY, price, volume, symbol, stop)       
	elif ypos0L >= volume:
	    return self.sendOrder(CTAORDER_SELL, price, volume, symbol, stop)       

    #----------------------------------------------------------------------
    def cover(self, price, volume, symbol='', stop=False):
        """买平"""
        symbol = self.vtSymbol if symbol == '' else symbol
        tpos0S = self.tpos0S.get(symbol)
        ypos0S = self.ypos0S.get(symbol)
	if tpos0S >= volume:
	    return self.sendOrder(CTAORDER_COVER_TODAY, price, volume, symbol, stop)       
	elif ypos0S >= volume:
	    return self.sendOrder(CTAORDER_COVER, price, volume, symbol, stop)       

    #----------------------------------------------------------------------
    def buy1(self, price, volume, symbol='', stop=False):
        """买开"""
        symbol = self.vtSymbol1 if symbol == '' else symbol
        return self.sendOrder(CTAORDER_BUY, price, volume, symbol, stop)
    
    #----------------------------------------------------------------------
    def short1(self, price, volume, symbol='', stop=False):
        """卖开"""
        symbol = self.vtSymbol1 if symbol == '' else symbol
        return self.sendOrder(CTAORDER_SHORT, price, volume, symbol, stop)          
 
    #----------------------------------------------------------------------
    def sell1(self, price, volume,symbol='', stop=False):
        """卖平"""
        symbol = self.vtSymbol1 if symbol == '' else symbol
        tpos0L = self.tpos0L.get(symbol)
        ypos0L = self.ypos0L.get(symbol)
	if tpos0L >= volume:
	    return self.sendOrder(CTAORDER_SELL_TODAY, price, volume, symbol, stop)       
	elif ypos0L >= volume:
	    return self.sendOrder(CTAORDER_SELL, price, volume, symbol, stop)       

    #----------------------------------------------------------------------
    def cover1(self, price, volume, symbol='', stop=False):
        """买平"""
        symbol = self.vtSymbol1 if symbol == '' else symbol
        tpos0S = self.tpos0S.get(symbol)
        ypos0S = self.ypos0S.get(symbol)
	if tpos0S >= volume:
	    return self.sendOrder(CTAORDER_COVER_TODAY, price, volume, symbol, stop)       
	elif ypos0S >= volume:
	    return self.sendOrder(CTAORDER_COVER, price, volume, symbol, stop)       

    #----------------------------------------------------------------------
    def cover_y(self, price, volume, symbol='', stop=False):
        """买平"""
        symbol = self.vtSymbol if symbol == '' else symbol
	return self.sendOrder(CTAORDER_COVER, price, volume, symbol, stop)       

    #----------------------------------------------------------------------
    def cover_t(self, price, volume, symbol='', stop=False):
        """买平"""
        symbol = self.vtSymbol if symbol == '' else symbol
	return self.sendOrder(CTAORDER_COVER_TODAY, price, volume, symbol, stop)       

    #----------------------------------------------------------------------
    def buy_fok(self, price, volume, symbol='', stop=False):
        """买开"""
        symbol = self.vtSymbol if symbol == '' else symbol
        return self.sendOrderFOK(CTAORDER_BUY, price, volume, symbol)
    
    #----------------------------------------------------------------------
    def sell_fok(self, price, volume, symbol='', stop=False):
        """卖平"""
        symbol = self.vtSymbol if symbol == '' else symbol
        tpos0L = self.tpos0L.get(symbol)
        ypos0L = self.ypos0L.get(symbol)
	if tpos0L >= volume:
	    return self.sendOrderFOK(CTAORDER_SELL_TODAY, price, volume, symbol)       
	elif ypos0L >= volume:
	    return self.sendOrderFOK(CTAORDER_SELL, price, volume, symbol)       

    #----------------------------------------------------------------------
    def short_fok(self, price, volume, symbol='', stop=False):
        """卖开"""
        symbol = self.vtSymbol if symbol == '' else symbol
        return self.sendOrderFOK(CTAORDER_SHORT, price, volume, symbol)          
 
    #----------------------------------------------------------------------
    def cover_fok(self, price, volume, symbol='', stop=False):
        """买平"""
        symbol = self.vtSymbol if symbol == '' else symbol
        tpos0S = self.tpos0S.get(symbol)
        ypos0S = self.ypos0S.get(symbol)
	if tpos0S >= volume:
	    return self.sendOrderFOK(CTAORDER_COVER_TODAY, price, volume, symbol)       
	elif ypos0S >= volume:
	    return self.sendOrderFOK(CTAORDER_COVER, price, volume, symbol)       

    #----------------------------------------------------------------------
    def buy_fak(self, price, volume, symbol='', stop=False):
        """买开"""
        symbol = self.vtSymbol if symbol == '' else symbol
        return self.sendOrderFAK(CTAORDER_BUY, price, volume, symbol)
    
    #----------------------------------------------------------------------
    def sell_fak(self, price, volume, symbol='', stop=False):
        """卖平"""
        symbol = self.vtSymbol if symbol == '' else symbol
        tpos0L = self.tpos0L.get(symbol)
        ypos0L = self.ypos0L.get(symbol)
	if tpos0L >= volume:
	    return self.sendOrderFAK(CTAORDER_SELL_TODAY, price, volume, symbol)       
	elif ypos0L >= volume:
	    return self.sendOrderFAK(CTAORDER_SELL, price, volume, symbol)       

    #----------------------------------------------------------------------
    def short_fak(self, price, volume, symbol='', stop=False):
        """卖开"""
        symbol = self.vtSymbol if symbol == '' else symbol
        return self.sendOrderFAK(CTAORDER_SHORT, price, volume, symbol)          
 
    #----------------------------------------------------------------------
    def cover_fak(self, price, volume, symbol='', stop=False):
        """买平"""
        symbol = self.vtSymbol if symbol == '' else symbol
        tpos0S = self.tpos0S.get(symbol)
        ypos0S = self.ypos0S.get(symbol)
	if tpos0S >= volume:
	    return self.sendOrderFAK(CTAORDER_COVER_TODAY, price, volume, symbol)       
	elif ypos0S >= volume:
	    return self.sendOrderFAK(CTAORDER_COVER, price, volume, symbol)       

    #----------------------------------------------------------------------
    def sendOrder(self, orderType, price, volume, symbol = '', stop=False):
        """发送委托"""
        if self.trading:
            symbol = self.vtSymbol if symbol=='' else symbol
            if stop:
                vtOrderID = self.ctaEngine.sendStopOrder(symbol, orderType, price, volume, self) 
            else:
                vtOrderID = self.ctaEngine.sendOrder(symbol, orderType, price, volume, self) 
            return vtOrderID
        else:
            return ''        

    #----------------------------------------------------------------------
    def sendOrderFOK(self, orderType, price, volume, symbol=''):
        """发送委托"""
        if self.trading:
            symbol = self.vtSymbol if symbol=='' else symbol
            vtOrderID = self.ctaEngine.sendOrderFOK(symbol, orderType, price, volume, self) 
            return vtOrderID
        else:
            return ''        

    #----------------------------------------------------------------------
    def sendOrderFAK(self, orderType, price, volume, symbol=''):
        """发送委托"""
        if self.trading:
            symbol = self.vtSymbol if symbol=='' else symbol
            vtOrderID = self.ctaEngine.sendOrderFAK(symbol, orderType, price, volume, self) 
            return vtOrderID
        else:
            return ''        

    #----------------------------------------------------------------------
    def cancelOrder(self, vtOrderID):
        """撤单"""
        return self.ctaEngine.cancelOrder(vtOrderID)
    
    #----------------------------------------------------------------------
    def insertTick(self, tick):
        """向数据库中插入tick数据"""
        self.ctaEngine.insertData(self.tickDbName, self.vtSymbol, tick)
    
    #----------------------------------------------------------------------
    def insertBar(self, bar):
        """向数据库中插入bar数据"""
        self.ctaEngine.insertData(self.barDbName, self.vtSymbol, bar)
        
    #----------------------------------------------------------------------
    def loadTick(self, days):
        """读取tick数据"""
        return self.ctaEngine.loadTick(self.tickDbName, self.vtSymbol, days)
    
    #----------------------------------------------------------------------
    def loadBar(self, days):
        """读取bar数据"""
        return self.ctaEngine.loadBar(self.barDbName, self.vtSymbol, days)
    
    #----------------------------------------------------------------------
    def writeCtaLog(self, content):
        """记录CTA日志"""
        content = self.name + ':' + content
        self.ctaEngine.writeCtaLog(content)
        
    #----------------------------------------------------------------------
    def output(self, content):
        """输出信息（必须由用户继承实现）"""
        # 输出信息
        self.ctaEngine.output(content)
    #----------------------------------------------------------------------
    def putEvent(self):
        """发出策略状态变化事件"""
        self.ctaEngine.putStrategyEvent(self.name)

########################################################################
class BarManager(object):
    """
    K线合成器，支持：
    1. 基于Tick合成1分钟K线
    2. 基于1分钟K线合成X分钟K线（X可以是2、3、5、10、15、30、60）
    """

    #----------------------------------------------------------------------
    def __init__(self, onBar, xmin=0, onXminBar=None):
        """Constructor"""
        self.bar = None             # 1分钟K线对象
        self.onBar = onBar          # 1分钟K线回调函数
        
        self.xminBar = None         # X分钟K线对象
        self.xmin = xmin            # X的值
        self.onXminBar = onXminBar  # X分钟K线的回调函数
        
        self.lastTick = None        # 上一TICK缓存对象
        
    #----------------------------------------------------------------------
    def updateTick(self, tick):
        """TICK更新"""
        newMinute = False   # 默认不是新的一分钟
        
        # 尚未创建对象
        if not self.bar:
            self.bar = VtBarData()
            newMinute = True
        # 新的一分钟
        elif self.bar.datetime.minute != tick.datetime.minute or self.bar.datetime.hour != tick.datetime.hour:
            # 生成上一分钟K线的时间戳
            self.bar.datetime = self.bar.datetime.replace(second=0, microsecond=0)  # 将秒和微秒设为0
            self.bar.date = self.bar.datetime.strftime('%Y%m%d')
            self.bar.time = self.bar.datetime.strftime('%H:%M:%S.%f')
            
            # 推送已经结束的上一分钟K线
            self.onBar(self.bar)
            
            # 创建新的K线对象
            self.bar = VtBarData()
            newMinute = True
            
        # 初始化新一分钟的K线数据
        if newMinute:
            self.bar.vtSymbol = tick.vtSymbol
            self.bar.symbol = tick.symbol
            self.bar.exchange = tick.exchange

            self.bar.open = tick.lastPrice
            self.bar.high = tick.lastPrice
            self.bar.low = tick.lastPrice
        # 累加更新老一分钟的K线数据
        else:                                   
            self.bar.high = max(self.bar.high, tick.lastPrice)
            self.bar.low = min(self.bar.low, tick.lastPrice)

        # 通用更新部分
        self.bar.close = tick.lastPrice        
        self.bar.datetime = tick.datetime  
        self.bar.openInterest = tick.openInterest
   
        if self.lastTick:
            self.bar.volume += (tick.volume - self.lastTick.volume) # 当前K线内的成交量
            
        # 缓存Tick
        self.lastTick = tick

    #----------------------------------------------------------------------
    def updateBar(self, bar):
        """1分钟K线更新"""
        # 尚未创建对象
        if not self.xminBar:
            self.xminBar = VtBarData()
            
            self.xminBar.vtSymbol = bar.vtSymbol
            self.xminBar.symbol = bar.symbol
            self.xminBar.exchange = bar.exchange
        
            self.xminBar.open = bar.open
            self.xminBar.high = bar.high
            self.xminBar.low = bar.low            

        # 累加老K线
        else:
            self.xminBar.high = max(self.xminBar.high, bar.high)
            self.xminBar.low = min(self.xminBar.low, bar.low)
    
        # 通用部分
        self.xminBar.close = bar.close
        self.xminBar.datetime = bar.datetime
        self.xminBar.openInterest = bar.openInterest
        self.xminBar.volume += int(bar.volume)                
            
        # X分钟已经走完
        if not (bar.datetime.minute+1) % self.xmin:   # 可以用X整除
            # 生成上一X分钟K线的时间戳
            self.xminBar.datetime = self.xminBar.datetime.replace(second=0, microsecond=0)  # 将秒和微秒设为0
            self.xminBar.date = self.xminBar.datetime.strftime('%Y%m%d')
            self.xminBar.time = self.xminBar.datetime.strftime('%H:%M:%S.%f')
            
            # 推送
            self.onXminBar(self.xminBar)
            
            # 清空老K线缓存对象
            self.xminBar = None


########################################################################
class ArrayManager(object):
    """
    K线序列管理工具，负责：
    1. K线时间序列的维护
    2. 常用技术指标的计算
    """

    #----------------------------------------------------------------------
    def __init__(self, size=100, maxsize=None, bars=None):
        """Constructor"""

        # 一次性载入
        if not bars is None:
            return self.loadBars(bars)
        
        # 实盘分次载入
        self.count = 0                      # 缓存计数
        self.size = size                    # 缓存大小
        self.inited = False                 # True if count>=size

        self.maxsize = size if maxsize is None else maxsize
        
        self.openArray = np.zeros(self.maxsize)     # OHLC
        self.highArray = np.zeros(self.maxsize)
        self.lowArray = np.zeros(self.maxsize)
        self.closeArray = np.zeros(self.maxsize)
        self.volumeArray = np.zeros(self.maxsize)
        
    #----------------------------------------------------------------------
    def loadBars(self, bars):
        """更新K线"""
        self.size        = len(bars)
        self.maxsize     = self.size
        self.openArray   = bars.open
        self.highArray   = bars.high
        self.lowArray    = bars.low        
        self.closeArray  = bars.close
        self.volumeArray = bars.volume

    #----------------------------------------------------------------------
    def updateBar(self, bar):
        """更新K线"""
        self.count += 1
        if not self.inited and self.count >= self.size:
            self.inited = True
        self.openArray[0:self.maxsize-1] = self.openArray[1:self.maxsize]
        self.highArray[0:self.maxsize-1] = self.highArray[1:self.maxsize]
        self.lowArray[0:self.maxsize-1] = self.lowArray[1:self.maxsize]
        self.closeArray[0:self.maxsize-1] = self.closeArray[1:self.maxsize]
        self.volumeArray[0:self.maxsize-1] = self.volumeArray[1:self.maxsize]
    
        self.openArray[-1] = bar.open
        self.highArray[-1] = bar.high
        self.lowArray[-1] = bar.low        
        self.closeArray[-1] = bar.close
        self.volumeArray[-1] = bar.volume
        return self.inited
        
    #----------------------------------------------------------------------
    def updateFactor(self, factor):
        """缓存数据复权"""
        self.openArray = self.openArray*factor
        self.highArray = self.highArray*factor
        self.lowArray = self.lowArray*factor
        self.closeArray = self.closeArray*factor
        
    #----------------------------------------------------------------------
    @property
    def open(self):
        """获取开盘价序列"""
        return self.openArray[-self.size:]
        
    #----------------------------------------------------------------------
    @property
    def high(self):
        """获取最高价序列"""
        return self.highArray[-self.size:]
    
    #----------------------------------------------------------------------
    @property
    def low(self):
        """获取最低价序列"""
        return self.lowArray[-self.size:]
    
    #----------------------------------------------------------------------
    @property
    def close(self):
        """获取收盘价序列"""
        return self.closeArray[-self.size:]
    
    #----------------------------------------------------------------------
    @property    
    def volume(self):
        """获取成交量序列"""
        return self.volumeArray[-self.size:]
    
    #----------------------------------------------------------------------
    def hhv(self, n, array=False):
        """移动最高"""
        result = talib.MAX(self.high, n)
        if array:
            return result
        return result[-1]
        
    #----------------------------------------------------------------------
    def llv(self, n, array=False):
        """移动最低"""
        result = talib.MAX(self.high, n)
        if array:
            return result
        return result[-1]
        
    #----------------------------------------------------------------------
    def kdj(self, n, s, f, array=False):
        """KDJ指标"""
        c   = self.close
        hhv = self.hhv(n)
        llv = self.llv(n)
        shl = talib.SUM(hhv-llv,s)
        scl = talib.SUM(c-llv,s)
        k   = 100*shl/scl
        d   = talib.SMA(k,f)
        j   = 3*k - 2*d
        if array:
            return k,d,j
        return k[-1],d[-1],j[-1]
        
    #----------------------------------------------------------------------
    def sma(self, n, array=False):
        """简单均线"""
        result = talib.SMA(self.close, n)
        if array:
            return result
        return result[-1]
        
    #----------------------------------------------------------------------
    def std(self, n, array=False):
        """标准差"""
        result = talib.STDDEV(self.close, n)
        if array:
            return result
        return result[-1]
    
    #----------------------------------------------------------------------
    def cci(self, n, array=False):
        """CCI指标"""
        result = talib.CCI(self.high, self.low, self.close, n)
        if array:
            return result
        return result[-1]
        
    #----------------------------------------------------------------------
    def kd(self, nf=9, ns=3, array=False):
        """KD指标"""
        slowk, slowd = talib.STOCH(self.high, self.low, self.close,
                        fastk_period=nf,
                        slowk_period=ns,
                        slowk_matype=0,
                        slowd_period=ns,
                        slowd_matype=0)
        if array:
            return slowk, slowd 
        return slowk[-1], slowd[-1]
        
    #----------------------------------------------------------------------
    def vol(self, n, array=False):
        """波动率指标"""
        logrtn = talib.LN(self.high/self.low)
        stdrtn = talib.STDDEV(logrtn,n)
        vol    = talib.EXP(stdrtn)-1
        if array:
            return vol
        return vol[-1]
        
    #----------------------------------------------------------------------
    def atr(self, n, array=False):
        """ATR指标"""
        result = talib.ATR(self.high, self.low, self.close, n)
        if array:
            return result
        return result[-1]
        
    #----------------------------------------------------------------------
    def cmi(self, n, array=False):
        """CMI指标"""
        hhm = max(self.high[-n:])
        llm = min(self.low[-n:])
        delta = abs(self.close[-1]-self.close[-n])
        result = delta/(hhm-llm)
        return result

    #----------------------------------------------------------------------
    def rsi(self, n, array=False):
        """RSI指标"""
        result = talib.RSI(self.close, n)
        if array:
            return result
        return result[-1]
    
    #----------------------------------------------------------------------
    def macd(self, fastPeriod, slowPeriod, signalPeriod, array=False):
        """MACD指标"""
        macd, signal, hist = talib.MACD(self.close, fastPeriod,
                                        slowPeriod, signalPeriod)
        if array:
            return macd, signal, hist
        return macd[-1], signal[-1], hist[-1]
    
    #----------------------------------------------------------------------
    def adx(self, n, array=False):
        """ADX指标"""
        result = talib.ADX(self.high, self.low, self.close, n)
        if array:
            return result
        return result[-1]
    
    #----------------------------------------------------------------------
    def peak(self, lookahead=100, delta=5, array=False):
        """峰值"""
        size = min(self.count,self.maxsize-1)
        maxP,minP = peakdetect(self.closeArray[-size:],lookahead=lookahead,delta=delta)
        if array:
            return maxP,minP
        return maxP,minP

    #----------------------------------------------------------------------
    def boll(self, n, dev, array=False):
        """布林通道"""
        mid = self.sma(n, array)
        std = self.std(n, array)
        
        up = mid + std * dev
        down = mid - std * dev
        
        return up, down    
    
    #----------------------------------------------------------------------
    def keltner(self, n, dev, array=False):
        """肯特纳通道"""
        mid = self.sma(n, array)
        atr = self.atr(n, array)
        
        up = mid + atr * dev
        down = mid - atr * dev
        
        return up, down
    
    #----------------------------------------------------------------------
    def donchian(self, n, array=False):
        """唐奇安通道"""
        up = talib.MAX(self.high, n)
        down = talib.MIN(self.low, n)
        
        if array:
            return up, down
        return up[-1], down[-1]
