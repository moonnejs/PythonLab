# encoding: UTF-8

"""
包含一些开放中常用的函数
"""

import decimal
import json
import pymongo
import pandas as pd
from datetime import datetime

MAX_NUMBER = 10000000000000
MAX_DECIMAL = 4

#----------------------------------------------------------------------
def safeUnicode(value):
    """检查接口数据潜在的错误，保证转化为的字符串正确"""
    # 检查是数字接近0时会出现的浮点数上限
    if type(value) is int or type(value) is float:
        if value > MAX_NUMBER:
            value = 0
    
    # 检查防止小数点位过多
    if type(value) is float:
        d = decimal.Decimal(str(value))
        if abs(d.as_tuple().exponent) > MAX_DECIMAL:
            value = round(value, ndigits=MAX_DECIMAL)
    
    return unicode(value)

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
def loadHistoryData(dbName, symbol, start="20151001", end="",
        fields=['datetime','lastPrice'],pdformat=True):
    """载入历史数据"""
    dataEndDate = None
    if 'datetime' not in fields:
        fields.insert(0,'datetime')
    host, port = loadMongoSetting()
    dbClient = pymongo.MongoClient(host, port, socketKeepAlive=True)
    collection = dbClient[dbName][symbol]          

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
        flt = {'datetime':{'$gte':dataStartDate}}   # 数据过滤条件
    else:
        flt = {'datetime':{'$gte':dataStartDate,
                           '$lte':dataEndDate}}  
    dbCursor = collection.find(flt,no_cursor_timeout=True).batch_size(1000)
    
    if not pdformat:
        return dbCursor

    datas = pd.DataFrame([data for data in\
        dbCursor],columns=fields,index=range(0,dbCursor.count()))
    datas = datas.set_index('datetime')

    return datas
    

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
    #datas = datas.set_index('date')

    return datas
    

#----------------------------------------------------------------------
def loadMcSetting(path=""):
    """载入Memcache配置"""
    try:
        f = file(path+"VT_setting.json")
        setting = json.load(f)
        host = setting['mcHost']
        port = setting['mcPort']
    except:
        host = 'localhost'
        port = 11210
        
    return host, port

#----------------------------------------------------------------------
def loadMongoSetting0(path=""):
    """载入MongoDB数据库的配置"""
    try:
        f = file(path+"VT_setting.json")
        setting = json.load(f)
        host = setting['mongoHost0']
        port = setting['mongoPort0']
    except:
        host = 'localhost'
        port = 27017
        
    return host, port

#----------------------------------------------------------------------
def loadPhoneSetting(path=""):
    """载入电话配置"""
    try:
        f = file(path+"VT_setting.json")
        setting = json.load(f)
        phone = setting['phoneNumber']
        sms = setting['smsWarn']
    except:
        phone = ''
        sms = False
        
    return phone, sms

#----------------------------------------------------------------------
def todayDate():
    """获取当前本机电脑时间的日期"""
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)    

 
