# encoding: UTF-8

"""
本模块中主要包含：
1. 从通联数据下载历史行情的引擎
2. 用来把MultiCharts导出的历史数据载入到MongoDB中用的函数
"""
import re
import os
import sys
import ctaBase
import pymongo
#ROOT_PATH = os.path.abspath(os.path.dirname(__file__)).decode('gbk')
#sys.path.append(ROOT_PATH+u'../')

from time import time
from datetime import datetime, timedelta

from ctaBase import *
from vtConstant import *

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
def loadMcCsv(fileName, dbName, symbol):
    """将Multicharts导出的csv格式的历史数据插入到Mongo数据库中"""
    import csv
    
    from time import time
    start = time()
    
    # 锁定集合，并创建索引
    host, port = loadMongoSetting()
    
    client = pymongo.MongoClient(host, port)    
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)   
    
    # 读取数据和插入到数据库
    reader = csv.DictReader(file(fileName, 'r'))
    for d in reader:
        bar = CtaBarData()
        bar.vtSymbol = symbol
        bar.symbol = symbol
        bar.open = float(d['Open'])
        bar.high = float(d['High'])
        bar.low = float(d['Low'])
        bar.close = float(d['Close'])
        bar.date = datetime.strptime(d['Date'], '%Y/%m/%d').strftime('%Y%m%d')
        bar.time = d['Time']
        bar.datetime = datetime.strptime(bar.date + ' ' + bar.time, '%Y%m%d %H:%M:%S')
        bar.volume = d['TotalVolume']

        flt = {'datetime': bar.datetime}
        collection.update_one(flt, {'$set':bar.__dict__}, upsert=True)  


#----------------------------------------------------------------------
def loadCtpTickCsv(fileName, dbName, symbol):
    """将CTP-csv格式的历史数据插入到Mongo数据库中"""
    import csv
    from time import time
    start = time()
    
    # 锁定集合，并创建索引
    host, port = loadMongoSetting()
	
    client = pymongo.MongoClient(host, port) 
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)   
    
    # 读取数据和插入到数据库
    reader = csv.DictReader(open(fileName, 'r'))
    for d in reader:
	tick = CtaTickData()
        tick.vtSymbol = symbol
        tick.symbol = symbol

	tick.lastPrice = float(d[u'最新价'.encode('gbk')])
	tick.volume = int(d[u'数量'.encode('gbk')])
	tick.openInterest = int(d[u'持仓量'.encode('gbk')])

	tick.upperLimit = float(d[u'涨停板价'.encode('gbk')])
	tick.lowerLimit = float(d[u'跌停板价'.encode('gbk')])

	tick.turnover = float(d[u'成交金额'.encode('gbk')])

	tick.date = d[u'业务日期'.encode('gbk')]
	tick.time = d[u'最后修改时间'.encode('gbk')]
        tick.datetime = datetime.strptime(tick.date + ' ' + tick.time, '%Y%m%d %H:%M:%S')
	tick.datetime = tick.datetime.replace(microsecond = 1000*int(d[u'最后修改毫秒'.encode('gbk')]))

	tick.bidPrice1 = float(d[u'申买价一'.encode('gbk')])
	tick.bidVolume1 = float(d[u'申买量一'.encode('gbk')])
	tick.askPrice1 = float(d[u'申卖价一'.encode('gbk')])
	tick.askVolume1 = float(d[u'申卖量一'.encode('gbk')])

        flt = {'datetime': tick.datetime}
        collection.update_one(flt, {'$set':tick.__dict__}, upsert=True)  
    return fileName
    

