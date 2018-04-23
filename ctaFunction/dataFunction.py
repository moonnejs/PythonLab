# encoding: UTF-8
"""
包含一些为CTA因子提供数据的函数
"""
import json
import ctaBase
import pymongo
import pandas as pd
from ctaBase import *
from datetime import datetime

MAX_NUMBER = 10000000000000
MAX_DECIMAL = 4

#----------------------------------------------------------------------
def todayDate():
    """获取当前本机电脑时间的日期"""
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)    

#---------------------------------------------------------------------------------------
def getDbByMode(mode):
    """获取合约信息"""
    with open("./json/DATA_setting.json") as f:
        for setting in json.load(f):
             mode0 = setting[u'mode']
             if mode == mode0:
                 return setting[u'dbname']
    return "VnTrader_1Min_Db"

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

#----------------------------------------------------------------------
def loadStrategyData(dbName, name, start="20151001", end="",
        fields=['date','pnl'],pdformat=True):
    """载入历史数据"""
    dataEndDate = None
    if 'date' not in fields:
        fields.insert(0,'date')

    host, port = loadMongoSetting()
    dbClient = pymongo.MongoClient(host, port, socketKeepAlive=True)
    collection = dbClient[dbName][name]          

    if len(start) == 8:
    	dataStartDate = datetime.strptime(start, '%Y%m%d')
    else:
    	dataStartDate = datetime.strptime(start, '%Y%m%d %H:%M:%S')
    if len(end) == 8:
    	dataEndDate = datetime.strptime(end, '%Y%m%d')
    elif len(end) > 0:
    	dataEndDate = datetime.strptime(end, '%Y%m%d %H:%M:%S')

    # 载入回测数据
    if not dataEndDate:
        flt = {'date':{'$gte':dataStartDate}}   # 数据过滤条件
    else:
        flt = {'date':{'$gte':dataStartDate,
                       '$lte':dataEndDate}}  
    dbCursor = collection.find(flt,no_cursor_timeout=True).batch_size(1000)
    
    if not pdformat:
        return dbCursor

    datas = pd.DataFrame([data for data in\
        dbCursor],columns=fields,index=range(0,dbCursor.count()))
    return datas

#----------------------------------------------------------------------
def loadHistoryData(dbName, symbol, start="20151001", end="",
        fields=['datetime','lastPrice'],pdformat=True):
    """载入历史数据"""
    # 获得数据库
    host, port = loadMongoSetting()
    dbClient = pymongo.MongoClient(host, port, socketKeepAlive=True)
    collection = dbClient[dbName][symbol]          
    # 确定过滤条件
    dayFmt = '%Y%m%d'
    minFmt = '%Y%m%d %H:%M:%S'
    dataStartDate = datetime.strptime(start,dayFmt) if len(start) == 8 else datetime.strptime(start,minFmt)
    dataEndDate = datetime.strptime(end,dayFmt) if len(end) == 8 else datetime.strptime(end,minFmt) if len(end)>0 else None 
    flt = {'datetime':{'$gte':dataStartDate}} if not dataEndDate else {'datetime':{'$gte':dataStartDate,'$lte':dataEndDate}}  
    # 数据库指针
    dbCursor = collection.find(flt,no_cursor_timeout=True).batch_size(1000)
    
    if not pdformat:
        return dbCursor

    if 'datetime' not in fields:
        fields.insert(0,'datetime')

    allDatas = [data for data in dbCursor]
    # 对于某些字段不统一的宏观数据，需要特殊处理
    if len(fields)==1:
        fields = set([])
        for d in allDatas:
            fields = fields|set(d.keys())
        fields.remove('_id')
        fields = [str(f) for f in fields]
    datas = pd.DataFrame(allDatas,columns=fields,index=range(0,dbCursor.count()))
    datas = datas.set_index('datetime')
    return datas

#----------------------------------------------------------------------
def loadHistoryBarByTick(dbName, symbol, start="20151001", end="",
        fields=['datetime','open', 'high', 'low', 'close'],nMin=1,pSecond=59,pdformat=True,mode='t'):
    """载入历史数据"""
    dbCursor = loadHistoryData(dbName,symbol,start,end,pdformat=False)
    bars = [b for b in tick2vbars(dbCursor,nMin)] if mode=='v'\
      else [b for b in tick2bars(dbCursor,nMin,pSecond)]

    if not pdformat:
        return bars
    if 'datetime' not in fields:
        fields.insert(0,'datetime')
    datas = pd.DataFrame([d.__dict__ for d in bars],columns=fields)
    datas = datas.set_index('datetime')
    return datas

