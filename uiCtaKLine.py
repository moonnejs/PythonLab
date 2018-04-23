# -*- coding: utf-8 -*-
from ctaBase import CtaBarData 
from uiBasicIO import uiBasicIO
from uiKLine import KLineWidget
# PyQt
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import QtGui,QtCore
from datetime import datetime

from threading import Thread
from collections import deque

import pymongo
import time

import numpy as np
import pandas as pd



########################################################################
class ctaKLine(uiBasicIO):

    """K线向量化回测工具"""

    dbClient = None
    signal = QtCore.pyqtSignal(type({}))

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, eventEngine, parent=None):
        """初始化函数"""
        import ctaBase
        super(ctaKLine,self).__init__(parent,\
                    'json\\uiCtaKLine_input.json',\
                    'json\\uiCtaKLine_button.json')  # 输入配置文件,按钮配置文件

        # 用于计算因子的数据
        self.bars = deque([])
        self.pdBars = pd.DataFrame()
        self.signals = deque([])
        self.signalsOpen = deque([])
        self.states = []
        self.pnl = []
        self.stateData = {}

        self.spdData = pd.DataFrame()
        
        self.datas = None
        self.vtSymbol = ""
        self.vtSymbol1 = ""
        self.mode = 'deal'

        self.canvas = KLineWidget(self)
        self.signal.connect(self.loadData)

        self.initUi()

    #-----------------------------------------------
    def loadData(self,data):
        """载入所有数据"""
        self.bars = data['bar']
        self.states = data['state']
        self.pnl = data['pnl']
        self.signals = data['deal']
        self.signalsOpen = data['dealOpen']
        kTool = self.canvas
        for sig in kTool.sigPlots:
            kTool.pwKL.removeItem(kTool.sigPlots[sig])
        kTool.sigData  = {}
        kTool.sigPlots = {}
        for sig in kTool.subSigPlots:
            kTool.pwOI.removeItem(kTool.subSigPlots[sig])
        kTool.subSigData  = {}
        kTool.subSigPlots = {}
        print u'正在准备回测结果数据....'
        self.canvas.clearData()
        self.pdBars = pd.DataFrame(list(self.bars))
        self.pdBars = self.pdBars[['datetime','open','close','low','high','volume','openInterest']].set_index('datetime')
        self.canvas.loadData(self.pdBars)
        self.canvas.updateSig(self.signals,self.signalsOpen)
        self.spdData = pd.DataFrame(self.states)
        self.stateData = self.spdData.to_records()
        allState = filter(lambda s:s not in ['trading','inited','pos'],self.spdData.columns)
        allState = filter(lambda s:isinstance(self.spdData[s][0], (int, long, float)),allState)
        self.spdData['pnl'] = self.pnl
        self.spdData = self.spdData[self.spdData['pnl']!=0][allState+['pnl']]
        #self.spdData['pnl'] = ['p' if p > 0 else 'l' for p in self.pnl]
        self.editDict['signalName'].clear()
        self.editDict['signalName'].addItems(allState) 
        print u'数据准备完成！'

    #-----------------------------------------------
    def loadSig(self,data):
        """载入K线信号"""
        self.states = data['state']
        self.pnl = data['pnl']
        self.signals = data['deal']
        self.signalsOpen = data['dealOpen']
        kTool = self.canvas
        for sig in kTool.sigPlots:
            kTool.pwKL.removeItem(kTool.sigPlots[sig])
        kTool.sigData  = {}
        kTool.sigPlots = {}
        for sig in kTool.subSigPlots:
            kTool.pwOI.removeItem(kTool.subSigPlots[sig])
        kTool.subSigData  = {}
        kTool.subSigPlots = {}
        self.canvas.updateSig(self.signals)
        self.spdData = pd.DataFrame(self.states)
        self.stateData = self.spdData.to_records()
        allState = filter(lambda s:s not in ['trading','inited','pos'],self.spdData.columns)
        allState = filter(lambda s:isinstance(self.spdData[s][0], (int, long, float)),allState)
        self.spdData['pnl'] = self.pnl
        self.spdData = self.spdData[self.spdData['pnl']!=0][allState+['pnl']]
        #self.spdData['pnl'] = ['p' if p > 0 else 'l' for p in self.pnl]
        self.editDict['signalName'].clear()
        self.editDict['signalName'].addItems(allState) 

    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.groupInput)
        hbox.addWidget(self.groupProcess)
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.canvas)
        self.setLayout(vbox)

    #----------------------------------------------------------------------
    def setSymbol(self, symbol):
        """设置合约信息"""
        self.vtSymbol = symbol
        self.editDict['symbol'].setText(symbol)  
        if '-' in symbol:
            self.vtSymbol = symbol.split('-')[0]
            self.vtSymbol1 = symbol.split('-')[1] 
        else:
            self.vtSymbol1 = None

########################################################################
import sys
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 界面设置
    cfgfile = QtCore.QFile('css.qss')
    cfgfile.open(QtCore.QFile.ReadOnly)
    styleSheet = cfgfile.readAll()
    styleSheet = unicode(styleSheet, encoding='utf8')
    app.setStyleSheet(styleSheet)
    # K线界面
    ui = ctaKLine()
    ui.show()
    app.exec_()
