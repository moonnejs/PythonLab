# -*- coding: utf-8 -*-
import ctypes
from ctypes import Structure,c_char,c_longlong,c_int,c_double

class QDMarketDataField(Structure):
    _fields_ = [
        ("vtSymbol", c_char * 31),	# 合约代码 
        ("ctime", c_longlong),	        # 时间 
        ("msec", c_int),	        # 最后修改毫秒 
        ("lastPrice", c_double),	# 最新价 
        ("volume", c_int),	        # 数量 
        ("turnover", c_double),	        # 成交金额 
        ("openInterest", c_double),	# 持仓量 
        ("upperLimit", c_double),	# 涨停板价 
        ("lowerLimit", c_double),	# 跌停板价 
        ("bidPrice1", c_double),	# 申买价一 
        ("bidVolume1", c_int),	        # 申买量一 
        ("askPrice1", c_double),	# 申卖价一 
        ("askVolume1", c_int),	        # 申卖量一 
        ("date", c_char * 13),	        # 交易日 
        ]

class QDBarMarketDataField(Structure):
    _fields_ = [
        ("date", c_char * 9),	        # 交易日 
        ("vtSymbol", c_char * 31),	# 合约代码 
        ("ctime", c_longlong),	        # 首tick修改时间 
        ("open", c_double),	        # 开 
        ("close", c_double),	        # 收 
        ("low", c_double),	        # 低 
        ("high", c_double),	        # 高 
        ("volume", c_double),	        # 区间交易量 
        ]

class QDRtnOrderField(Structure):
    _fields_ = [
        ("brokerID", c_char * 11),	# 经纪公司代码 
        ("userID", c_char * 16),	# 用户代码 
        ("participantID", c_char * 11),	# 会员代码 
        ("investorID", c_char * 19),	# 投资者代码 
        ("businessUnit", c_char * 21),	# 业务单元 
        ("vtSymbol", c_char * 31),	# 合约代码 
        ("orderID", c_char * 21),	# 报单引用 
        ("exchange", c_char * 11),	# 交易所代码 
        ("price", c_double),	        # 价格 
        ("tradedVolume", c_int),	# 今成交数量 
        ("volumeTotal", c_int),	        # 剩余数量 
        ("totalVolume", c_int),	        # 总数量 
        ("timeCondition", c_char),	# 有效期类型
        ("volumeCondition", c_char),	# 成交量类型
        ("priceType", c_char),	        # 报单价格条件
        ("directioncpp", c_char),	# 买卖方向
        ("offsetcpp", c_char),	        # 开平标志
        ("hedge", c_char),	        # 投机套保标志
        ("statuscpp", c_char),	        # 报单状态
        ("orderTime", c_char * 21),	# 报单时间 
        ("orderID", c_int),	        # 请求编号 
        ]

class QDRtnTradeField(Structure):
    _fields_ = [
        ("brokerID", c_char * 11),	# 经纪公司代码 
        ("userID", c_char * 16),	# 用户代码 
        ("investorID", c_char * 19),	# 投资者代码 
        ("businessUnit", c_char * 21),	# 业务单元 
        ("vtSymbol", c_char * 31),	# 合约代码 
        ("orderID", c_char * 21),	# 报单引用 
        ("exchange", c_char * 11),	# 交易所代码 
        ("tradeID", c_char * 21),	# 成交编号 
        ("orderSysID", c_char * 31),	# 报单编号 
        ("participantID", c_char * 11),	# 会员代码 
        ("clientID", c_char * 21),	# 客户代码 
        ("price", c_double),	        # 价格 
        ("volume", c_int),	        # 数量 
        ("ctime", c_longlong),	        # 时间 
        ("tradingDay", c_char * 13),	# 交易日 
        ("tradeTm", c_char * 13),	# 成交时间 
        ("directioncpp", c_char),	# 买卖方向
        ("offsetcpp", c_char),	        # 开平标志
        ("hedgeFlag", c_char),	        # 投机套保标志
        ]