#----------------------------------------------------------------------
def tick2bars(tickers, nMin=1, pSecond=59):
    """tick数据转换为bar数据"""
    bar = None
    barMinute = 0
    for tick_dict in tickers:
        # 计算K线
        tick = ctaBase.CtaTickData()
        tick.__dict__ = tickers.next()
        tickMinute,tickSecond = tick.datetime.minute,tick.datetime.second
        if tickSecond == pSecond:
            tickMinute+=1
        if not bar or int(tickMinute/nMin) != int(barMinute/nMin):
            if bar:
                bar.datetime = tick.datetime
                bar.high     = max(bar.high, tick.lastPrice)
                bar.low      = min(bar.low, tick.lastPrice)
                bar.close    = tick.lastPrice
                if tick.volume > bar.volume and bar.volume > 0:
                    bar.openInterest = tick.openInterest - bar.openInterest
                    bar.volume       = tick.volume - bar.volume
                    bar.turnover     = tick.turnover - bar.turnover
                else:
                    bar.openInterest = 0
                    bar.volume       = 0
                    bar.turnover     = 0
                yield bar

            bar = ctaBase.CtaBarData()              
            bar.vtSymbol = tick.vtSymbol
            bar.symbol   = tick.symbol
            bar.exchange = tick.exchange

            bar.open     = tick.lastPrice
            bar.high     = tick.lastPrice
            bar.low      = tick.lastPrice
            bar.close    = tick.lastPrice

            bar.volume   = tick.volume
            bar.turnover = tick.turnover

            bar.date     = tick.date
            bar.time     = tick.time
            bar.datetime = tick.datetime       
            barMinute    = tickMinute          
            bar.openInterest = tick.openInterest

        else:                                   
            bar.high  = max(bar.high, tick.lastPrice)
            bar.low   = min(bar.low, tick.lastPrice)
            bar.close = tick.lastPrice

#----------------------------------------------------------------------
def tick2vbars(tickers, nMin=10000, size=1):
    """tick数据转换为等成交bar数据"""
    bar = None
    barVolume = 0
    lasttick = None
    sumvOnAskmBid = 0
    sumvolume = 0
    for tick_dict in tickers:
        # 计算K线
        tick = ctaBase.CtaTickData()
        tick.__dict__ = tickers.next()
        tickVolume = tick.volume
        if tickVolume < barVolume or (lasttick and tickVolume < lasttick.volume):
            barVolume = 0
            bar = None
        askPrice = tick.askPrice1
        bidPrice = tick.bidPrice1
        if lasttick:
            turnover = tick.turnover-lasttick.turnover
            volume =  tick.volume-lasttick.volume
        else:
            turnover = tick.turnover
            volume =  tick.volume
        if volume == 0:
            aprice = 0
        else:
            aprice = turnover/volume/size
        vOnAskmBid = (2*aprice - askPrice - bidPrice)/(askPrice-bidPrice)*volume 
        sumvOnAskmBid += vOnAskmBid
        sumvolume += volume

        lasttick = tick

        if not bar or int(tickVolume/nMin) != int(barVolume/nMin):
            if bar:
                bar.datetime = tick.datetime
                bar.high = max(bar.high, tick.lastPrice)
                bar.low = min(bar.low, tick.lastPrice)
                bar.close = tick.lastPrice
                bar.openInterest = tick.openInterest - bar.openInterest
                bar.volume       = tick.volume - bar.volume
                bar.turnover     = tick.turnover - bar.turnover
                if sumvolume != 0:
                    bar.vpin     = sumvOnAskmBid/sumvolume
                else:
                    bar.vpin     = 0
                sumvOnAskmBid    = 0
                sumvolume        = 0
                yield bar

            bar = ctaBase.CtaBarData()              
            bar.vtSymbol = tick.vtSymbol
            bar.symbol = tick.symbol
            bar.exchange = tick.exchange

            bar.open = tick.lastPrice
            bar.high = tick.lastPrice
            bar.low  = tick.lastPrice
            bar.close = tick.lastPrice

            bar.openInterest = tick.openInterest
            bar.volume = tick.volume
            bar.turnover = tick.turnover

            bar.date = tick.date
            bar.time = tick.time
            bar.datetime = tick.datetime    # K线的时间设为第一个Tick的时间

            barVolume = tickVolume          # 更新当前的分钟

        else:                               # 否则继续累加新的K线

            bar.high = max(bar.high, tick.lastPrice)
            bar.low = min(bar.low, tick.lastPrice)
            bar.close = tick.lastPrice

