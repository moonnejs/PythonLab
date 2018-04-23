# encoding: UTF-8

"""
加佳交易系统策略

注意事项：
1. 作者不对交易盈利做任何保证，策略代码仅供参考
"""

from __future__ import division
import ctypes
from ctaBase import *
from ctaTemplate import *


########################################################################
class JJNZDStrategy(CtaTemplate):
    """加佳通道交易策略"""
    vtSymbol = 'rb1801'
    exchange = 'SHFE'
    className = 'JJNZDStrategy'
    author = u'binbinwei'
    name = EMPTY_UNICODE                # 策略实例名称

    # 参数列表，保存了参数的名称
    paramList = ['N',
                 'mPrice',
                 'dRatio',
                 'delta',
                 'detectTh',
                 'nMin',
                 'V']

    # 变量列表，保存了变量的名称
    varList = ['trading',
               'pos',
               'hpeak',
               'lpeak',
               'nHigh',
               'nLow',
               'dZone']

    # 参数映射表
    paramMap = {'N'       :u'回溯周期',
                'V'       :u'下单手数',
                'delta'   :u'峰值过滤阈值',
                'dRatio'  :u'决策区宽度',
                'mPrice'  :u'最小价格变动',
                'nMin'    :u'交易周期',
		'exchange':u'交易所',
                'vtSymbol':u'合约'}

    # 变量映射表
    varMap   = {'trading' :u'交易中',
                'pos'     :u'仓位',
                'dZone'   :u'波动范围',
                'nHigh'   :u'上决策区次数',
                'nLow'    :u'下决策区次数',
                'hpeak'   :u'上轨',
                'lpeak'   :u'下轨'}


    #----------------------------------------------------------------------
    def __init__(self,ctaEngine=None,setting={}):
        """Constructor"""

        # 策略参数
        self.N        = 60
        self.V        = 1
        self.dZone    = 0
        self.nMin     = 15
        self.detectTh = 10
        self.dRatio   = 0.2
        self.delta    = 20
        self.mPrice   = 1

        # 策略状态
        self.hhv      = 0
        self.llv      = 0
        self.hpeak    = 0
        self.lpeak    = 0
        self.atr      = 0
        self.cost     = 0
        self.nextTick = False


        self.lasttime   = ''
        self.lastbar    = None
        self.lastsymbol = None

        super(JJNZDStrategy, self).__init__(ctaEngine,setting)

        # 决策区
        self.inHZone = np.zeros(self.N)
        self.inLZone = np.zeros(self.N)
        self.crossH  = np.zeros(self.N)
        self.crossL  = np.zeros(self.N)
        self.dZone   = 1
        self.nHigh   = 0
        self.nLow    = 0

        self.updateH = True               # 是否需要重绘通道
        self.updateL = True               # 是否需要重绘通道

        self.KH      = 0                   # 高点通道斜率
        self.DH      = 0                   # 低点通道截距
        self.KL      = 0                   # 高点通道斜率
        self.DL      = 0                   # 低点通道截距

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
        super(JJNZDStrategy, self).onUpdate(setting)
        self.bm = BarManager(self.onBar,self.nMin,self.onBarX)
        self.am = ArrayManager(size=self.N)

    #----------------------------------------------------------------------
    def onBar(self, bar):
        bar.vtSymbol = bar.symbol
        self.bm.updateBar(bar)

    #----------------------------------------------------------------------
    def onBarX(self, bar):
        self.vtSymbol = bar.symbol

        self.bar = bar
        # 记录数据
        if not self.am.updateBar(bar):
            return
        # 回测检查换月
        if not self.lastsymbol is None:
            pos = self.pos[self.lastsymbol]
        else:
            pos = 0
        if self.lastsymbol is None:
            self.lastsymbol = bar.vtSymbol
        elif (bar.vtSymbol > self.lastsymbol) and pos == 0:
            self.output(' '.join([u'换月',self.lastsymbol,bar.vtSymbol]))
            self.lastsymbol = bar.vtSymbol
        elif (bar.vtSymbol > self.lastsymbol) and pos != 0 and self.orderID is None:
            self.output(' '.join([u'换月移仓',self.lastsymbol,bar.vtSymbol]))
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

        self.lasttime = bar.time
        self.lastbar = bar
        self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        super(JJNZDStrategy, self).onTick(tick)
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
        close  = bar.close
        # 决策区
        self.inHZone[0:self.N-1] = self.inHZone[1:self.N]
        self.inLZone[0:self.N-1] = self.inLZone[1:self.N]
        self.crossH[0:self.N-1]  = self.crossH[1:self.N]
        self.crossL[0:self.N-1]  = self.crossL[1:self.N]
        self.inHZone[-1] = 1 if close > self.hhv-self.dRatio*self.dZone else 0
        self.inLZone[-1] = 1 if close < self.llv+self.dRatio*self.dZone else 0
        self.crossH[-1]  = 1 if self.inHZone[-1]==1 and self.inHZone[-2]==0 else 0
        self.crossL[-1]  = 1 if self.inLZone[-1]==1 and self.inLZone[-2]==0 else 0
        # 决策区次数
        self.nLow  = sum(self.crossL)
        self.nHigh = sum(self.crossH)

    #----------------------------------------------------------------------
    def getCtaSignal(self,bar):
        """计算交易信号"""
        close = bar.close
        pos   = self.pos[self.vtSymbol]
        # 定义尾盘，尾盘不交易并且空仓
        self.endOfDay = False
        # 判断是否要进行交易
        goodpeak = self.hpeak != 0 and self.lpeak != 0 and self.hpeak - self.lpeak > 10*self.mPrice
        self.shortSig = self.hpeak + self.dRatio*self.dZone >= bar.close >= self.hpeak and not self.updateH and goodpeak
        self.buySig   = self.lpeak - self.dRatio*self.dZone <= bar.close <= self.lpeak and not self.updateL and goodpeak
        self.sellSig  = bar.close >= self.hpeak or bar.close <= self.lpeak - self.dRatio*self.dZone
        self.coverSig = bar.close <= self.lpeak or bar.close >= self.hpeak + self.dRatio*self.dZone
        # 交易价格
        self.buyPrice   = bar.close+20*self.mPrice
        self.shortPrice = bar.close-20*self.mPrice
        self.coverPrice = bar.close+20*self.mPrice
        self.sellPrice  = bar.close-20*self.mPrice
        if not self.updateH:
            self.updateH = close > self.hpeak
        if not self.updateL:
            self.updateL = close < self.lpeak
        high,low = self.am.peak(self.detectTh,self.delta*self.mPrice,True)
        if len(high) >= 2:
            p0 = high[-1]
            p1 = high[-2]
            #print 'high',p0,p1
            KH = (p0[1]-p1[1])/(p0[0]-p1[0])
            self.DH = p0[1]-KH*p0[0]
            if not KH == self.KH:
                self.KH = KH
                self.updateH =False
        if len(low) >= 2:
            p0 = low[-1]
            p1 = low[-2]
            #print 'low',p0,p1
            KL = (p0[1]-p1[1])/(p0[0]-p1[0])
            self.DL =  p0[1]-KL*p0[0]
            if not KL == self.KL:
                self.KL = KL
                self.updateL =False
        self.DH += self.KH
        self.DL += self.KL
        self.hhv = max(self.am.high[-self.N:])
        self.llv = min(self.am.low[-self.N:])
        self.hpeak = self.KH*self.N+self.DH
        self.lpeak = self.KL*self.N+self.DL
        self.dZone = self.hhv - self.llv


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
            elif self.buySig:
                self.orderID = self.buy(self.buyPrice, volume)
        elif pos!= 0:
            # 持有多头仓位
            if pos > 0 and (self.sellSig or self.endOfDay):
                self.orderID = self.sell(self.sellPrice, pos)
            elif pos < 0 and (self.coverSig or self.endOfDay):
                self.orderID = self.cover(self.coverPrice, -pos)

    #---------------------------------------------------------------------
    def onTrade(self, trade):
        self.cost = trade.price
        super(JJNZDStrategy, self).onTrade(trade,log=True)

    #----------------------------------------------------------------------
    def onStart(self):
        self.loadBar(3)
        super(JJNZDStrategy, self).onStart()

    #----------------------------------------------------------------------
    def onStop(self):
        super(JJNZDStrategy, self).onStop()