#----------------------------------------------------------------------
def loadCtpEnTickCsv(fileName, dbName, symbol):
    """将CTP-csv格式的历史数据插入到Mongo数据库中"""
    import csv
    from time import time
    start = time()
    
    # 锁定集合，并创建索引
    host, port = loadMongoSetting()
	
    client = pymongo.MongoClient(host, port) 
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)   
    
    # 读取数据和插入到数据库
    reader = csv.DictReader(open(fileName, 'r'))
    for d in reader:
	tick = CtaTickData()
        tick.vtSymbol = symbol
        tick.symbol = symbol
        try:
	    tick.lastPrice = float(d['LastPrice'])
	    tick.volume = float(d['Volume'])
	    tick.openInterest = float(d['OpenInterest'])

	    tick.upperLimit = float(d['UpperLimitPrice'])
	    tick.lowerLimit = float(d['LowerLimitPrice'])

	    tick.turnover = float(d['Turnover'])

	    tick.date = d['TradingDay']
	    tick.time = d['UpdateTime']
            tick.datetime = datetime.strptime(tick.date + ' ' + tick.time, '%Y%m%d %H:%M:%S')
	    tick.datetime = tick.datetime.replace(microsecond = 1000*int(d['UpdateMillisec']))
            if tick.datetime.hour >= 20:
                tick.datetime = tick.datetime-timedelta(days=1)

	    tick.bidPrice1 = float(d['BidPrice1'])
	    tick.bidVolume1 = float(d['BidVolume1'])
	    tick.askPrice1 = float(d['AskPrice1'])
	    tick.askVolume1 = float(d['AskVolume1'])
	    tick.bidPrice2 = float(d['BidPrice2'])
	    tick.bidVolume2 = float(d['BidVolume2'])
	    tick.askPrice2 = float(d['AskPrice2'])
	    tick.askVolume2 = float(d['AskVolume2'])
	    tick.bidPrice3 = float(d['BidPrice3'])
	    tick.bidVolume3 = float(d['BidVolume3'])
	    tick.askPrice3 = float(d['AskPrice3'])
	    tick.askVolume3 = float(d['AskVolume3'])
	    tick.bidPrice4 = float(d['BidPrice4'])
	    tick.bidVolume4 = float(d['BidVolume4'])
	    tick.askPrice4 = float(d['AskPrice4'])
	    tick.askVolume4 = float(d['AskVolume4'])
	    tick.bidPrice5 = float(d['BidPrice5'])
	    tick.bidVolume5 = float(d['BidVolume5'])
	    tick.askPrice5 = float(d['AskPrice5'])
	    tick.askVolume5 = float(d['AskVolume5'])
        except:
            pass

        flt = {'datetime': tick.datetime}
        collection.update_one(flt, {'$set':tick.__dict__}, upsert=True)  
    return fileName
    

#----------------------------------------------------------------------
def loadYCZTickCsv(fileName, dbName, symbol):
    """将预测者网股票csv格式的历史数据插入到Mongo数据库中"""
    import csv
    from time import time
    start = time()
    
    # 锁定集合，并创建索引
    host, port = loadMongoSetting()
	
    client = pymongo.MongoClient(host, port) 
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)   
    
    # 读取数据和插入到数据库
    f = open(fileName, 'r')
    f.readline()
    reader = csv.DictReader(f)
    for d in reader:
	tick = CtaTickData()
        tick.vtSymbol = symbol
        tick.symbol = symbol

	tick.lastPrice = float(d[u'价格'.encode('gbk')])
	tick.volume = int(d[u'成交量'.encode('gbk')])
	tick.openInterest = 0

	tick.upperLimit = 999999.0
	tick.lowerLimit = 0

	tick.turnover = float(d[u'成交额'.encode('gbk')])
        
        datetime = d[u'时间'.encode('gbk')].split(' ')
        
	tick.date = datetime[0]
	tick.time = datetime[1]
        tick.datetime = datetime.strptime(tick.date + ' ' + tick.time, '%Y/%m/%d %H:%M:%S')

	tick.bidPrice1 = float(d[u'买一价'.encode('gbk')])
	tick.bidVolume1 = float(d[u'买一量'.encode('gbk')])
	tick.askPrice1 = float(d[u'卖一价'.encode('gbk')])
	tick.askVolume1 = float(d[u'卖一量'.encode('gbk')])
	tick.bidPrice2 = float(d[u'买二价'.encode('gbk')])
	tick.bidVolume2 = float(d[u'买二量'.encode('gbk')])
	tick.askPrice2 = float(d[u'卖二价'.encode('gbk')])
	tick.askVolume2 = float(d[u'卖二量'.encode('gbk')])
	tick.bidPrice3 = float(d[u'买三价'.encode('gbk')])
	tick.bidVolume3 = float(d[u'买三量'.encode('gbk')])
	tick.askPrice3 = float(d[u'卖三价'.encode('gbk')])
	tick.askVolume3 = float(d[u'卖三量'.encode('gbk')])
	tick.bidPrice4 = float(d[u'买四价'.encode('gbk')])
	tick.bidVolume4 = float(d[u'买四量'.encode('gbk')])
	tick.askPrice4 = float(d[u'卖四价'.encode('gbk')])
	tick.askVolume4 = float(d[u'卖四量'.encode('gbk')])
	tick.bidPrice5 = float(d[u'买五价'.encode('gbk')])
	tick.bidVolume5 = float(d[u'买五量'.encode('gbk')])
	tick.askPrice5 = float(d[u'卖五价'.encode('gbk')])
	tick.askVolume5 = float(d[u'卖五量'.encode('gbk')])

        flt = {'datetime': tick.datetime}
        collection.update_one(flt, {'$set':tick.__dict__}, upsert=True)  
    return fileName
    

