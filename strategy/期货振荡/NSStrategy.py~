# encoding: UTF-8

"""
逆势交易系统策略

注意事项：
1. 作者不对交易盈利做任何保证，策略代码仅供参考
"""

from __future__ import division
import ctypes
import math
from ctaBase import *
from ctaTemplate import *


########################################################################
class NSStrategy(CtaTemplate):
    """逆势交易策略"""
    vtSymbol = 'rb1801'
    exchange = 'SHFE'
    className = 'NSStrategy'
    author = u'binbinwei'
    name = EMPTY_UNICODE                # 策略实例名称

    # 参数列表，保存了参数的名称
    paramList = ['N',
                 'K',
                 'D',
                 'nBar',
                 'nMin',
                 'mPrice',
                 'V']

    # 变量列表，保存了变量的名称
    varList = ['trading',
               'pos',
               'hhv',
               'llv',
               'oRatio',
               'nHigh',
               'nLow',
               'dZone']

    # 参数映射表
    paramMap = {'N'       :u'回溯周期',
                'K'       :u'标准差倍数',
                'D'       :u'阈值',
                'V'       :u'下单手数',
                'nBar'    :u'持仓时间',
                'mPrice'  :u'最小价格变动',
                'nMin'    :u'交易周期',
		'exchange':u'交易所',
                'vtSymbol':u'合约'}

    # 变量映射表
    varMap   = {'trading' :u'交易中',
                'pos'     :u'仓位',
                'dZone'   :u'波动范围',
                'oRatio'  :u'波动范围',
                'nHigh'   :u'上决策区次数',
                'nLow'    :u'下决策区次数',
                'hhv'     :u'上轨',
                'llv'     :u'下轨'}


    #----------------------------------------------------------------------
    def __init__(self,ctaEngine=None,setting={}):
        """Constructor"""

        # 策略参数
        self.N      = 60
        self.K      = 3
        self.D      = 0.005
        self.V      = 1
        self.dZone  = 0
        self.nMin   = 15
        self.mPrice = 1
        self.nBar   = 1

        # 策略状态
        self.hhv = 0
        self.llv = 0
        self.mid = 0
        self.cost = 0
        self.shortStop = 0
        self.longStop = 0
        self.oRatio = 0.1
        self.dRatio = 0.1
        self.barSinceOpen   = 0
        self.nextTick = False
        self.lastbreakL = False
        self.lastbreakH = False


        self.lastbar = None
        self.lastsymbol = None

        super(NSStrategy, self).__init__(ctaEngine,setting)

        # 决策区
        self.inHZone = np.zeros(self.N)
        self.inLZone = np.zeros(self.N)
        self.crossH  = np.zeros(self.N)
        self.crossL  = np.zeros(self.N)
        self.dZone   = 1
        self.nHigh   = 0
        self.nLow    = 0

        self.buyPrice   = EMPTY_FLOAT      # 多头开仓价
        self.shortPrice = EMPTY_FLOAT      # 空头开仓价
        self.coverPrice = EMPTY_FLOAT      # 多头开仓价
        self.sellPrice  = EMPTY_FLOAT      # 空头开仓价


        # K线
        self.bm = BarManager(self.onBar,self.nMin,self.onBarX)

        # 默认技术指标列表
        self.am = ArrayManager(size=self.N)
        
        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）        

    #----------------------------------------------------------------------
    def onUpdate(self,setting):
        """刷新策略"""
        super(NSStrategy, self).onUpdate(setting)
        self.bm = BarManager(self.onBar,self.nMin,self.onBarX)
        self.am = ArrayManager(size=self.N)

    #----------------------------------------------------------------------
    def onBar(self, bar):
        bar.vtSymbol = bar.symbol
        self.bm.updateBar(bar)
        self.am.updateBar(bar)
        self.lastbar = bar

    #----------------------------------------------------------------------
    def onBarX(self, bar):
        self.vtSymbol = bar.symbol

        self.bar = bar
        # 记录数据
        #if not self.am.updateBar(bar):
        #    return
        # 计算指标

        # 回测检查换月
        if not self.lastsymbol is None:
            pos = self.pos[self.lastsymbol]
        else:
            pos = 0
        if self.lastsymbol is None:
            self.lastsymbol = bar.vtSymbol
        elif (bar.vtSymbol > self.lastsymbol) and pos == 0:
            print u'换月',self.lastsymbol,bar.vtSymbol
            self.lastsymbol = bar.vtSymbol
        elif (bar.vtSymbol > self.lastsymbol) and pos != 0:
            print u'换月移仓',self.lastsymbol,bar.vtSymbol
            # 持有多头仓位
            if pos > 0:
                self.orderID = self.sell(self.lastbar.close-20*self.mPrice, pos, self.lastsymbol)
                self.orderID = self.buy(bar.close+20*self.mPrice, pos)
            elif pos < 0:
                self.orderID = self.cover(self.lastbar.close+20*self.mPrice, -pos, self.lastsymbol)
                self.orderID = self.short(bar.close-20*self.mPrice, -pos)
            self.lastsymbol = bar.vtSymbol
        # 简易信号执行
        elif self.am.inited:
            self.getCtaIndictor(bar)
            self.getCtaSignal(bar)
            self.execSignal(self.V)
            self.barSinceOpen += 1

        self.lastbar = bar
        self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        super(NSStrategy, self).onTick(tick)
        # 过滤涨跌停和集合竞价
        if tick.lastPrice == 0 or tick.askPrice1==0 or tick.bidPrice1==0:
            return
        self.bm.updateTick(tick)
        if self.nextTick == True:
            self.nextTick = False
            self.execSignal(self.V)

    #----------------------------------------------------------------------
    def getCtaIndictor(self,bar):
        """计算指标数据"""
        # 计算指标数值
        self.dRatio = self.oRatio = self.K*self.nMin*self.am.vol(self.N)+self.D
        # 计算指标数值
        self.hhv = bar.open + bar.close*self.oRatio
        self.llv = bar.open - bar.close*self.oRatio
        self.mid = self.am.sma(self.N)

    #----------------------------------------------------------------------
    def getCtaSignal(self,bar):
        """计算交易信号"""
        close  = bar.close
        # 定义尾盘，尾盘不交易并且空仓
        self.endOfDay = False
        # 判断是否要进行交易
        self.shortSig = bar.high <= self.lastbar.high and self.lastbreakH
        self.buySig   = bar.low  >= self.lastbar.low  and self.lastbreakL
        self.sellSig  = self.barSinceOpen >= self.nBar
        self.coverSig = self.barSinceOpen >= self.nBar
        # 交易价格
        self.buyPrice   = close+2*self.mPrice#bar.open-close*self.oRatio
        self.shortPrice = close-2*self.mPrice#bar.open+close*self.oRatio
        self.coverPrice = close+2*self.mPrice
        self.sellPrice  = close-2*self.mPrice
        self.lastbreakH = bar.high > self.hhv
        self.lastbreakL = bar.low  < self.llv

    #----------------------------------------------------------------------
    def execSignal(self,volume):
        """简易交易信号执行"""
        pos = self.pos[self.vtSymbol]
        endOfDay = self.endOfDay
        # 挂单未成交
        if not self.orderID is None:
            self.cancelOrder(self.orderID)
            self.nextTick = True
        # 当前无仓位
        if pos == 0 and not self.endOfDay:
            # 买开，卖开    
            if self.shortSig:
                self.orderID = self.short(self.shortPrice, volume)
                self.barSinceOpen = 0
            elif self.buySig:
                self.orderID = self.buy(self.buyPrice, volume)
                self.barSinceOpen = 0
        elif pos!= 0:
            # 持有多头仓位
            if pos > 0 and (self.sellSig or self.endOfDay):
                self.orderID = self.sell(self.sellPrice, pos)
            elif pos < 0 and (self.coverSig or self.endOfDay):
                self.orderID = self.cover(self.coverPrice, -pos)

    #---------------------------------------------------------------------
    def onTrade(self, trade):
        self.cost = trade.price
        super(NSStrategy, self).onTrade(trade,log=True)

    #----------------------------------------------------------------------
    def onStart(self):
        self.loadBar(3)
        super(NSStrategy, self).onStart()

    #----------------------------------------------------------------------
    def onStop(self):
        super(NSStrategy, self).onStop()
