# encoding: UTF-8

'''
本文件中包含了CTA模块中用到的一些基础设置、类和常量等。
'''

from __future__ import division
from vtConstant import *

# 把vn.trader根目录添加到python环境变量中
import sys
sys.path.append('..')


# 常量定义
# CTA引擎中涉及到的交易方向类型
CTAORDER_BUY = u'买开'
CTAORDER_SELL = u'卖平'
CTAORDER_SELL_TODAY = u'卖平今'
CTAORDER_SHORT = u'卖开'
CTAORDER_COVER = u'买平'
CTAORDER_COVER_TODAY = u'买平今'
STATUS_PARTTRADED_PARTCANCELLED = u'部成部撤'

# 本地停止单状态
STOPORDER_WAITING   = u'等待中'
STOPORDER_CANCELLED = u'已撤销'
STOPORDER_TRIGGERED = u'已触发'

# 本地停止单前缀
STOPORDERPREFIX = 'CtaStopOrder.'

# CTA模块事件
EVENT_CTA_LOG = 'eCtaLog'               # CTA相关的日志事件
EVENT_CTA_STRATEGY = 'eCtaStrategy.'    # CTA策略状态变化事件

# 数据库名称
SETTING_DB_NAME = 'VnTrader_Setting_Db'
CAPITAL_DB_NAME = 'vt_trader_cap_db'
TICK_DB_NAME    = 'vnTrader_Tick_db'
CAP_DB_NAME     = 'vt_trader_cap_db'
DAILY_DB_NAME   = 'VnTrader_Daily_Db'
MINUTE_DB_NAME  = 'VnTrader_1Min_Db'

########################################################################
class CtaBarData(object):
    """K线数据"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.vtSymbol = EMPTY_STRING        # vt系统代码
        self.symbol = EMPTY_STRING          # 代码
        self.exchange = EMPTY_STRING        # 交易所
    
        self.open = EMPTY_FLOAT             # OHLC
        self.high = EMPTY_FLOAT
        self.low = EMPTY_FLOAT
        self.close = EMPTY_FLOAT
        
        self.date = EMPTY_STRING            # bar开始的时间，日期
        self.time = EMPTY_STRING            # 时间
        self.datetime = None                # python的datetime时间对象
        
        self.volume = EMPTY_INT             # 成交量
        self.openInterest = EMPTY_INT       # 持仓量
        self.turnover = EMPTY_FLOAT         # 成交额


########################################################################
class CtaTickData(object):
    """Tick数据"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""       
        self.vtSymbol = EMPTY_STRING            # vt系统代码
        self.symbol = EMPTY_STRING              # 合约代码
        self.exchange = EMPTY_STRING            # 交易所代码

        # 成交数据
        self.lastPrice = EMPTY_FLOAT            # 最新成交价
        self.volume = EMPTY_INT                 # 最新成交量
        self.openInterest = EMPTY_INT           # 持仓量
        
        self.upperLimit = EMPTY_FLOAT           # 涨停价
        self.lowerLimit = EMPTY_FLOAT           # 跌停价

        self.turnover = EMPTY_FLOAT		# 成交额
        
        # tick的时间
        self.date = EMPTY_STRING            # 日期
        self.time = EMPTY_STRING            # 时间
        self.datetime = None                # python的datetime时间对象
        
        # 五档行情
        self.bidPrice1 = EMPTY_FLOAT
        self.bidPrice2 = EMPTY_FLOAT
        self.bidPrice3 = EMPTY_FLOAT
        self.bidPrice4 = EMPTY_FLOAT
        self.bidPrice5 = EMPTY_FLOAT
        
        self.askPrice1 = EMPTY_FLOAT
        self.askPrice2 = EMPTY_FLOAT
        self.askPrice3 = EMPTY_FLOAT
        self.askPrice4 = EMPTY_FLOAT
        self.askPrice5 = EMPTY_FLOAT        
        
        self.bidVolume1 = EMPTY_INT
        self.bidVolume2 = EMPTY_INT
        self.bidVolume3 = EMPTY_INT
        self.bidVolume4 = EMPTY_INT
        self.bidVolume5 = EMPTY_INT
        
        self.askVolume1 = EMPTY_INT
        self.askVolume2 = EMPTY_INT
        self.askVolume3 = EMPTY_INT
        self.askVolume4 = EMPTY_INT
        self.askVolume5 = EMPTY_INT    
        
########################################################################
class CtaCapData(object):
    """策略资产数据"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""       
        self.name = EMPTY_STRING                 # 策略名
        self.datetime = None                     # 时间
        self.start = None                        # 开始时间
        self.date = None                         # 日期
        self.cap = EMPTY_FLOAT                   # 资金
        self.pnl = EMPTY_FLOAT                   # 当日盈亏
        self.drawdown = EMPTY_FLOAT              # 回撤
