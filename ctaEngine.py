# encoding: UTF-8

'''
本文件中实现了CTA策略引擎，针对CTA类型的策略，抽象简化了部分底层接口的功能。
'''

import os
import time
import json
import pymongo
import ctaTaskPool
ctaTaskPool.taskPool = ctaTaskPool.ctaTaskPool()
import traceback
import multiprocessing


from datetime import datetime
from collections import OrderedDict
from eventEngine import *

from ctaBase import *
from ctaFunction import *
from vtConstant import *
from ctaSetting import *
from ctaBacktesting import *
from vtObject import VtLogData

########################################################################
class CtaEngine(object):
    """CTA策略引擎"""

    settingFileName = 'CTA_setting.json'
    settingFileName = os.getcwd() + '\\json\\' + settingFileName

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, settingFileName = 'CTA_setting.json'):
        """Constructor"""
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
	settingFileName0 = settingFileName
	self.settingFileName = os.getcwd() + '\\json\\' + settingFileName0
	self.optimism = False
        self.q = multiprocessing.Queue()

        # 当前日期
        self.today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # key为策略名称，value为策略实例，注意策略名称不允许重复
        self.strategyDict = {}

    #----------------------------------------------------------------------
    def writeCtaLog(self, content):
        """快速发出CTA模块日志事件"""
        log = VtLogData()
        log.logContent = content
        event = Event(type_=EVENT_CTA_LOG)
        event.dict_['data'] = log
        self.eventEngine.put(event)   
    
    #----------------------------------------------------------------------
    def loadStrategy(self, setting):
        """载入策略"""
        try:
            name = setting['name']
            className = setting['className']
        except Exception, e:
            self.writeCtaLog(u'载入策略出错：%s' %e)
            return
        
        # 获取策略类
        strategyClass = STRATEGY_CLASS.get(className, None)
        if not strategyClass:
            self.writeCtaLog(u'找不到策略类：%s' %className)
            return
        
        # 防止策略重名
        if name in self.strategyDict:
            pass
        else:
            # 创建策略实例
            strategy = strategyClass(self, setting)  
            self.strategyDict[name] = strategy

    #----------------------------------------------------------------------
    def updateStrategy(self, name):
        """更新策略配置"""
        if name in self.strategyDict:
            strategy = self.strategyDict[name]
            
        with open(self.settingFileName) as f:
            l = json.load(f)
            for setting in l:
		if setting[u'name'] == name:
		    self.callStrategyFunc(strategy, strategy.onUpdate,setting)
    
    #----------------------------------------------------------------------
    def callStrategyFunc(self, strategy, func, params=None):
        """调用策略的函数，若触发异常则捕捉"""
        try:
            if params:
                func(params)
            else:
                func()
        except Exception:
            # 停止策略，修改状态为未初始化
            strategy.trading = False
            strategy.inited = False
            
            # 发出日志
            content = '\n'.join([u'策略%s触发异常已停止' %strategy.name,traceback.format_exc()])
            self.writeCtaLog(content)
  
    #----------------------------------------------------------------------
    def backtestStrategy(self, name, startTime = '20161001', endTime = '20161030', slippage = 0, mode = 'T'):
        """回测单个策略"""
	setting_bt = {}
        with open(self.settingFileName) as f:
            l = json.load(f)
            for setting in l:
	        if setting[u'name'] == name:
	            setting_bt = setting
        q = True if mode[0:2] == 'BV' else False
        t = ctaTaskPool.taskPool.addTask('bt',args=(setting_bt, startTime, endTime, slippage, self.optimism, mode, q), runmode = mode)

    #----------------------------------------------------------------------
    def backtestRollingStrategy(self, name, optimizationSetting, startTime = '20161001', endTime = '20161030', rollingDays=20, slippage = 0, mode = 'T'):
        """回测单个策略"""
	setting_bt = {}
        with open(self.settingFileName) as f:
            l = json.load(f)
            for setting in l:
	        if setting[u'name'] == name:
	            setting_bt = setting
        q = True if mode == 'BV' else False
        ctaTaskPool.backtestingRollingE(setting_bt, optimizationSetting, startTime, endTime, rollingDays, slippage, self.optimism, mode, q)
    	self.putStrategyEvent(name)


    #----------------------------------------------------------------------
    def optimizeStrategy(self, name, optimizationSetting, startTime = '20161001', endTime = '20161030', slippage = 0, mode='T'):
        """参数扫描"""
	setting_bt = {}
        with open(self.settingFileName) as f:
            l = json.load(f)
            for setting in l:
		if setting[u'name'] == name:
		    setting_bt = setting
        ctaTaskPool.optimizeE(setting_bt,optimizationSetting,startTime,endTime,slippage,self.optimism,mode)
    	self.putStrategyEvent(name)

    #----------------------------------------------------------------------
    def reportStrategy(self):
        """策略组合报告"""
        strategyNames = []
        strategyBases = []
        for name,strategy in self.strategyDict.items():
             strategyNames.append(name)
             strategyBases.append(strategy.capital)
        rtn_table,cap_table = get_daily_rtn(strategyNames,strategyBases)
        weis = get_best_wei(rtn_table,30)
        print weis
        plotPortfolioCurve(cap_table,weis)

    #----------------------------------------------------------------------
    def saveSetting(self):
        """保存策略配置"""
        with open(self.settingFileName, 'w') as f:
            l = []
            for strategy in self.strategyDict.values():
                setting = {}
                for param in strategy.paramList:
                    value = str(strategy.__getattribute__(param))
                    if not param == 'name' and value.isdigit():
                        value = eval(value)
                    elif not param == 'name':
                        try:
                            value = float(value)
                        except Exception, e:
                            pass
                    setting[param] = value 
                l.append(setting)
            
            jsonL = json.dumps(l, indent=4)
            f.write(jsonL)
    
    #----------------------------------------------------------------------
    def loadSetting(self):
        """读取策略配置"""
        with open(self.settingFileName) as f:
            l = json.load(f)
            for setting in l:
                self.loadStrategy(setting)
    
    #----------------------------------------------------------------------
    def getStrategyVar(self, name):
        """获取策略当前的变量字典"""
        if name in self.strategyDict:
            strategy = self.strategyDict[name]
            varDict = OrderedDict()
            for key in strategy.varList:
                varDict[key] = strategy.__getattribute__(key)
            return varDict
        else:
            self.writeCtaLog(u'策略实例不存在：' + name)    
            return None
    
    #----------------------------------------------------------------------
    def getStrategyParam(self, name):
        """获取策略的参数字典"""
        if name in self.strategyDict:
            strategy = self.strategyDict[name]
            paramDict = OrderedDict()
            for key in strategy.paramList:  
                paramDict[key] = strategy.__getattribute__(key)
            return paramDict
        else:
            self.writeCtaLog(u'策略实例不存在：' + name)    
            return None   
        
    #----------------------------------------------------------------------
    def setStrategyParam(self, name, paramDict):
        """设置策略的参数字典"""
        if name in self.strategyDict:
            strategy = self.strategyDict[name]
            for key in strategy.paramList:  
                strategy.__setattr__(key, paramDict[key])
        else:
            self.writeCtaLog(u'策略实例不存在：' + name)    
            return None   
        
    #----------------------------------------------------------------------
    def putStrategyEvent(self, name):
        """触发策略状态变化事件（通常用于通知GUI更新）"""
        event = Event(EVENT_CTA_STRATEGY+name)
        self.eventEngine.put(event)

    #----------------------------------------------------------------------
    def output(self, content):
        """输出内容"""
        self.writeCtaLog(content)

