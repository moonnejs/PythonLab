# encoding: UTF-8

'''
本文件中包含了CTA模块中用到的一些基础设置、类和常量等。
'''

from __future__ import division
from qtpy import QtGui, QtCore
from ctaBase import *
from eventEngine import *

########################################################################
class StrategyBacktesting(QtGui.QStandardItemModel):

    """用于回测的策略信息"""
    signal = QtCore.Signal(type(Event()))
    #----------------------------------------------------------------------
    def __init__(self, eventEngine, ctaEngine=None, view = None):
        """Constructor"""
        super(StrategyBacktesting, self).__init__(None)
      
        self.eventEngine = eventEngine
        self.ctaEngine = ctaEngine
        self.view = view 
        self.view = view 
        self.nRow = 0
        self.nameItems = {}
        self.classItems = {}

        self.initUi()  
        self.updateData()

    #----------------------------------------------------------------------
    def initUi(self):
        """"""
        self.setHorizontalHeaderItem(0, QtGui.QStandardItem(u'策略信息'))
        self.setHorizontalHeaderItem(1, QtGui.QStandardItem(u'交易合约'))
        self.setHorizontalHeaderItem(2, QtGui.QStandardItem(u'使用资金'))

    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.signal.connect(self.updateData)
        self.eventEngine.register(EVENT_CTA_STRATEGY, self.signal.emit)

    #----------------------------------------------------------------------
    def updateData(self,name0=''):
        if self.nRow > 0:
            self.removeRows(0,self.nRow)
        self.classItems = {}
        self.nameItems = {}
        for name in self.ctaEngine.strategyDict:
            paramDict = self.ctaEngine.getStrategyParam(name)
            className = paramDict['className']
            if not className in self.classItems:
                self.classItems[className] = QtGui.QStandardItem(paramDict['className'])
                self.appendRow([self.classItems[className]])
            nameItem = QtGui.QStandardItem(name)
            self.nameItems[name] = nameItem
            if name != name0:
                nameItem.setCheckState(False)  
            else:
                nameItem.setCheckState(True)  
            nameItem.setCheckable(False)
            self.classItems[className].appendRow([
                nameItem,
                QtGui.QStandardItem(str(paramDict['symbolList'])),
                QtGui.QStandardItem(str(paramDict['capital']))])
        self.nRow = len(self.classItems.values())
        if self.view: self.view.expandAll()

    #----------------------------------------------------------------------
    def checkName(self,name0):
        for name in self.nameItems:
            if name0==name:
                self.nameItems[name].setCheckState(True)
            else:
                self.nameItems[name].setCheckState(False)

########################################################################
class StrategyParam(QtGui.QStandardItemModel):

    """用于回测的策略信息"""
    signal = QtCore.Signal(type(Event()))
    #----------------------------------------------------------------------
    def __init__(self, eventEngine, ctaEngine=None):
        """Constructor"""
        super(StrategyParam, self).__init__(None)
      
        self.eventEngine = eventEngine
        self.ctaEngine = ctaEngine
        self.name = ''
        self.nRow = 0
        self.nameItems = {}

    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.signal.connect(self.updateData)
        self.eventEngine.register(EVENT_CTA_STRATEGY, self.signal.emit)

    #----------------------------------------------------------------------
    def updateData(self,name,append = False):
        if not append: 
            #self.removeRows(0,self.nRow) 
            self.clear()
            self.nRow = 1
        else:
            self.nRow += 1
        paramDict = self.ctaEngine.getStrategyParam(name)
        keys = []
        values = []
        for k,v in paramDict.items():
            keys.append(k)
            values.append(v)
        for i in range(len(keys)):
            self.setHorizontalHeaderItem(i, QtGui.QStandardItem(str(keys[i])))
        self.appendRow([
        QtGui.QStandardItem(str(v)) for v in values
        ])


########################################################################
class MongoData(QtGui.QStandardItemModel):

    """数据信息"""
    signal = QtCore.Signal(type(Event()))
    #----------------------------------------------------------------------
    def __init__(self, eventEngine, ctaEngine=None):
        """Constructor"""
        super(MongoData, self).__init__(None)
      
        self.eventEngine = eventEngine
        self.ctaEngine = ctaEngine
        self.name = ''
        self.nRow = 0
        self.nameItems = {}

    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.signal.connect(self.updateData)
        self.eventEngine.register(EVENT_CTA_STRATEGY, self.signal.emit)

    #----------------------------------------------------------------------
    def updateData(self,name):
        if self.nRow > 0:
            self.removeRows(0,self.nRow)
        self.setHorizontalHeaderItem(0, QtGui.QStandardItem(u'合约'))
        self.setHorizontalHeaderItem(1, QtGui.QStandardItem(u'数据范围'))
        self.setHorizontalHeaderItem(2, QtGui.QStandardItem(u'文件大小'))
        self.appendRow([
        QtGui.QStandardItem(str(v)) for v in values])