#----------------------------------------------------------------------
def loadPkTickCsv(fileName, dbName, symbol):
    """将Multicharts导出的csv格式的历史数据插入到Mongo数据库中"""
    import csv
    from time import time
    start = time()
    
    # 锁定集合，并创建索引
    host, port = loadMongoSetting()
	
    client = pymongo.MongoClient(host, port) 
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)   
    
    # 读取数据和插入到数据库
    reader = csv.DictReader(open(fileName, 'r'))
    for d in reader:
	tick = CtaTickData()
        tick.vtSymbol = symbol
        tick.symbol = symbol

	tick.lastPrice = float(d[u'最新'.encode('gbk')])
	tick.volume = int(float(d[u'成交量'.encode('gbk')]))
	tick.openInterest = int(float(d[u'持仓'.encode('gbk')]))

	tick.upperLimit = float(99999)
	tick.lowerLimit = float(0)

	tick.turnover = float(d[u'成交额'.encode('gbk')])

        dateandtime  = d[u'时间'.encode('gbk')].split(' ')
	tick.date = dateandtime[0]
	tick.time = dateandtime[1]
        tick.datetime = datetime.strptime(tick.date + ' ' + tick.time, '%Y-%m-%d %H:%M:%S.%f')

	tick.bidPrice1 = float(d[u'买一价'.encode('gbk')])
	tick.bidVolume1 = float(d[u'买一量'.encode('gbk')])
	tick.askPrice1 = float(d[u'卖一价'.encode('gbk')])
	tick.askVolume1 = float(d[u'卖一量'.encode('gbk')])

        flt = {'datetime': tick.datetime}
        collection.update_one(flt, {'$set':tick.__dict__}, upsert=True)  
    return fileName
    

#----------------------------------------------------------------------
def loadCtpBarCsv(fileName, dbName, symbol):
    """将csv内历史数据插入到Mongo数据库中"""
    import csv
    from time import time
    start = time()
    
    # 锁定集合，并创建索引
    host, port = loadMongoSetting()
	
    client = pymongo.MongoClient(host, port) 
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)   
    
    	
    # 读取数据和插入到数据库
    reader = csv.reader(open(fileName, 'r'))
    for d in reader:
        dict_data = {}
        date0 = d[0]
	time0 = d[1]
        datetime0 = datetime.strptime(date0 + ' ' + time0, '%Y-%m-%d %H:%M')
        dict_data['datetime']       = datetime0
        dict_data['open']           = float(d[2])
        dict_data['high']           = float(d[3])
        dict_data['low']            = float(d[4])
        dict_data['close']          = float(d[5])
        dict_data['volume']         = float(d[6])
        dict_data['openInterest']   = float(d[7])
        dict_data['vtSymbol']       = symbol
        dict_data['symbol']         = symbol

        flt = {'datetime': datetime0}
        collection.update_one(flt, {'$set':dict_data}, upsert=True)  
    return fileName
    

#----------------------------------------------------------------------
def loadTdTickCsv(fileName, dbName, symbol):
    """将Multicharts导出的csv格式的历史数据插入到Mongo数据库中"""
    import csv
    from time import time
    start = time()
    
    # 锁定集合，并创建索引
    host, port = loadMongoSetting()
	
    client = pymongo.MongoClient(host, port) 
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)   
    
    # 读取数据和插入到数据库
    reader = csv.DictReader(open(fileName, 'r'))
    for d in reader:
	tick = CtaTickData()
        tick.vtSymbol = symbol
        tick.symbol = symbol

	tick.lastPrice = float(d[u'LastPrice'.encode('gbk')])
	tick.volume = int(d[u'Volume'.encode('gbk')])
	tick.openInterest = int(d[u'Volume'.encode('gbk')])

	tick.upperLimit = float(d[u'UpperLimitPrice'.encode('gbk')])
	tick.lowerLimit = float(d[u'LowerLimitPrice'.encode('gbk')])

	tick.date = d[u'UpdateDay'.encode('gbk')]
	tick.time = d[u'UpdateTime'.encode('gbk')]
        tick.datetime = datetime.strptime(tick.date + ' ' + tick.time, '%Y%m%d %H:%M:%S')
	tick.datetime = tick.datetime.replace(microsecond = 1000*int(d[u'UpdateMillisec'.encode('gbk')]))

	tick.bidPrice1 = float(d[u'BidPrice1'.encode('gbk')])
	tick.bidVolume1 = float(d[u'BidVolume1'.encode('gbk')])
	tick.askPrice1 = float(d[u'AskPrice1'.encode('gbk')])
	tick.askVolume1 = float(d[u'AskVolume1'.encode('gbk')])

        flt = {'datetime': tick.datetime}
        collection.update_one(flt, {'$set':tick.__dict__}, upsert=True)  
    return fileName


