# encoding: UTF-8

"""
双均线策略

注意事项：
1. 作者不对交易盈利做任何保证，策略代码仅供参考
2. 本策略需要用到talib，没有安装的用户请先参考www.vnpy.org上的教程安装
"""

from __future__ import division
from ctaBase import *
from ctaTemplate import *


########################################################################
class DMAStrategy(CtaTemplate):
    """双均线交易策略"""
    vtSymbol = 'rb1801'
    exchange = 'SHFE'
    className = 'DMAStrategy'
    author = u'binbinwei'
    name = EMPTY_UNICODE                # 策略实例名称

    # 策略参数
    N = 5                               # 快均线周期
    P = 20                              # 慢均线周期
    A = 26                              # 止损
    mPrice = 5                          # 一跳的价格
    nMin =  1                           # 操作级别分钟数
    initDays = 10                       # 初始化数据所用的天数

    # 策略变量
    ma0  = 0                            # 当前K线慢均线数值
    ma1  = 0                            # 当前K线快均线数值
    ma00 = 0                            # 上一个K线慢均线数值
    ma10 = 0                            # 上一个K线快均线数值

    # 参数列表，保存了参数的名称
    paramList = ['N',
                 'P',
                 'A',
                 'V',
                 'nMin',
                 'mPrice']

    # 变量列表，保存了变量的名称
    varList = ['trading',
               'ma0',
               'ma1',
               'pos']

    # 参数映射表
    paramMap = {'N'   :u'快均线周期',
                'P'   :u'慢均线周期',
                'A'   :u'止损指标',
                'v'   :u'下单手数',
                'nMin':u'K线分钟',
                'exchange':u'交易所',
                'vtSymbol':u'合约'}

    # 变量映射表
    varMap   = {'trading' :u'交易中',
                'ma0'     :u'慢均线',
                'ma1'     :u'快均线'}


    #----------------------------------------------------------------------
    def __init__(self,ctaEngine=None,setting={}):
        """Constructor"""
        super(DMAStrategy, self).__init__(ctaEngine,setting)

        self.widgetClass = None
        self.widget = None

        self.bm = BarManager(self.onBar,self.nMin)

        self.cost = 0                            # 持仓成本
        
        self.V = 1                               # 下单手数
        self.ma0 = 0                             # 当前K线慢均线数值
        self.ma1 = 0                             # 当前K线快均线数值
        self.ma00 = 0                            # 上一个K线慢均线数值
        self.ma10 = 0                            # 上一个K线快均线数值

        
        # 启动界面
        self.signal = 0                          # 买卖标志
        self.mainSigs = ['ma0','ma1','cost']     # 主图显示
        self.subSigs = []                        # 副图显示
        #self.getGui()

        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）        

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送"""
        super(DMAStrategy, self).onTick(tick)
        # 过滤涨跌停和集合竞价
        if tick.lastPrice == 0 or tick.askPrice1==0 or tick.bidPrice1==0:
            return
        self.bm.updateTick(tick)

    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        self.bar = bar
        if self.tradeDate != bar.datetime.date():
            self.tradeDate = bar.datetime.date()

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
        if (not self.widget is None) and (not self.bar is None):
            data = {'bar':self.bar,'sig':self.signal,'ma0':self.ma0,'ma1':self.ma1,'cost':self.cost}
            self.widget.addBar(data)
        if self.trading:
            self.putEvent()

    #----------------------------------------------------------------------
    def getCtaIndictor(self,bar):
        """计算指标数据"""
        # 计算指标数值
        ma  = self.am.sma(self.P,True)
        ma1 = self.am.sma(self.N,True)
        self.ma0,self.ma00 = ma[-1],ma[-2]
        self.ma1,self.ma10 = ma1[-1],ma1[-2]

    #----------------------------------------------------------------------
    def getCtaSignal(self,bar):
        """计算交易信号"""
        close  = bar.close
        hour   = bar.datetime.hour
        minute = bar.datetime.minute
        # 定义尾盘，尾盘不交易并且空仓
        self.endOfDay = hour==14 and minute >=40
        # 判断是否要进行交易
        self.buySig   = self.ma1 > self.ma0 and self.ma10 < self.ma00
        self.shortSig = self.ma1 < self.ma0 and self.ma10 > self.ma00
        self.coverSig = self.buySig or close >= self.cost+self.A*close
        self.sellSig  = self.shortSig or close <= self.cost-self.A*close
        # 交易价格
        self.longPrice  = bar.close
        self.shortPrice = bar.close

    #----------------------------------------------------------------------
    def execSignal(self,volume):
        """简易交易信号执行"""
        pos = self.pos[self.vtSymbol]
        endOfDay = self.endOfDay
        # 挂单未成交
        if not self.orderID is None:
            self.cancelOrder(self.orderID)

        self.signal = 0
        # 当前无仓位
        if pos == 0 and not self.endOfDay:
            # 买开，卖开    
            if self.shortSig:
                self.signal = -self.shortPrice
                self.orderID = self.short(self.shortPrice, volume)
            elif self.buySig:
                self.signal = self.longPrice
                self.orderID = self.buy(self.longPrice, volume)

        # 持有多头仓位
        elif pos > 0 and (self.sellSig or self.endOfDay):
                self.signal = -self.shortPrice
                self.orderID = self.sell(self.shortPrice, pos)

        # 持有空头仓位
        elif pos < 0 and (self.coverSig or self.endOfDay):
                self.signal = self.longPrice
                self.orderID = self.cover(self.longPrice, -pos)

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        super(DMAStrategy, self).onTrade(trade,log=True)

    #----------------------------------------------------------------------
    def onStart(self):
        self.loadBar(3)
        super(DMAStrategy, self).onStart()
        #self.getGui()

    #----------------------------------------------------------------------
    def onStop(self):
        super(DMAStrategy, self).onStop()
        if not self.widget is None:
            self.widget.clear()
            #self.closeGui()
