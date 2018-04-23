# encoding: UTF-8

'''
本文件中包含的是CTA模块的回测引擎，回测引擎的API和CTA引擎一致，
可以使用和实盘相同的代码进行回测。
'''
from __future__ import division  
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from itertools import product

import os
import csv
import json
import copy
import pytz
import pymongo
import traceback
import threading
import multiprocessing
import pandas as pd
import matplotlib
matplotlib.use('Qt4Agg')

from datetime import datetime,timedelta
from collections import OrderedDict,defaultdict
from progressbar import ProgressBar
from collections import deque

from ctaBase import *
from vtConstant import *


from vtObject import VtOrderData, VtTradeData

#----------------------------------------------------------------------
def loadMongoSetting(path=""):
    """载入MongoDB数据库的配置"""
    try:
        f = file(path+"VT_setting.json")
        setting = json.load(f)
        host = setting['mongoHost']
        port = setting['mongoPort']
    except:
        host = 'localhost'
        port = 27017
    return host, port

########################################################################
class BacktestingEngine(object):
    """
    CTA回测引擎
    函数接口和策略引擎保持一样，
    从而实现同一套代码从回测到实盘。
    增加双合约回测功能
    增加快速慢速切换功能（挂单策略建议使用快速模式）
    """
    
    TICK_MODE = 'tick'
    BAR_MODE = 'bar'
    bufferSize = 1000
    Version = 20170928

    #----------------------------------------------------------------------
    def __init__(self,optimism=False):
        """Constructor"""
        # 回测相关
        self.strategy = None                        # 回测策略
        self.mode = self.BAR_MODE                   # 回测模式，默认为K线
        self.shfe = True                            # 上期所  
        self.fast = False                           # 是否支持排队

        self.plot = True                            # 打印数据
        self.plotfile = False                       # 打印到文件
        self.optimism = False                       # 高速回测模式

        self.symbolList = []                        # 用到的所有合约
        self.symbolMap = {}                         # 合约映射，为了适配主力连续
        
        self.leverage = {}                          # 保证金率
        self.slippage = {}                          # 回测时假设的滑点
        self.rate = {}                              # 回测时假设的佣金比例（适用于百分比佣金）
        self.size = {}                              # 合约大小，默认为1        
        self.mPrice = {}                            # 最小价格变动，默认为1        
        
        self.dbClient = None                        # 数据库客户端
        self.dbCursor = {}                          # 数据库指针
        self.index = {}                             # 指针当前位置
        self.dbCursor_count = {}                    # 数据库大小
        
        self.backtestingData = {}                   # 回测用的数据,deque([])
        self.savedata =  False                      # 保存外部数据
        self.datas =  None                          # 外部数据

        self.dataStartDate = None                   # 回测数据开始日期，datetime对象
        self.dataEndDate = None                     # 回测数据结束日期，datetime对象
        self.strategyStartDate = None               # 策略启动日期（即前面的数据用于初始化），datetime对象


        # 本地停止单
        self.stopOrderCount = 0                     # 编号计数：stopOrderID = STOPORDERPREFIX + str(stopOrderCount)
        
        self.stopOrderDict = {}                     # 停止单撤销后不会从本字典中删除
        self.workingStopOrderDict = {}              # 停止单撤销后会从本字典中删除
        
        self.limitOrderDict = OrderedDict()         # 限价单字典
        self.workingLimitOrderDict = OrderedDict()  # 活动限价单字典，用于进行撮合用
        self.limitOrderCount = 0                    # 限价单编号

        self.tradeCount = 0                         # 成交编号
        self.tradeDict = defaultdict(OrderedDict)   # 成交字典 OrderedDict()
        
        self.tradeSnap = OrderedDict()              # 合约市场快照

        self.dataClass = None                       # 使用的数据类

        self.logList = []                           # 日志记录
        self.tradeList = []                         # 成交记录

        self.orderPrice = {}                        # 合约限价单价格
        self.orderVolume = {}                       # 合约限价单盘口

        self.dataBar = []                           # 需要推送的K线数据
        self.dataState = []                         # 需要推送的状态数据
        self.dataDeal = []                          # 需要推送的成交数据
        self.dataDealOpen = []                      # 需要推送的成交数据
        self.dataPnl = []                           # 需要推送的盈亏数据（与开仓时间对齐）

        self.state = {}                             # 当前策略状态
        self.dealOpen = 0                           # 当前策略开仓
        self.lastOpen = []                          # 上一次策略开仓
        self.pnl = 0                                # 当前策略盈亏
        self.deal = 0                               # 当前策略平仓
            
        # 当前最新数据，用于模拟成交用
        self.tick = {}                              # 当前tick
        self.lasttick = {}                          # 上一个tick
        self.bar = {}                               # 当前bar
        self.lastbar = {}                           # 上一个bar
        self.dt = None                              # 最新的时间
        
    #----------------------------------------------------------------------
    def setStartDate(self, startDate='20100416', initDays=10):
        """设置回测的启动日期
           支持两种日期模式"""
        self.dataStartDate = datetime.strptime(startDate, '%Y%m%d') if len(startDate) == 8\
                        else datetime.strptime(startDate, '%Y%m%d %H:%M:%S')
        
    #----------------------------------------------------------------------
    def setEndDate(self, endDate='20100416'):
        """设置回测的结束日期
           支持两种日期模式"""
        self.dataEndDate= datetime.strptime(endDate, '%Y%m%d') if len(endDate) == 8\
                     else datetime.strptime(endDate, '%Y%m%d %H:%M:%S')
        
    #---------------------------------------------------------------------
    def setBacktestingMode(self, mode):
        """设置回测模式"""
        self.mode = mode
        self.dataClass = CtaBarData if self.mode == self.BAR_MODE\
                    else CtaTickData

    #----------------------------------------------------------------------
    def loadRefData(self, dbName):
        """载入参考数据"""
        self.output(u' ')

    #----------------------------------------------------------------------
    def getHistData(self):
        """获取参考数据"""
        self.output(u' ')

    #----------------------------------------------------------------------
    def loadHistoryData(self, dbName, symbolList):
        """载入历史数据"""
        self.symbolList = symbolList
        host, port = loadMongoSetting()
        if not self.dbClient:
            self.dbClient = pymongo.MongoClient(host, port, socketKeepAlive=True)
        self.output(u'开始载入数据')
        
        # 载入回测数据
        self.output("Start : " + str(self.dataStartDate))
        self.output("End : " + str(self.dataEndDate))
        # 数据过滤条件
        flt = {'datetime':{'$gte':self.dataStartDate}} if not self.dataEndDate\
        else  {'datetime':{'$gte':self.dataStartDate,
                           '$lt':self.dataEndDate}}  
        # 载入合约数据
        def loadData(symbol):
            collection = self.dbClient[dbName][symbol]          
            self.dbCursor[symbol] = collection.find(flt,no_cursor_timeout=True).batch_size(self.bufferSize)
            self.dbCursor_count[symbol] = self.dbCursor[symbol].count()
            self.backtestingData[symbol] = deque([])
            self.symbolMap[symbol] = symbol
            self.index[symbol] = 0
            self.output(u'合约%s载入完成，数据量：%s' %(symbol,self.dbCursor_count[symbol]))

        map(loadData,symbolList)

        self.output(u' ')

    #----------------------------------------------------------------------
    def prepareData(self):
        """数据准备线程"""
        # 快速读取
        index = self.index
        dataClass = self.dataClass
        dbCursor = self.dbCursor
        bufferSize = self.bufferSize
        dbCursor_count = self.dbCursor_count
        backtestingData = self.backtestingData
        # 补充数据缓存容器
        def fillData(symbol):
            while len(backtestingData[symbol]) < bufferSize and index[symbol] < dbCursor_count[symbol]:
                data = dataClass()
                data.__dict__ = dbCursor[symbol].next()
                # 为了弥补数据错误，需要删除
                data.datetime += timedelta(hours=8)
                backtestingData[symbol].append(data)
                self.symbolMap[data.symbol] = symbol
                index[symbol] += 1
        map(fillData,self.symbolList)

    #----------------------------------------------------------------------
    def runBacktesting(self):
        """运行回测"""

        start = datetime.now()

        # 首先根据回测模式，确认要使用的数据类
        dataClass,func = (CtaBarData,self.newBar) if self.mode == self.BAR_MODE\
                    else (CtaTickData,self.newTick)

        self.output(u'开始回放数据')

        # 快速读取
        index           = self.index
        dbCursor_count  = self.dbCursor_count
        backtestingData = self.backtestingData

        #检查是否回测完成
        #----------------------------------------------------------
        def backtestFinished():
            return any(((index[s] >= dbCursor_count[s] and not backtestingData[s]) for s in index))

        #检查是否存在缓存数据
        #----------------------------------------------------------
        def hasCacheData():
            return all([backtestingData[s] for s in index]) 

        # 多合约合约回测
        while not backtestFinished():        
            # 启动数据准备线程
            self.prepareData()
            # 模拟撮合
            while hasCacheData():
                latestDatetime = min([backtestingData[s][0].datetime for s in index])
                data = [backtestingData[s].popleft() for s in index\
                        if backtestingData[s][0].datetime == latestDatetime]
                data = [(d.symbol,d) for d in data]
                func(dict(data))

        # 推送回测结果数据
        # 将策略状态对齐到开仓
        lastOpen = 0
        for i in range(len(self.dataPnl)):
            if self.dataPnl[i] != 0:
                self.dataPnl[lastOpen] = self.dataPnl[i]
                self.dataPnl[i] = 0
                lastOpen = i
            if self.dataDealOpen[i] != 0:
                lastOpen = i
        # 推送结果
        self.datas = {'bar':self.dataBar,
                      'state':self.dataState,
                      'deal':self.dataDeal,
                      'pnl':self.dataPnl,
                      'dealOpen':self.dataDealOpen}
        
        end = datetime.now()

        self.output(u'耗时 : '+str(end-start))
        self.output(u'数据回放结束')


    #----------------------------------------------------------------------
    def dataProduced(self):
        """准备推送的数据"""
        if self.strategy is None:
            return
        bar    = self.strategy.bar
        symbol = self.strategy.vtSymbol
        if bar is None:
            return
        self.dataBar.append(bar.__dict__)
        self.dataState.append(self.getState())
        self.dataPnl.append(self.pnl)
        self.dataDeal.append(self.deal)
        self.dataDealOpen.append(self.dealOpen)
        self.deal = 0
        self.dealOpen = 0
        self.pnl = 0
        
    #----------------------------------------------------------------------
    def newBar(self, bar):
        """新的K线"""
        self.dt = bar.values()[0].datetime
        self.bar.update(bar)
        # 先全部撮合再全部推送，没有切片的合约不发送行情（为了和实盘一致）
        if not self.optimism:
            map(self.crossStopOrder,self.bar.keys())
            map(self.crossLimitOrder,self.bar.keys())
        map(self.strategy.onBar,bar.values())
        # 高速模式（直接撮合）
        if self.optimism:
            map(self.crossLimitOrder,self.bar.keys())
            map(self.crossStopOrder,self.bar.keys())
        self.lastbar = self.bar
    
    #----------------------------------------------------------------------
    def newTick(self, tick):
        """新的Tick"""
        self.dt = tick.values()[0].datetime
        self.tick.update(tick)
        # 低速模式（延时1个Tick撮合）
        map(self.crossLimitOrder,self.tick.keys())
        map(self.strategy.onTick,tick.values())
        # 高速模式（直接撮合）
        if self.optimism:
            map(self.crossLimitOrder,self.tick.keys())
        else:
            map(self.updateLimitOrder,self.tick.keys())
        self.lasttick.update(tick)

    #----------------------------------------------------------------------
    def initStrategy(self, strategyClass, setting=None):
        """
        初始化策略
        setting是策略的参数设置，如果使用类中写好的默认设置则可以不传该参数
        """
        self.output(u'开始回测')
        self.strategy = strategyClass(self, setting)
        
        self.strategy.inited = True
        self.strategy.onInit()
        self.output(u'策略初始化完成')
        
        self.strategy.trading = True
        self.strategy.onStart()
        self.output(u'策略启动完成')

        for symbol in self.strategy.symbolList:
            self.tradeDict[symbol] = OrderedDict()

    #----------------------------------------------------------------------
    def sendStopOrder(self, vtSymbol, orderType, price, volume, strategy):
        """发停止单（本地实现）"""

        self.stopOrderCount += 1
        stopOrderID = str(self.stopOrderCount)
        
        order = VtOrderData()
        order.vtSymbol = vtSymbol
        order.price = price
        order.priceType = PRICETYPE_LIMITPRICE
        order.totalVolume = volume
        order.status = STATUS_NOTTRADED     # 刚提交尚未成交
        order.orderID = stopOrderID
        order.vtOrderID = stopOrderID
        order.orderTime = str(self.dt)
        
        # CTA委托类型映射
        if orderType == CTAORDER_BUY:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_OPEN
        elif orderType == CTAORDER_SELL and not self.shfe:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_CLOSE
        elif orderType == CTAORDER_SELL and self.shfe:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_CLOSEYESTERDAY
        elif orderType == CTAORDER_SELL_TODAY:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_CLOSETODAY
        elif orderType == CTAORDER_SHORT:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_OPEN
        elif orderType == CTAORDER_COVER and not self.shfe:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_CLOSE     
        elif orderType == CTAORDER_COVER and self.shfe:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_CLOSEYESTERDAY     
        elif orderType == CTAORDER_COVER_TODAY:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_CLOSETODAY     
        
        # 保存stopOrder对象到字典中
        self.stopOrderDict[stopOrderID] = order
        self.workingStopOrderDict[stopOrderID] = order
        
        # 推送停止单初始更新
        self.strategy.onStopOrder(order)        
        
        return stopOrderID

    #----------------------------------------------------------------------
    def cancelStopOrder(self, stopOrderID):
        """撤销停止单"""
        # 检查停止单是否存在
        if stopOrderID in self.workingStopOrderDict:
            so = self.workingStopOrderDict[stopOrderID]
            so.status = STATUS_CANCELLED
            del self.workingStopOrderDict[stopOrderID]
            self.strategy.onStopOrder(so)
        
    #----------------------------------------------------------------------
    def sendOrder(self, vtSymbol, orderType, price, volume, strategy):
        """发单"""
        if not self.strategy.trading:
            return None
        self.limitOrderCount += 1
        orderID = str(self.limitOrderCount)
        
        order = VtOrderData()
        order.vtSymbol = vtSymbol
        order.price = price
        order.priceType = PRICETYPE_LIMITPRICE
        order.totalVolume = volume
        order.status = STATUS_NOTTRADED     # 刚提交尚未成交
        order.orderID = orderID
        order.vtOrderID = orderID
        order.orderTime = str(self.dt)
        
        # CTA委托类型映射
        if orderType == CTAORDER_BUY:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_OPEN
        elif orderType == CTAORDER_SELL and not self.shfe:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_CLOSE
        elif orderType == CTAORDER_SELL and self.shfe:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_CLOSEYESTERDAY
        elif orderType == CTAORDER_SELL_TODAY:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_CLOSETODAY
        elif orderType == CTAORDER_SHORT:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_OPEN
        elif orderType == CTAORDER_COVER and not self.shfe:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_CLOSE     
        elif orderType == CTAORDER_COVER and self.shfe:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_CLOSEYESTERDAY     
        elif orderType == CTAORDER_COVER_TODAY:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_CLOSETODAY     
        
        # 保存到限价单字典中
        self.workingLimitOrderDict[orderID] = order
        self.limitOrderDict[orderID] = order
        
        return orderID

    #----------------------------------------------------------------------
    def sendOrderFAK(self, vtSymbol, orderType, price, volume, strategy):
        """发单"""
        if not self.strategy.trading:
            return None
        self.limitOrderCount += 1
        orderID = str(self.limitOrderCount)
        
        order = VtOrderData()
        order.vtSymbol = vtSymbol
        order.price = price
        order.priceType = PRICETYPE_FAK
        order.totalVolume = volume
        order.status = STATUS_NOTTRADED     # 刚提交尚未成交
        order.orderID = orderID
        order.vtOrderID = orderID
        order.orderTime = str(self.dt)
        
        # CTA委托类型映射
        if orderType == CTAORDER_BUY:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_OPEN
        elif orderType == CTAORDER_SELL and not self.shfe:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_CLOSE
        elif orderType == CTAORDER_SELL and self.shfe:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_CLOSEYESTERDAY
        elif orderType == CTAORDER_SELL_TODAY:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_CLOSETODAY
        elif orderType == CTAORDER_SHORT:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_OPEN
        elif orderType == CTAORDER_COVER and not self.shfe:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_CLOSE     
        elif orderType == CTAORDER_COVER and self.shfe:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_CLOSEYESTERDAY     
        elif orderType == CTAORDER_COVER_TODAY:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_CLOSETODAY     
        
        self.workingLimitOrderDict[orderID] = order
        self.limitOrderDict[orderID] = order
        
        return orderID

    #----------------------------------------------------------------------
    def sendOrderFOK(self, vtSymbol, orderType, price, volume, strategy):
        """发单"""
        if not self.strategy.trading:
            return None
        self.limitOrderCount += 1
        orderID = str(self.limitOrderCount)
        
        order = VtOrderData()
        order.vtSymbol = vtSymbol
        order.price = price
        order.priceType = PRICETYPE_FOK
        order.totalVolume = volume
        order.status = STATUS_NOTTRADED     # 刚提交尚未成交
        order.orderID = orderID
        order.vtOrderID = orderID
        order.orderTime = str(self.dt)
        
        # CTA委托类型映射
        if orderType == CTAORDER_BUY:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_OPEN
        elif orderType == CTAORDER_SELL and not self.shfe:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_CLOSE
        elif orderType == CTAORDER_SELL and self.shfe:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_CLOSEYESTERDAY
        elif orderType == CTAORDER_SELL_TODAY:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_CLOSETODAY
        elif orderType == CTAORDER_SHORT:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_OPEN
        elif orderType == CTAORDER_COVER and not self.shfe:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_CLOSE     
        elif orderType == CTAORDER_COVER and self.shfe:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_CLOSEYESTERDAY     
        elif orderType == CTAORDER_COVER_TODAY:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_CLOSETODAY     
        
        self.workingLimitOrderDict[orderID] = order
        self.limitOrderDict[orderID] = order
        
        return orderID

    #----------------------------------------------------------------------
    def cancelOrder(self, vtOrderID):
        """撤单"""
        # 找到订单
        if vtOrderID in self.workingLimitOrderDict:
            order = self.workingLimitOrderDict[vtOrderID]
        else:
            order = None
            return False
        # 委托回报
        if order.status == STATUS_NOTTRADED:
            order.status = STATUS_CANCELLED
            order.cancelTime = str(self.dt)
            self.strategy.onOrder(order)
        else:
            order.status = STATUS_PARTTRADED_PARTCANCELLED
            order.cancelTime = str(self.dt)
            self.strategy.onOrder(order)
        # 删除数据
        if vtOrderID in self.workingLimitOrderDict:
            self.removeOrder(vtOrderID)
        return True
        
    #----------------------------------------------------------------------
    def filterTradeTime(self,tick,bar):
        """过滤非交易时间(国内期货和股票)"""
        if tick is None and bar is None:
            return True
        if self.dt:
            hour = self.dt.hour
            # 丢弃非交易时间错误数据
            if (hour >= 15 and hour < 20) or (hour > 2 and hour < 8):
                return True
            # 清空隔交易日订单
            elif hour == 8:
                self.lasttick = {}
                self.lastbar = {}
                for orderID in self.workingLimitOrderDict:
                    self.cancelOrder(orderID)
                return True
            elif hour == 20:
                self.lasttick = {}
                self.lastbar = {}
                for orderID in self.workingLimitOrderDict:
                    self.cancelOrder(orderID)
                return True
        return False

    #----------------------------------------------------------------------
    def calcTickVolume(self,tick,lasttick,size):
        """计算两边盘口的成交量"""
        if (not lasttick):
            currentVolume = tick.volume
            currentTurnOver = tick.turnover
            pOnAsk = tick.askPrice1
            pOnBid = tick.bidPrice1
        else:
            currentVolume = tick.volume - lasttick.volume
            currentTurnOver = tick.turnover - lasttick.turnover
            pOnAsk = lasttick.askPrice1
            pOnBid = lasttick.bidPrice1
        
        if lasttick and currentVolume > 0: 
            currentPrice = currentTurnOver/currentVolume/size
            ratio = (currentPrice-lasttick.bidPrice1)/(lasttick.askPrice1-lasttick.bidPrice1)
            ratio = max(ratio,0)
            ratio = min(ratio,1)
            volOnAsk = ratio*currentVolume/2
            volOnBid = currentVolume/2 - volOnAsk
        else:
            volOnAsk = 0
            volOnBid = 0
        return volOnBid,volOnAsk,pOnBid,pOnAsk

    #----------------------------------------------------------------------
    def removeOrder(self, orderID):
        """清除订单信息"""
        if orderID in self.workingLimitOrderDict:
            del self.workingLimitOrderDict[orderID]
        if orderID in self.orderPrice:
            del self.orderPrice[orderID]
        if orderID in self.orderVolume:
            del self.orderVolume[orderID]

    #----------------------------------------------------------------------
    def snapMarket(self, tradeID):
        """快照市场"""
        if self.mode == self.TICK_MODE:
            self.tradeSnap[tradeID] = copy.copy(self.tick)
        else:
            self.tradeSnap[tradeID] = copy.copy(self.bar)

    #----------------------------------------------------------------------
    def strategyOnOrder(self, order, volumeTraded):
        """处理委托回报"""
        orderID = order.orderID
        order.tradedVolume += volumeTraded
        # FOK订单，不全部成交则撤销
        if order.priceType == PRICETYPE_FOK:
            if order.tradedVolume < order.totalVolume:
                order.tradedVolume = 0
                order.status = STATUS_CANCELLED
            else:
                order.status = STATUS_ALLTRADED
        # FAK订单，不全部成交则剩余撤销
        elif order.priceType == PRICETYPE_FAK:
            if order.tradedVolume == 0:
                order.status = STATUS_CANCELLED
            elif order.tradedVolume < order.totalVolume:
                order.status = STATUS_PARTTRADED_PARTCANCELLED
            else:
                order.status = STATUS_ALLTRADED
        # 普通限价单，不成交剩余排队
        else:
            if order.tradedVolume == 0:
                order.status = STATUS_NOTTRADED
            elif order.tradedVolume < order.totalVolume:
                order.status = STATUS_PARTTRADED
            else:
                order.status = STATUS_ALLTRADED
        # 处理完毕，完成订单删除数据
        if not (order.status == STATUS_PARTTRADED\
             or order.status == STATUS_NOTTRADED):
            self.removeOrder(order.orderID)
            self.strategy.onOrder(order)
        # 推送委托回报
        elif volumeTraded > 0:
            self.strategy.onOrder(order)


    #----------------------------------------------------------------------
    def strategyOnTrade(self, order, volumeTraded, priceTraded):
        """处理成交回报"""
        if volumeTraded<=0:
            return
        # 推送成交数据,
        self.tradeCount += 1
        tradeID = str(self.tradeCount)
        trade = VtTradeData()
        #省略回测无关内容
        #trade.tradeID = tradeID
        #trade.vtTradeID = tradeID
        trade.orderID = order.orderID
        trade.vtOrderID = order.orderID
        trade.dt = self.dt
        trade.vtSymbol = order.vtSymbol
        trade.direction = order.direction
        trade.offset = order.offset
        trade.tradeTime = self.dt.strftime('%Y%m%d %H:%M:%S.')+self.dt.strftime('%f')[:1] 
        trade.volume = volumeTraded
        trade.price = priceTraded
        # 记录成交
        self.deal = priceTraded if trade.direction == u'多' else -priceTraded
        self.dealOpen = priceTraded if trade.direction == DIRECTION_LONG and trade.offset == OFFSET_OPEN else\
                        -priceTraded if trade.direction == DIRECTION_SHORT and trade.offset == OFFSET_OPEN else 0
        self.strategy.onTrade(copy.copy(trade))
        self.tradeList.append(copy.copy(trade.__dict__))
        # 记录盈亏
        if self.dealOpen == 0:
            if not self.deal == 0:
                self.openPrice =  self.lastOpen.pop() if self.lastOpen else self.openPrice
                size = self.size[self.symbolMap[self.strategy.vtSymbol]]
                turnover = (abs(self.deal)+abs(self.openPrice))*size
                commission = turnover*self.rate[self.symbolMap[self.strategy.vtSymbol]]
                self.pnl += (-self.deal-self.openPrice)* size - commission
        else:
            self.lastOpen.insert(0,self.dealOpen)
        # 快照市场，用于计算持仓盈亏，暂不支持
        # self.snapMarket(tradeID)
        self.tradeDict[trade.vtSymbol][tradeID] = trade

    #----------------------------------------------------------------------
    def updateLimitOrder(self,symbol):
        """基于最新数据撮合限价单"""
        # 遍历限价单字典中的所有限价单
        tick = self.tick.get(symbol)
        for orderID, order in self.workingLimitOrderDict.items():
            if order.vtSymbol == symbol:
                buyCrossPrice  = tick.askPrice1 if tick.askPrice1 > 0 else tick.bidPrice1+self.mPrice.get(symbol)
                sellCrossPrice = tick.bidPrice1 if tick.bidPrice1 > 0 else tick.askPrice1-self.mPrice.get(symbol)
                buyCross  = order.direction==DIRECTION_LONG  and order.price>=buyCrossPrice
                sellCross = order.direction==DIRECTION_SHORT and order.price<=sellCrossPrice
                if not orderID in self.orderPrice and not (buyCross or sellCross):
                    self.orderPrice[orderID] = order.price


    #----------------------------------------------------------------------
    def crossStopOrder(self,symbol):
        """基于最新数据撮合停止单"""
        tick     = self.tick.get(symbol)
        lasttick = self.lasttick.get(symbol)
        bar      = self.bar.get(symbol)
        lastbar  = self.lastbar.get(symbol)

        # 先确定会撮合成交的价格，这里和限价单规则相反
        if self.mode == self.BAR_MODE:
            buyCrossPrice  = bar.high   # 若买入方向停止单价格低于该价格，则会成交
            sellCrossPrice = bar.low    # 若卖出方向限价单价格高于该价格，则会成交
            bestCrossPrice = bar.open   # 最优成交价，买入停止单不能低于，卖出停止单不能高于
        else:
            buyCrossPrice  = tick.lastPrice
            sellCrossPrice = tick.lastPrice
            bestCrossPrice = tick.lastPrice
        
        # 遍历停止单字典中的所有停止单
        for stopOrderID, so in self.workingStopOrderDict.items():
            if so.vtSymbol == symbol:
                # 判断是否会成交
                buyCross  = so.direction==DIRECTION_LONG and so.price < buyCrossPrice
                sellCross = so.direction==DIRECTION_SHORT and so.price > sellCrossPrice
                
                # 如果发生了成交
                if buyCross or sellCross:
                    # 计算成交价和成交量
                    priceTraded  = so.price
                    volumeTraded = so.totalVolume - so.tradedVolume

                    # 推送委托回报
                    self.strategyOnOrder(so, volumeTraded)
                    # 推送成交回报
                    self.strategyOnTrade(so, volumeTraded, priceTraded)

                    if stopOrderID in self.workingStopOrderDict:
                        del self.workingStopOrderDict[stopOrderID]                        

                    self.strategy.onStopOrder(so)


    #----------------------------------------------------------------------
    def crossLimitOrder(self,symbol):
        """基于最新数据撮合限价单"""
        # 缓存数据
        tick     = self.tick.get(symbol)
        lasttick = self.lasttick.get(symbol)
        bar      = self.bar.get(symbol)
        lastbar  = self.lastbar.get(symbol)
        # 过滤数据
        if self.filterTradeTime(tick,bar):
            return

        # 确定成交判定价格
        if self.mode == self.BAR_MODE:
            # Bar价格撮合，目前不支持Fok,Fak
            buyCrossPrice  = bar.low+self.mPrice.get(symbol,0.01)    # 若买入方向限价单价格高于该价格，则会成交
            sellCrossPrice = bar.high-self.mPrice.get(symbol,0.01)   # 若卖出方向限价单价格低于该价格，则会成交
        else:
            # Tick采用对价撮合，支持Fok，Fak
            buyCrossPrice  = tick.askPrice1 if tick.askPrice1 > 0 else tick.bidPrice1+self.mPrice.get(symbol)
            sellCrossPrice = tick.bidPrice1 if tick.bidPrice1 > 0 else tick.askPrice1-self.mPrice.get(symbol)
        
        # 遍历限价单字典中的所有限价单
        for orderID, order in self.workingLimitOrderDict.items():
            if order.vtSymbol == symbol:
                # 判断是否会成交
                buyCross  = order.direction==DIRECTION_LONG  and order.price>=buyCrossPrice
                sellCross = order.direction==DIRECTION_SHORT and order.price<=sellCrossPrice

                # 如果首次挂入，并且可以对价撮合（避免限价单获得更有利的价格）
                if (buyCross or sellCross) and (not orderID in self.orderPrice):
                    # 计算成交量
                    volumeTraded = (order.totalVolume-order.tradedVolume) 
                    if self.mode == self.TICK_MODE:
                        volumeTraded = min(volumeTraded, tick.askVolume1) if buyCross \
                                  else min(volumeTraded, tick.bidVolume1)
                    elif self.mode == self.BAR_MODE:
                        volumeTraded = min(volumeTraded, bar.volume)
                    volumeTraded = max(volumeTraded,1)

                    # 计算成交价
                    if self.mode==self.BAR_MODE:
                        priceTraded = min(order.price,bar.open) if buyCross \
                                 else max(order.price,bar.open)
                    else:
                        priceTraded = min(order.price,buyCrossPrice) if buyCross \
                                 else max(order.price,sellCrossPrice)

                    # 推送委托回报
                    self.strategyOnOrder(order,volumeTraded)
                    # 推送成交回报
                    self.strategyOnTrade(order,volumeTraded,priceTraded)

                # 立即成交订单，未成交直接撤销
                elif not order.priceType == PRICETYPE_LIMITPRICE:
                    self.strategyOnOrder(order,0)

                # 模拟排队撮合部分，TICK模式有效（使用Tick内成交均价简单估计两边盘口的成交量）
                elif self.mode == self.TICK_MODE and not self.fast:

                    # 计算估计的两边盘口的成交量
                    volOnBid,volOnAsk,pOnBid,pOnAsk = self.calcTickVolume(tick, lasttick, self.size.get(symbol,1))

                    # 排队队列维护
                    # 跳空并且对价能成交
                    if (buyCross or sellCross) and tick.volume > lasttick.volume:
                        self.orderVolume[orderID] = 0
                    # 非首次进入队列
                    elif orderID in self.orderPrice and tick.volume > lasttick.volume:
                        # 标记首先排队进入(不允许直接在买卖盘中间成交)
                        if orderID not in self.orderVolume: 
                            if order.price == tick.bidPrice1 and order.direction==DIRECTION_LONG:
                                self.orderVolume[orderID] = tick.bidVolume1 
                            elif order.price == tick.bidPrice2 and order.direction==DIRECTION_LONG and bidVolume2 > 0:
                                self.orderVolume[orderID] = tick.bidVolume2 
                            elif order.price == tick.bidPrice3 and order.direction==DIRECTION_LONG and bidVolume3 > 0:
                                self.orderVolume[orderID] = tick.bidVolume3 
                            elif order.price == tick.bidPrice4 and order.direction==DIRECTION_LONG and bidVolume4 > 0:
                                self.orderVolume[orderID] = tick.bidVolume4 
                            elif order.price == tick.bidPrice5 and order.direction==DIRECTION_LONG and bidVolume5 > 0:
                                self.orderVolume[orderID] = tick.bidVolume5 
                            elif order.price == tick.askPrice1 and order.direction==DIRECTION_SHORT:
                                self.orderVolume[orderID] = tick.askVolume1                         
                            elif order.price == tick.askPrice2 and order.direction==DIRECTION_SHORT and askVolume2 > 0:
                                self.orderVolume[orderID] = tick.askVolume2                         
                            elif order.price == tick.askPrice3 and order.direction==DIRECTION_SHORT and askVolume3 > 0:
                                self.orderVolume[orderID] = tick.askVolume3                         
                            elif order.price == tick.askPrice4 and order.direction==DIRECTION_SHORT and askVolume4 > 0:
                                self.orderVolume[orderID] = tick.askVolume4                         
                            elif order.price == tick.askPrice5 and order.direction==DIRECTION_SHORT and askVolume5 > 0:
                                self.orderVolume[orderID] = tick.askVolume5
                        # 首先排队进入，然后被打穿
                        elif (order.price > sellCrossPrice and order.direction==DIRECTION_LONG) or\
                             (order.price < buyCrossPrice  and order.direction==DIRECTION_SHORT):
                            self.orderVolume[orderID] = 0
                        # 更新排队值
                        elif order.price == pOnBid and order.direction==DIRECTION_LONG:
                            self.orderVolume[orderID] -= volOnBid
                        elif order.price == pOnAsk and order.direction==DIRECTION_SHORT:
                            self.orderVolume[orderID] -= volOnAsk
                    # 首次进入队列
                    elif not orderID in self.orderPrice:
                        self.orderPrice[orderID] = order.price
                        if order.price == tick.bidPrice1 and order.direction==DIRECTION_LONG:
                            self.orderVolume[orderID] = tick.bidVolume1 
                        elif order.price == tick.bidPrice2 and order.direction==DIRECTION_LONG and bidVolume2 > 0:
                            self.orderVolume[orderID] = tick.bidVolume2                                            
                        elif order.price == tick.bidPrice3 and order.direction==DIRECTION_LONG and bidVolume3 > 0:
                            self.orderVolume[orderID] = tick.bidVolume3                                            
                        elif order.price == tick.bidPrice4 and order.direction==DIRECTION_LONG and bidVolume4 > 0:
                            self.orderVolume[orderID] = tick.bidVolume4                                            
                        elif order.price == tick.bidPrice5 and order.direction==DIRECTION_LONG and bidVolume5 > 0:
                            self.orderVolume[orderID] = tick.bidVolume5 
                        elif order.price == tick.askPrice1 and order.direction==DIRECTION_SHORT:
                            self.orderVolume[orderID] = tick.askVolume1
                        elif order.price == tick.askPrice2 and order.direction==DIRECTION_SHORT and askVolume2 > 0:
                            self.orderVolume[orderID] = tick.askVolume2                         
                        elif order.price == tick.askPrice3 and order.direction==DIRECTION_SHORT and askVolume3 > 0:
                            self.orderVolume[orderID] = tick.askVolume3                         
                        elif order.price == tick.askPrice4 and order.direction==DIRECTION_SHORT and askVolume4 > 0:
                            self.orderVolume[orderID] = tick.askVolume4                         
                        elif order.price == tick.askPrice5 and order.direction==DIRECTION_SHORT and askVolume5 > 0:
                            self.orderVolume[orderID] = tick.askVolume5

                    # 排队成交，注意，目前简单一次性全部成交！！
                    if orderID in self.orderVolume and self.orderVolume[orderID] <= 0:

                        # 计算成交价和成交量
                        priceTraded  = order.price
                        volumeTraded = order.totalVolume - order.tradedVolume

                        # 推送委托回报
                        self.strategyOnOrder(order, volumeTraded)
                        # 推送成交回报
                        self.strategyOnTrade(order, volumeTraded, priceTraded)
                    
                        # 从字典中删除该限价单
                        self.removeOrder(orderID)

    #----------------------------------------------------------------------
    def insertData(self, dbName, collectionName, data):
        """考虑到回测中不允许向数据库插入数据，防止实盘交易中的一些代码出错"""
        pass
    
    #----------------------------------------------------------------------
    def writeCtaLog(self, content):
        """记录日志"""
        log = str(self.dt) + ' ' + content 
        self.logList.append(log)
        
    #----------------------------------------------------------------------
    def output(self, content):
        """输出内容"""
        self.logList.append(str(content))
        if self.plotfile:
            print content.encode('utf8')
        elif self.plot:
            print content

    #----------------------------------------------------------------------
    def crossTrade2PNL(self, dict_trade, pnlDict, resList):
        """逐比对冲成交回报"""
        longTrade = deque([])        # 未平仓的多头交易
        shortTrade = deque([])       # 未平仓的空头交易
        for trade in dict_trade.values():
            symbol = trade.vtSymbol
            # 多头交易
            if trade.direction == DIRECTION_LONG:
                # 当前多头交易为平空
                untraded = True
                while (shortTrade and untraded):
                    entryTrade = shortTrade[0]
                    exitTrade = trade
                    # 计算比例佣金
                    volume = min(entryTrade.volume,exitTrade.volume)
                    entryTrade.volume = entryTrade.volume-volume
                    exitTrade.volume = exitTrade.volume-volume
                    if entryTrade.volume == 0:
                        shortTrade.popleft()
                    if exitTrade.volume == 0:
                        untraded = False
                    if exitTrade.dt not in pnlDict:
                        pnlDict[exitTrade.dt] = TradingResult(entryTrade.price, entryTrade.dt, exitTrade.price,
                                exitTrade.dt,-volume, self.rate[self.symbolMap[symbol]], self.slippage, self.size[self.symbolMap[symbol]])
                        pnl = pnlDict[exitTrade.dt].pnl
                    else:
                        pnlDict[exitTrade.dt].add(entryTrade.price, entryTrade.dt, exitTrade.price, 
                                exitTrade.dt,-volume, self.rate[self.symbolMap[symbol]], self.slippage, self.size[self.symbolMap[symbol]])
                        pnl = pnlDict[exitTrade.dt].pnl
                # 如果尚无空头交易
                if untraded:
                    longTrade.append(trade)
                    
            # 空头交易        
            else:
                # 当前空头交易为平多
                untraded=True
                while (longTrade and untraded):
                    entryTrade = longTrade[0]
                    exitTrade = trade
                    # 计算比例佣金
                    volume = min(entryTrade.volume,exitTrade.volume)
                    entryTrade.volume = entryTrade.volume-volume
                    exitTrade.volume = exitTrade.volume-volume
                    if entryTrade.volume == 0:
                        longTrade.popleft()
                    if exitTrade.volume == 0:
                        untraded = False
                    if exitTrade.dt not in pnlDict:
                        pnlDict[exitTrade.dt] = TradingResult(entryTrade.price, entryTrade.dt,exitTrade.price,
                                exitTrade.dt, volume, self.rate[self.symbolMap[symbol]], self.slippage, self.size[self.symbolMap[symbol]])
                        pnl = pnlDict[exitTrade.dt].pnl
                    else:
                        pnlDict[exitTrade.dt].add(entryTrade.price, entryTrade.dt,exitTrade.price,
                                exitTrade.dt, volume, self.rate[self.symbolMap[symbol]], self.slippage, self.size[self.symbolMap[symbol]])
                        pnl = pnlDict[exitTrade.dt].pnl
                # 如果尚无多头交易
                if untraded:
                    shortTrade.append(trade)
        # 计算剩余持仓盈亏
        while (shortTrade):
            entryTrade = shortTrade.popleft()
            volume = entryTrade.volume
            symbol = entryTrade.vtSymbol
            if self.mode == self.TICK_MODE:
                exitTime = self.tick[symbol].datetime
                exitPrice = self.tick[symbol].askPrice1
            else:
                exitTime = self.bar[symbol].datetime
                exitPrice = self.bar[symbol].close
            if exitTime not in pnlDict:
                pnlDict[exitTime] = TradingResult(entryTrade.price, entryTrade.dt, exitPrice, exitTime,
                    -volume, self.rate[self.symbolMap[symbol]], self.slippage, self.size[self.symbolMap[symbol]])
                pnl = pnlDict[exitTime].pnl
            else:
                pnlDict[exitTime].add(entryTrade.price, entryTrade.dt, exitPrice, exitTime,
                    -volume, self.rate[self.symbolMap[symbol]], self.slippage, self.size[self.symbolMap[symbol]])
                pnl = pnlDict[exitTime].pnl
        while (longTrade):
            entryTrade = longTrade.popleft()
            volume = entryTrade.volume
            symbol = entryTrade.vtSymbol
            if self.mode == self.TICK_MODE:
                exitTime = self.tick[symbol].datetime
                exitPrice = self.tick[symbol].bidPrice1
            else:
                exitTime = self.bar[symbol].datetime
                exitPrice = self.bar[symbol].close

            if exitTime not in pnlDict:
                pnlDict[exitTime] = TradingResult(entryTrade.price, entryTrade.dt, exitPrice, exitTime,
                    volume, self.rate[self.symbolMap[symbol]], self.slippage, self.size[self.symbolMap[symbol]])
                pnl = pnlDict[exitTime].pnl
            else:
                pnlDict[exitTime].add(entryTrade.price, entryTrade.dt,exitPrice, exitTime,
                    volume, self.rate[self.symbolMap[symbol]], self.slippage, self.size[self.symbolMap[symbol]])
                pnl = pnlDict[exitTime].pnl

        return pnlDict,resList


    #----------------------------------------------------------------------
    def calculateBacktestingResult(self, detial = False):
        """
        计算回测结果
        """
        self.output(u'按逐笔对冲计算回测结果')
        # 首先基于回测后的成交记录，计算每笔交易的盈亏
        pnlDict = OrderedDict()      # 每笔盈亏的记录 
        resList = [{"name":self.strategy.name}]
        
        # 计算滑点，一个来回包括两次
        totalSlippage = self.slippage * 2 
        for symbol in self.tradeDict:
            self.output(u'合约%s 总交易量 : %d' %(symbol,len(self.tradeDict[symbol])))

        for symbol in self.tradeDict:
            pnlDict,resList = self.crossTrade2PNL(self.tradeDict[symbol],pnlDict,resList)


        # 由于多合约的问题，需要整理时间序列和结果序列
        timeList = []
        resultList = []
        pnlDict0 = sorted(pnlDict.iteritems(),key=lambda d:d[0])
        for k,v in pnlDict0:
            timeList.append(k)
            resultList.append(v)

        # 然后基于每笔交易的结果，我们可以计算具体的盈亏曲线和最大回撤等        
        timeList = []           # 时间序列
        pnlList = []            # 每笔盈亏序列
        capital = 0             # 资金
        maxCapital = 0          # 资金最高净值
        drawdown = 0            # 回撤
        
        totalResult = 0         # 总成交数量
        totalTurnover = 0       # 总成交金额（合约面值）
        totalCommission = 0     # 总手续费
        totalSlippage = 0       # 总滑点
        
        capitalList = []        # 盈亏汇总的时间序列
        drawdownList = []       # 回撤的时间序列
        
        winningResult = 0       # 盈利次数
        losingResult = 0        # 亏损次数        
        totalWinning = 0        # 总盈利金额        
        totalLosing = 0         # 总亏损金额        
        
        for result in resultList:
            capital += result.pnl
            maxCapital = max(capital+result.posPnl, maxCapital)
            drawdown = round(capital+result.posPnl-maxCapital,2)
            
            pnlList.append(result.pnl)
            # 交易的时间戳使用平仓时间
            timeList.append(result.exitDt)
            capitalList.append(capital+result.posPnl)
            drawdownList.append(drawdown)
            
            totalResult += 1
            totalTurnover += result.turnover
            totalCommission += result.commission
            totalSlippage += result.slippage
            
            if result.pnl >= 0:
                winningResult += 1
                totalWinning += result.pnl
            else:
                losingResult += 1
                totalLosing += result.pnl
                
        # 计算盈亏相关数据
        averageWinning  = 0
        averageLosing   = 0
        profitLossRatio = 0
        winningRate     = 0 if totalResult==0 else winningResult*1.0/totalResult*100
        averageWinning  = 0 if winningResult==0 else totalWinning/winningResult
        averageLosing   = 0 if losingResult==0 else totalLosing/losingResult
        profitLossRatio = 0 if averageLosing==0 else -averageWinning/averageLosing 

        # 返回回测结果
        d = {}
        d['name']            = self.strategy.name
        d['capital']         = round(capital,2)
        d['maxCapital']      = maxCapital
        d['drawdown']        = drawdown
        d['totalResult']     = round(totalResult,2)
        d['totalTurnover']   = round(totalTurnover,2)
        d['totalCommission'] = round(totalCommission,2)
        d['totalSlippage']   = round(totalSlippage,2)
        d['timeList']        = timeList
        d['pnlList']         = pnlList
        d['capitalList']     = capitalList
        d['drawdownList']    = drawdownList
        d['winningRate']     = round(winningRate,2)
        d['averageWinning']  = round(averageWinning,2)
        d['averageLosing']   = round(averageLosing,2)
        d['profitLossRatio'] = round(profitLossRatio,2)
        d['resList']         = resList
        d['datas']           = self.datas if self.savedata else None

        return d

    #----------------------------------------------------------------------
    def showBacktestingResult(self,d=None):
        """
        显示回测结果
        """
        d = self.calculateBacktestingResult() if d is None else d
        with open('log\{}.log'.format(self.strategy.name),'wb') as f:
            for content in self.logList:
                f.write(content+'\n')
        if len(self.tradeList) > 0:
            pd.DataFrame(self.tradeList).set_index('dt').to_csv('trade\{}.csv'.format(self.strategy.name),encoding="gbk")
        showBtResult(d)

    #----------------------------------------------------------------------
    def showBacktestingResult_nograph(self,d=None):
        """
        显示回测结果
        """
        import numpy as np
        d = self.calculateBacktestingResult() if d is None else d
        with open('log\{}.log'.format(self.strategy.name),'wb') as f:
            for content in self.logList:
                f.write(content+'\n')
        if len(self.tradeList) > 0:
            pd.DataFrame(self.tradeList).set_index('dt').to_csv('trade\{}.csv'.format(self.strategy.name),encoding="gbk")

        # 记录日盈亏数据到数据库
        name = d.get('name')
        timeList = d['timeList']
        pnlList = d['pnlList']
        capitalList = d['capitalList']
        drawdownList = d['drawdownList']
        
        print(u'显示回测结果')
        # 输出
        if len(timeList)>0:
            print('-' * 30)
            print(u'第一笔交易：\t%s' % d['timeList'][0])
            print(u'最后一笔交易：\t%s' % d['timeList'][-1])
            
            print(u'总交易次数：\t%s' % formatNumber(d['totalResult']))        
            print(u'总盈亏：\t%s' % formatNumber(d['capital']))
            print(u'最大回撤: \t%s' % formatNumber(min(d['drawdownList'])))                
            print(u'最大盈利: \t%s' % formatNumber(max(d['pnlList'])))                
            print(u'最大亏损: \t%s' % formatNumber(min(d['pnlList'])))                
            
            print(u'平均每笔盈亏：\t%s' %formatNumber(d['capital']/d['totalResult']))
            print(u'平均每笔滑点：\t%s' %formatNumber(d['totalSlippage']/d['totalResult']))
            print(u'平均每笔佣金：\t%s' %formatNumber(d['totalCommission']/d['totalResult']))

            print(u'盈亏标准差: \t%s' % formatNumber(np.std(d['drawdownList'])))                
            print(u'回撤标准差: \t%s' % formatNumber(np.std(d['pnlList'])))                

            print(u'盈亏中位数: \t%s' % formatNumber(np.median(d['drawdownList'])))                
            print(u'回撤中位数: \t%s' % formatNumber(np.median(d['pnlList'])))                
            
            print(u'胜率\t\t%s%%' %formatNumber(d['winningRate']))
            print(u'平均每笔盈利\t%s' %formatNumber(d['averageWinning']))
            print(u'平均每笔亏损\t%s' %formatNumber(d['averageLosing']))
            print(u'盈亏比：\t%s' %formatNumber(d['profitLossRatio']))

            # 资金曲线插入数据库,用于组合回测
            lastTime = None
            lastCap = 0
            lastDayCap = 0
            lastDraw = 0
            time0 = timeList[0]
            time1 = timeList[-1]
            name  = name.split('.')[-1]
            deleteCap(CAPITAL_DB_NAME,name,{})
            for (time,cap,drawdown) in zip(timeList,capitalList,drawdownList):
                if lastTime and time.day != lastTime.day: 
                    capData          = CtaCapData()
                    capData.name     = name
                    capData.start    = ''
                    capData.cap      = lastCap
                    capData.datetime = lastTime
                    capData.pnl      = lastCap - lastDayCap
                    capData.drawdown = lastDraw
                    capData.date     = capData.datetime.replace(hour =0,minute=0,\
                                       second = 0,microsecond = 0)
                    insertCap(CAPITAL_DB_NAME,name,capData)
                    lastDayCap = lastCap
                lastTime = time
                lastCap = cap
                lastDraw = drawdown
    
    #----------------------------------------------------------------------
    def putStrategyEvent(self, name):
        """发送策略更新事件，回测中忽略"""
        self.dataProduced() if self.savedata else None

    #----------------------------------------------------------------------
    def getState(self):
        strategy = self.strategy
        varDict = OrderedDict()
        for key in strategy.varList:
            try:
                varDict[key] = float(strategy.__getattribute__(key))
            except:
                varDict[key] = strategy.__getattribute__(key)
        return varDict

    #----------------------------------------------------------------------
    def confSettle(self, name):
        """确认结算单，回测中忽略"""
        pass

    #----------------------------------------------------------------------
    def setSlippage(self, slippage):
        """设置滑点"""
        self.slippage = slippage
        
    #----------------------------------------------------------------------
    def setSize(self, size):
        """设置合约大小"""
        self.size = size
        
    #----------------------------------------------------------------------
    def setRate(self, rate):
        """设置佣金比例"""
        self.rate = rate
        
    #----------------------------------------------------------------------
    def setLeverage(self, leverage):
        """设置杠杆比率"""
        self.leverage = leverage

    #----------------------------------------------------------------------
    def setPrice(self, price):
        """设置合约大小"""
        self.mPrice = price

    #----------------------------------------------------------------------
    def loadTick(self, dbName, collectionName, days):
        """从数据库中读取Tick数据，startDate是datetime对象"""
        startDate = self.dataStartDate
        
        d = {'datetime':{'$lte':startDate}}
        host, port = loadMongoSetting()
        client = pymongo.MongoClient(host,port)
        collection = client[dbName][collectionName]

        cursor = collection.find(d).limit(days*10*60*120)

        l = []
        if cursor:
            for d in cursor:
                tick = CtaTickData()
                tick.__dict__ = d
                l.append(tick)
        
        return l    

    #----------------------------------------------------------------------
    def loadBar(self, dbName, collectionName, days):
        """从数据库中读取Tick数据，startDate是datetime对象"""
        startDate = self.dataStartDate
        
        d = {'datetime':{'$lte':startDate}}
        host, port = loadMongoSetting()
        client = pymongo.MongoClient(host,port)
        collection = client[dbName][collectionName]

        cursor = collection.find(d).limit(days*10*60)

        l = []
        if cursor:
            for d in cursor:
                bar = CtaBarData()
                bar.__dict__ = d
                l.append(bar)
        
        return l    

    #----------------------------------------------------------------------
    def clearBacktestingResult(self):
        """清空之前回测的结果"""
        # 交易行情相关
        self.dt = None
        self.backtestingData = {}
        self.tick = {}
        self.bar = {}
        self.lasttick = {}

        self.logList = []
        self.dataBar = []
        self.dataState = []
        self.dataDeal = []
        self.dataDealOpen = []

        # 清空限价单相关
        self.limitOrderCount = 0
        self.limitOrderDict.clear()
        self.workingLimitOrderDict.clear()        
        self.orderPrice = {}
        self.orderVolume = {}
        
        # 清空停止单相关
        self.stopOrderCount = 0
        self.stopOrderDict.clear()
        self.workingStopOrderDict.clear()
        
        # 清空成交相关
        self.tradeCount = 0
        self.tradeDict.clear()
        self.tradeSnap.clear()
        