#----------------------------------------------------------------------
def loadHistoryBarByTick(dbName, symbol, start="20151001", end="", nMin = 1):
    """载入历史数据"""
    dataEndDate = None
    host, port = loadMongoSetting()
    dbClient = pymongo.MongoClient(host, port, socketKeepAlive=True)
    collection = dbClient[dbName][symbol]          

    dataStartDate = datetime.strptime(start, '%Y%m%d') if len(start) == 8 else datetime.strptime(start, '%Y%m%d %H:%M:%S')
    if len(end) > 0:
        dataEndDate = datetime.strptime(end, '%Y%m%d') if len(end) == 8 else datetime.strptime(end, '%Y%m%d %H:%M:%S')

    flt = {'datetime':{'$gte':dataStartDate}} if not dataEndDate else {'datetime':{'$gte':dataStartDate,'$lte':dataEndDate}}  

    dbCursor = collection.find(flt,no_cursor_timeout=True).batch_size(1000)
    collection0 = dbClient[MINUTE_DB_NAME][symbol]
    collection0.ensure_index([('datetime', pymongo.ASCENDING)], unique=True) 

    for bar in tick2bars(dbCursor,nMin):
        flt = {'datetime': bar.datetime}
        collection0.update_one(flt, {'$set':bar.__dict__}, upsert=True)  
    

#----------------------------------------------------------------------
def tick2bars(tickers, nMin=1):
    """tick数据转换为bar数据"""
    bar = None
    barMinute = 0
    for tick_dict in tickers:
        # 计算K线
        tick = ctaBase.CtaTickData()
        tick.__dict__ = tickers.next()
        tickMinute = tick.datetime.minute
        if not bar or tickMinute/nMin != barMinute/nMin:
            if bar:
                bar.datetime = tick.datetime
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
            bar.symbol = tick.symbol
            bar.exchange = tick.exchange

            bar.open = tick.lastPrice
            bar.high = tick.lastPrice
            bar.low = tick.lastPrice
            bar.close = tick.lastPrice

            bar.openInterest = tick.openInterest
            bar.volume = tick.volume
            bar.turnover = tick.turnover

            bar.date = tick.date
            bar.time = tick.time
            bar.datetime = tick.datetime    # K线的时间设为第一个Tick的时间

            barMinute = tickMinute          # 更新当前的分钟

        else:                               # 否则继续累加新的K线

            bar.high = max(bar.high, tick.lastPrice)
            bar.low = min(bar.low, tick.lastPrice)
            bar.close = tick.lastPrice

#----------------------------------------------------------------------
def loadAllFileTick(path,dbName,mode='ctp'):
    import os
    import multiprocessing
    fileList=[]
    files=os.listdir(path)
    #----------------------------------------------------------------------
    def showProcessBar(result):
        """显示进度条"""
        print(result+u' 载入完成!')
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    for f in files:
        if(os.path.isfile(path + '/' + f)):  
        	fileList.append(f.decode('gbk'))  
    for fl in fileList:
	filename = re.split("_",fl)
	symbol = filename[0]
	if mode == 'ctp':
            pool.apply_async(loadCtpTickCsv,(path + '/' + fl,dbName,symbol),callback=showProcessBar)
	elif mode == 'ctpen':
            pool.apply_async(loadCtpEnTickCsv,(path + '/' + fl,dbName,symbol),callback=showProcessBar)
	elif mode == 'pk':
            pool.apply_async(loadPkTickCsv,(path + '/' + fl,dbName,symbol),callback=showProcessBar)
	elif mode == 'td':
            pool.apply_async(loadTdTickCsv,(path + '/' + fl,dbName,symbol),callback=showProcessBar)
	elif mode == 'ycz':
	    filename = re.split(" ",fl)
	    symbol = filename[1]
            pool.apply_async(loadYCZTickCsv,(path + '/' + fl,dbName,symbol),callback=showProcessBar)
    pool.close()
    pool.join()
		
