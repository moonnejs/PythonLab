# encoding: UTF-8

"""
基础策略模板，
"""

from __future__ import division
from ctaBase import *
from ctaTemplate import *

########################################################################
class BASICStrategy(CtaTemplate):
    """基础策略模板"""

    # 基础信息
    author    = u'binbinwei'        # 作者
    className = 'BASICStrategy'     # 策略类名称
    name      = EMPTY_UNICODE       # 策略实例名称

    # 策略参数
    vtSymbol  = '600435'            # 合约
    exchange  = 'SSE'               # 交易所
    mPrice    = 0.01                # 一跳的价格
    nMin      =  1  		    # 操作级别分钟数
    initDays  = 10                  # 初始化数据所用的天数

    # 策略变量


    # 参数列表，保存了参数的名称
    paramList = []

    # 变量列表，保存了变量的名称
    varList = []

    #----------------------------------------------------------------------
    def __init__(self,ctaEngine=None,setting={}):
        """Constructor"""
        super(BASICStrategy, self).__init__(ctaEngine,setting)
        
        # 创建K线合成器对象
        self.bm = BarManager(self.onBar,self.nMin)

        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）        

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        super(BASICStrategy, self).onTick(tick)
        self.bm.updateTick(tick)

    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        super(BASICStrategy, self).onBar(bar)

    #----------------------------------------------------------------------
    def getCtaIndictor(self,bar):
        """计算指标数据"""
        # 计算指标数值
        return

    #----------------------------------------------------------------------
    def getCtaSignal(self,bar):
        """计算交易信号"""
        close  = bar.close
        hour   = bar.datetime.hour
        minute = bar.datetime.minute
        # 定义尾盘，尾盘不交易并且空仓
        self.endOfDay = False
        # 判断是否要进行交易
        self.buySig   = False
        self.shortSig = False
        self.coverSig = False
        self.sellSig  = False
        # 交易价格
        self.longPrice  = bar.close
        self.shortPrice = bar.close

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        super(BASICStrategy, self).onTrade(trade,log=True)