########################################################################
class TradingResult(object):
    """每笔交易的结果"""

    #----------------------------------------------------------------------
    def __init__(self, entryPrice, entryDt, exitPrice, 
                 exitDt, volume, rate, slippage, size):
        """Constructor"""
        self.entryPrice = entryPrice    # 开仓价格
        self.exitPrice = exitPrice      # 平仓价格
        
        self.entryDt = entryDt          # 开仓时间
        self.exitDt = exitDt            # 平仓时间
        self.volume = volume            # 交易数量（+/-代表方向）
        
        self.turnover = (self.entryPrice+self.exitPrice)*size*abs(volume)   # 成交金额
        self.commission = self.turnover*rate                                # 手续费成本
        self.slippage = slippage*2*size*abs(volume)                         # 滑点成本
        self.pnl = ((self.exitPrice - self.entryPrice) * volume * size 
                    - self.commission - self.slippage)                      # 净盈亏
        self.posPnl = 0                                                     # 当时持仓盈亏

    #----------------------------------------------------------------------
    def add(self, entryPrice, entryDt, exitPrice, 
                 exitDt, volume, rate, slippage, size):
        """Constructor"""
        self.entryPrice = entryPrice    # 开仓价格
        self.exitPrice = exitPrice      # 平仓价格
        
        self.entryDt = entryDt          # 开仓时间datetime    
        self.exitDt = exitDt            # 平仓时间
        self.volume += volume           # 交易数量（+/-代表方向）
        
        turnover = (self.entryPrice+self.exitPrice)*size*abs(volume)   
        self.turnover += turnover                                           # 成交金额
        commission = turnover*rate
        self.commission += commission                                       # 手续费成本
        slippage0 = slippage*2*size*abs(volume)                         
        self.slippage += slippage0                                          # 滑点成本
        self.pnl += ((self.exitPrice - self.entryPrice) * volume * size 
                    - commission - slippage0)                               # 净盈亏