#----------------------------------------------------------------------
def loadAllFileBar(path,dbName,mode='ctp'):
    import os
    import multiprocessing
    fileList=[]
    files=os.listdir(path)
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    #----------------------------------------------------------------------
    def showProcessBar(result):
        """显示进度条"""
        print(result+u' 载入完成!')
    for f in files:
        if(os.path.isfile(path + '/' + f)):  
            fileList.append(f.decode('gbk'))  
    for fl in fileList:
        filename = fl[2:].split('.')
        filename = filename[0]
        month    = fl[-2:]
	symbol   = filename.lower()
	if mode == 'ctp':
            pool.apply_async(loadCtpBarCsv,(path + '/' + fl,dbName,symbol),callback=showProcessBar)
    pool.close()
    pool.join()

#----------------------------------------------------------------------
def bar2xbars(bars,xmin):
    """K线聚合"""
    xminBar = None
    # 尚未创建对象
    for bar_dict in bars:
        # 计算K线
        bar = CtaBarData()
        bar.__dict__ = bar_dict
        if not xminBar:
            xminBar = CtaBarData()
            
            xminBar.vtSymbol = bar.symbol
            xminBar.symbol = bar.symbol
            xminBar.exchange = bar.exchange
        
            xminBar.open = bar.open
            xminBar.high = bar.high
            xminBar.low = bar.low            

        # 累加老K线
        else:
            xminBar.high = max(xminBar.high, bar.high)
            xminBar.low = min(xminBar.low, bar.low)

        # 通用部分
        xminBar.close = bar.close
        xminBar.datetime = bar.datetime
        xminBar.openInterest = bar.openInterest
        xminBar.volume += int(bar.volume)                
            
        # X分钟已经走完
        if not (bar.datetime.minute+1) % xmin:   # 可以用X整除
            # 生成上一X分钟K线的时间戳
            xminBar.datetime = xminBar.datetime.replace(second=0, microsecond=0)  # 将秒和微秒设为0
            xminBar.date = xminBar.datetime.strftime('%Y%m%d')
            xminBar.time = xminBar.datetime.strftime('%H:%M:%S.%f')
            
            # 推送
            yield xminBar
            
            # 清空老K线缓存对象
            xminBar = None

#---------------------------------------------------------------------------------------
def getDbByMode(mode):
    """获取合约信息"""
    import json
    with open("./json/DATA_setting.json") as f:
        for setting in json.load(f):
             mode0 = setting[u'mode']
             if mode == mode0:
                 return setting[u'dbname']
    return "VnTrader_1Min_Db"

#----------------------------------------------------------------------
def generateXbars(symbol, start, end, xMin, mode):
    """生成N分钟K线"""
    # 锁定集合，并创建索引
    host, port = loadMongoSetting()
    client = pymongo.MongoClient(host, port) 
    collection = client[MINUTE_DB_NAME][symbol]
    collection0 = client[getDbByMode(mode)][symbol]
    dataStartDate = datetime.strptime(start, '%Y%m%d') if len(start) == 8 else datetime.strptime(start, '%Y%m%d %H:%M:%S')
    if len(end) > 0:
        dataEndDate = datetime.strptime(end, '%Y%m%d') if len(end) == 8 else datetime.strptime(end, '%Y%m%d %H:%M:%S')

    flt = {'datetime':{'$gte':dataStartDate}} if not dataEndDate else {'datetime':{'$gte':dataStartDate,'$lte':dataEndDate}}  
    bars = collection.find(flt,no_cursor_timeout=True).batch_size(1000)
    if xMin == 'D': 
        return
    else:
        xMin = eval(xMin)
    print(u'开始聚合K线..')
    for xbar in bar2xbars(bars,xMin):
        flt = {'datetime': xbar.datetime}
        collection0.update_one(flt, {'$set':xbar.__dict__}, upsert=True)  
    print(u'聚合K线完成!')
		
if __name__ == '__main__':
    # 简单的测试脚本可以写在这里
#    temp_Path=['.\\historyData']
#    for c in temp_Path :
#	path = c
#	loadAllFileTick(path,TICK_DB_NAME,mode='ctpen')
    loadHistoryBarByTick(TICK_DB_NAME, 'a1701', start="20161001", end="20161030", nMin = 1)