########################################################################
class OptimizationSetting(object):
    """优化设置"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.paramDict = OrderedDict()
        self.optimizeTarget = ''        # 优化目标字段
        
    #----------------------------------------------------------------------
    def addParameter(self, name, start, end, step):
        """增加优化参数"""
        if end <= start:
            print u'参数起始点必须小于终止点'
            return
        
        if step <= 0:
            print u'参数步进必须大于0'
            return
        
        l = []
        param = start
        
        while param <= end:
            l.append(param)
            param += step
        
        self.paramDict[name] = l
        
    #----------------------------------------------------------------------
    def generateSetting(self):
        """生成优化参数组合"""
        # 参数名的列表
        nameList = self.paramDict.keys()
        paramList = self.paramDict.values()
        
        # 使用迭代工具生产参数对组合
        productList = list(product(*paramList))
        
        # 把参数对组合打包到一个个字典组成的列表中
        settingList = []
        for p in productList:
            d = dict(zip(nameList, p))
            settingList.append(d)
    
        return settingList
    
    #----------------------------------------------------------------------
    def setOptimizeTarget(self, target):
        """设置优化目标字段"""
        self.optimizeTarget = target

#----------------------------------------------------------------------
def deleteCap(dbName, collectionName, d):
    """插入数据到数据库（这里的data可以是CtaTickData或者CtaBarData）"""
    host, port = loadMongoSetting()
    dbClient = pymongo.MongoClient(host, port, socketKeepAlive=True)
    db = dbClient[dbName]
    collection = db[collectionName]
    collection.remove({})

#----------------------------------------------------------------------
def insertCap(dbName, collectionName, d):
    """插入数据到数据库（这里的data可以是CtaTickData或者CtaBarData）"""
    host, port = loadMongoSetting()
    dbClient = pymongo.MongoClient(host, port, socketKeepAlive=True)
    db = dbClient[dbName]
    collection = db[collectionName]
    collection.ensure_index([('date', pymongo.ASCENDING)], unique=True)   
    flt = {'date': d.date}
    collection.update_one(flt, {'$set':d.__dict__}, upsert=True)  

#----------------------------------------------------------------------
def showBtResult(d,filepath=None):
    """
    显示回测结果
    """
    name = d.get('name')
    timeList = d['timeList']
    pnlList = d['pnlList']
    capitalList = d['capitalList']
    drawdownList = d['drawdownList']
    

    print(u'显示回测结果')
    # 输出
    if len(timeList)>0:
        print('-' * 30)
        print(u'第一笔交易：\t%s' % d['timeList'][0])
        print(u'最后一笔交易：\t%s' % d['timeList'][-1])
        
        print(u'总交易次数：\t%s' % formatNumber(d['totalResult']))        
        print(u'总盈亏：\t%s' % formatNumber(d['capital']))
        print(u'最大回撤: \t%s' % formatNumber(min(d['drawdownList'])))                
        
        print(u'平均每笔盈亏：\t%s' %formatNumber(d['capital']/d['totalResult']))
        print(u'平均每笔滑点：\t%s' %formatNumber(d['totalSlippage']/d['totalResult']))
        print(u'平均每笔佣金：\t%s' %formatNumber(d['totalCommission']/d['totalResult']))
        
        print(u'胜率\t\t%s%%' %formatNumber(d['winningRate']))
        print(u'平均每笔盈利\t%s' %formatNumber(d['averageWinning']))
        print(u'平均每笔亏损\t%s' %formatNumber(d['averageLosing']))
        print(u'盈亏比：\t%s' %formatNumber(d['profitLossRatio']))
        print(u'显示回测结果')

        # 绘图
        import matplotlib.pyplot as plt
        plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文标签
        plt.rcParams['axes.unicode_minus']=False #用来正常显示负号
        from matplotlib.dates import AutoDateLocator, DateFormatter  
        autodates = AutoDateLocator()  
        yearsFmt = DateFormatter('%y-%m-%d')  
                
        pCapital = plt.subplot(3, 1, 1)
        #pCapital.set_ylabel("capital")
        pCapital.set_ylabel(u'资金')
        pCapital.plot(timeList,capitalList)
        plt.gcf().autofmt_xdate()        #设置x轴时间外观  
        plt.gcf().subplots_adjust(bottom=0.3)
        plt.gca().xaxis.set_major_locator(autodates)       #设置时间间隔  
        plt.gca().xaxis.set_major_formatter(yearsFmt)      #设置时间显示格式  
                
        pDD = plt.subplot(3, 1, 2)
        #pDD.set_ylabel("dd")
        pDD.set_ylabel(u'回撤')
        pDD.bar(range(len(drawdownList)), drawdownList)         
        
        pPnl = plt.subplot(3, 1, 3)
        #pPnl.set_ylabel("pnl")
        pPnl.set_ylabel(u'盈亏统计')
        pPnl.hist(pnlList, bins=20)

        if filepath is None:
            plt.subplots_adjust(bottom=0.05,hspace=0.3)
            plt.show()
        else:
            plt.savefig(filepath)
            plt.close()
    
#----------------------------------------------------------------------
def runParallelOptimization(setting_c, optimizationSetting, optimism=False, startTime='', endTime='', slippage=0,mode='T'):
    """并行优化参数"""
    # 获取优化设置        
    global p
    global currentP 
    print(u'开始优化策略 : '+setting_c['name'])
    settingList = optimizationSetting.generateSetting()
    print(u'总共'+str(len(settingList))+u'个优化')
    targetName = optimizationSetting.optimizeTarget
    p = ProgressBar(maxval=len(settingList))
    p.start()
    currentP=0
    # 检查参数设置问题
    if not settingList or not targetName:
        print(u'优化设置有问题，请检查')
    
    # 多进程优化，启动一个对应CPU核心数量的进程池
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count()-1)
    l = []
    for setting in settingList:
        l.append(pool.apply_async(optimize,args=(setting_c,setting,startTime,endTime,slippage,optimism,mode),callback=showProcessBar))
    pool.close()
    pool.join()
    p.finish()
    
    # 显示结果
    resultList = [res.get() for res in l]
    print('-' * 30)
    print(u'优化结果：')
    filepath = '.\\opResults\\'
    with open(filepath+setting_c['name']+'.csv','wb') as csvfile:
        fieldnames = resultList[0][1].keys()
        fieldnames.sort()
        writer = csv.DictWriter(csvfile,fieldnames)
        writer.writeheader()
        setting_t = {}
        value_t = -99999
        for (setting,opDict) in resultList:
            writer.writerow(opDict)
            if opDict[targetName] > value_t:
                setting_t = setting 
                value_t = opDict[targetName]
                print(str(setting_t)+':'+str(value_t))    
    print(u'优化结束')
    print(u' ')
    return (setting_t,value_t)
    
#----------------------------------------------------------------------
def showProcessBar(result):
    """显示进度条"""
    global p
    global currentP 
    currentP+=1
    p.update(currentP)

#----------------------------------------------------------------------
def getSetting(name):
    """获取策略基础配置"""
    setting_c = {}
    settingFileName = '.\\json\\CTA_setting.json'
    with open(settingFileName) as f:
        l = json.load(f)
        for setting in l:
            if setting['name'] == name:
                setting_c = setting
    setting_c[u'backtesting'] = True
    return setting_c

#----------------------------------------------------------------------
def formatNumber(n):
    """格式化数字到字符串"""
    rn = round(n, 2)        # 保留两位小数
    return format(rn, ',')  # 加上千分符

#---------------------------------------------------------------------------------------
def getDbByMode(mode):
    """获取合约信息"""
    with open("./json/DATA_setting.json") as f:
        for setting in json.load(f):
             mode0 = setting[u'mode']
             if mode == mode0:
                 return setting[u'dbname']
    return "VnTrader_1Min_Db"

#---------------------------------------------------------------------------------------
def getSymbolInfo(symbolList):
    """获取合约信息"""
    import re
    rate  = {}
    price = {}
    size  = {}
    level = {}
    with open("./json/ContractInfo.json") as f:
        for setting in json.load(f):
             name = setting[u'name']
             for symbol in symbolList:
                match  = re.search('^'+name+'[0-9]',symbol)
                match0 = re.search('^'+name+'$',symbol)
                if match or match0:
                    rate[symbol]  = setting[u'mRate']
                    size[symbol]  = setting[u'mSize']
                    price[symbol] = setting[u'mPrice']
                    level[symbol] = setting[u'mLevel']

    for symbol in symbolList:
        if symbol not in rate:
            print(u'未找到%s合约手续费信息，按股票合约处理' %(symbol))
            rate[symbol]  = 0.0008
            size[symbol]  = 1
            level[symbol] = 1
            price[symbol] = 0.01
            # ETF合约有更小的最小价格变动，并且没有印花税
            if name[0:2]=='15':
                rate[symbol] = 0.00015
                size[symbol] = 100
                level[symbol] = 1
                price[symbol] = 0.001

    return rate,price,size,level
    
#---------------------------------------------------------------------------------------
def backtestingRolling(setting_c, optimizationSetting, StartTime = '', EndTime = '', RollingDays=20, slippage = 0, optimism = False, mode = 'T', savedata = False):
    """滚动优化回测"""
    import sys
    import ctaSetting
    reload(ctaSetting)
    className = setting_c[u'className']
    STRATEGY_CLASS = ctaSetting.STRATEGY_CLASS

    # 生成滚动回测序列
    dataStartDate = datetime.strptime(StartTime, '%Y%m%d') if len(StartTime) == 8\
                        else datetime.strptime(StartTime, '%Y%m%d %H:%M:%S')
    dataEndDate   = datetime.strptime(EndTime, '%Y%m%d') if len(EndTime) == 8\
                        else datetime.strptime(EndTime, '%Y%m%d %H:%M:%S')
    timeList = deque([])
    dataStepDate = dataStartDate
    while dataStepDate+timedelta(days=RollingDays) <= dataEndDate:
        dataStepDate += timedelta(days=RollingDays)
        timeList.append(dataStepDate)
    timeList.append(dataEndDate)

    symbolList = eval(str(setting_c[u'symbolList']))
    rate,price,size,level = getSymbolInfo(symbolList)

    engine=BacktestingEngine()
    engine.optimism = optimism
    engine.plot = True

    # 设置引擎的回测模式为TICK
    if mode[0] == 'T':
        engine.setBacktestingMode(engine.TICK_MODE)
    elif mode[0] == 'B':
        engine.setBacktestingMode(engine.BAR_MODE)
        engine.savedata = savedata
    dbName = getDbByMode(mode)

    StartTime = str(setting_c[u'StartTime']) if not StartTime else StartTime 
    if not EndTime:
        EndTime = str(setting_c[u'EndTime'])

    setting_c[u'backtesting'] = True

    # 设置产品相关参数
    engine.setSlippage(slippage)     # 滑点
    engine.setRate(rate)             # 手续费
    engine.setSize(size)             # 合约乘数    
    engine.setPrice(price)           # 最小价格变动    
    engine.setLeverage(level)        # 合约保证金    
    engine.initStrategy(STRATEGY_CLASS[className],setting_c)

    while timeList:
        # 设置回测用的数据起始日期
        if (not engine.dataStartDate is None) and (not engine.dataEndDate is None):
            setting_t,value_t = runParallelOptimization(setting_c, optimizationSetting, \
            optimism,engine.dataStartDate.strftime('%Y%m%d %H:%M:%S'), engine.dataEndDate.strftime('%Y%m%d %H:%M:%S'),\
            slippage, mode)
            print(u'使用参数: '+str(setting_t))
            engine.strategy.onUpdate(setting_t)
        engine.dataStartDate = dataStartDate
        dataStartDate = engine.dataEndDate = timeList.popleft()
        
        # 载入历史数据到引擎中
        engine.loadHistoryData(dbName, symbolList)
        engine.runBacktesting()

    engine.strategy.onStop()
    d = engine.calculateBacktestingResult()
    engine.showBacktestingResult(d)
    return setting_c,d

# C++回测
#---------------------------------------------------------------------------------------
def backtestingCpp(setting_c, StartTime = '', EndTime = '', slippage = 0, optimism = False, mode = 'T', savedata = False):
    """简单回测"""
    setting_c[u'backtesting'] = True
    import ctaSetting
    reload(ctaSetting)
    STRATEGY_CLASS = ctaSetting.STRATEGY_CLASS
    symbolList = eval(str(setting_c[u'symbolList']))
    rate,price,size,level = getSymbolInfo(symbolList)
    sp = dict([(s,slippage) for s in symbolList])

    # 设置引擎的回测模式为TICK
    if not mode == 'T':
        return setting_c,{}
    s = STRATEGY_CLASS[className](self, setting_c)
    s.setDataBase(TICK_DB_NAME,optimism)
    s.setTimeInfo(StartTime,EndTime)
    s.subScribeSymbols(symbolList)
    s.setSymbolSize(size)
    s.setSymbolPricetick(price)
    s.setSymbolFee(rate)
    s.setSymbolSlipage(sp)
    s.init()
    s.start()
    s.block()
    s.loadSetting(setting_c)
    d = s.calculateBacktestingResult()
    s.showBtResult(d)
    return setting_c,d

#---------------------------------------------------------------------------------------
def backtesting(setting_c, StartTime = '', EndTime = '', slippage = 0, optimism = False, mode = 'T', savedata = False):
    """简单回测"""
    setting_c[u'backtesting'] = True
    import ctaSetting
    reload(ctaSetting)
    className = setting_c[u'className']
    STRATEGY_CLASS = ctaSetting.STRATEGY_CLASS
    symbolList = eval(str(setting_c[u'symbolList']))
    rate,price,size,level = getSymbolInfo(symbolList)

    engine=BacktestingEngine()
    engine.optimism = optimism
    engine.plot = True

    if mode[0] == 'T':
        engine.setBacktestingMode(engine.TICK_MODE)
    elif mode[0] == 'B':
        engine.setBacktestingMode(engine.BAR_MODE)
        engine.savedata = savedata
    dbName = getDbByMode(mode)

    # 设置回测用的数据起始日期
    if not StartTime:
        StartTime = str(setting_c[u'StartTime'])
    if not EndTime:
        EndTime = str(setting_c[u'EndTime'])

    # 设置回测用的数据起始日期
    engine.setStartDate(StartTime,1)
    engine.setEndDate(EndTime)
    
    # 载入历史数据到引擎中
    engine.loadHistoryData(dbName, symbolList)

    # 设置产品相关参数
    engine.setSlippage(slippage)     # 滑点
    engine.setRate(rate)             # 手续费
    engine.setSize(size)             # 合约乘数    
    engine.setPrice(price)           # 最小价格变动    
    engine.setLeverage(level)        # 合约保证金    
    engine.initStrategy(STRATEGY_CLASS[className],setting_c)
    engine.runBacktesting()
    engine.strategy.onStop()
    d = engine.calculateBacktestingResult()
    engine.showBacktestingResult_nograph(d)
    return setting_c,d

#----------------------------------------------------------------------
def optimize(setting_c, setting,  startTime='', endTime='', slippage=0, optimism=False, mode = 'T'):
    """多进程优化时跑在每个进程中运行的函数"""
    try:
        from ctaBacktesting import BacktestingEngine
        setting_c[u'backtesting'] = True
        import ctaSetting
        reload(ctaSetting)
        className = setting_c[u'className']
        STRATEGY_CLASS = ctaSetting.STRATEGY_CLASS

        symbolList = eval(str(setting_c[u'symbolList']))
        rate,price,size,level = getSymbolInfo(symbolList)
            
        engine=BacktestingEngine()
        engine.plot = False
        engine.optimism = optimism

        # 设置引擎的回测模式为TICK
        if mode[0] == 'T':
            engine.setBacktestingMode(engine.TICK_MODE)
        elif mode[0] == 'B':
            engine.setBacktestingMode(engine.BAR_MODE)
            #engine.savedata = savedata
        dbName = getDbByMode(mode)
        
        # 设置回测用的数据起始日期
        if not startTime:
            startTime = str(setting_c[u'StartTime'])
        if not endTime:
            endTime = str(setting_c[u'EndTime'])

        # 设置回测用的数据起始日期
        engine.setStartDate(startTime,1)
        engine.setEndDate(endTime)
    
        # 载入历史数据到引擎中
        engine.loadHistoryData(dbName, symbolList)
        
        # 设置产品相关参数
        engine.setSlippage(slippage)   # 滑点
        engine.setRate(rate)           # 手续费
        engine.setSize(size)           # 合约大小    
        engine.setPrice(price)         # 最小价格变动     
        engine.setLeverage(level)      # 合约杠杆    
        setting_c.update(setting)
        engine.initStrategy(STRATEGY_CLASS[className], setting_c)
        engine.runBacktesting()
        engine.strategy.onStop()
        d = engine.calculateBacktestingResult()
        opResult = {}
        opResult.update(setting)
        opResult['totalResult']=d['totalResult']        
        opResult['capital']=round(d['capital'],2)
        if d['totalResult'] > 0:
            opResult['winPerT']=round(d['capital']/d['totalResult'],2)
            opResult['splipPerT']=round(d['totalSlippage']/d['totalResult'],2)
            opResult['commiPerT']=round(d['totalCommission']/d['totalResult'],2)
            opResult['maxDrawdown']=min(d['drawdownList'])                
        else:
            opResult['winPerT']=0
            opResult['splipPerT']=0
            opResult['commiPerT']=0
            opResult['maxDrawdown']=0
        opResult['winningRate']=round(d['winningRate'],2)
        opResult['averageLosing']=round(d['averageLosing'],2)
        opResult['averageWinning']=round(d['averageWinning'],2)
        opResult['profitLossRatio']=round(d['profitLossRatio'],2)
        return (setting,opResult)
    except Exception, e:
        print(u'回测策略出错：%s' %e)
        print 'traceback.print_exc():'; traceback.print_exc()
        return ({},{})

if __name__ == '__main__':
    # 建议使用ipython notebook或者spyder来做回测
    """读取策略配置"""
    begin = datetime.now()
    # 回测策略选择
    name = 'tl for rb'

    # 回测模式设置
    opt = False

    # 回测参数设置

    # 策略参数设置
    #optimizationSetting = OptimizationSetting()
    #optimizationSetting.addParameter('wLimit', 3, 6, 1)          

    # 确认检查
    print(u'即将开始优化回测，请确认下面的信息正确后开始回测：')
    print(u'1.回测引擎是正确的稳定版本')
    print(u'2.(乐观\悲观)模式选择正确')
    print(u'3.策略逻辑正确')
    print(u'4.策略参数初始化无遗漏')
    print(u'5.策略参数传递无遗漏')
    print(u'6.策略单次回测交割单检查正确')
    print(u'7.参数扫描区间合理')
    print(u'8.关闭结果文件')
    print(u'y/n:')
    choice = raw_input(u'')
    if not choice == 'y':
            exit(0)

    # 开始回测
    setting_c=getSetting(name)
    runParallelOptimization(setting_c,optimizationSetting,optimism=opt)
    end = datetime.now()
    print(end-begin)
    #outfile.close
