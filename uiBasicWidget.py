# encoding: UTF-8

CAPITAL_DB_NAME = 'vt_trader_cap_db'

import csv
import json

import numpy as np
from collections import OrderedDict
from datetime import datetime, timedelta

from qtpy import QtGui, QtCore
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from eventEngine import *
from ctaBasicModel import *
from ctaSetting import STRATEGY_CLASS
from ctaBacktesting import OptimizationSetting

from ctypes import windll, WINFUNCTYPE, c_bool, c_int
from ctypes.wintypes import UINT

WM_HOTKEY = 0x0312
KEY_F5    = 7602176
KEY_F2    = 7405568

# 字符串转换
#---------------------------------------------------------------------------------------
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

# 注册程序热键
#----------------------------------------------------------------------
def regHotKey(winId,keyId):
    """注册全局热键"""
    prototype = WINFUNCTYPE(c_bool, c_int, c_int, UINT, UINT)
    paramflags = (1, 'hWnd', 0), (1, 'id', 0), (1, 'fsModifiers', 0), (1, 'vk', 0)
    RegisterHotKey = prototype(('RegisterHotKey', windll.user32), paramflags)
    return RegisterHotKey(c_int(winId), 0x0000, 0, keyId)


# 载入字体
#----------------------------------------------------------------------
def loadFont():
    """载入字体设置"""
    try:
        f = file("VT_setting.json")
        setting = json.load(f)
        family = setting['fontFamily']
        size = setting['fontSize']
        font = QFont(family, size)
    except:
        font = QFont(u'微软雅黑', 12)
    return font

BASIC_FONT = loadFont()

########################################################################
class btQApp(QApplication):
    """定义回测应用，注册回测快捷键"""
    
    #----------------------------------------------------------------------
    def __init__(self, argv, eventEngine):
        """Constructor"""
        super(btQApp, self).__init__(argv)
        self.setWindowIcon(QIcon('cta.ico'))
        self.setFont(BASIC_FONT) 
        self.eventEngine = eventEngine
        
    #----------------------------------------------------------------------
    def winEventFilter(self, msg):
        if msg.message == WM_HOTKEY:
            if msg.lParam == KEY_F5:
                event = Event(type_=EVENT_F5)
                self.eventEngine.put(event)   
            #elif msg.lParam == KEY_F2:
            #    event = Event(type_=EVENT_F2)
            #    self.eventEngine.put(event)   
        return False,0


########################################################################
class BasicDialog(QWidget):
    """基础对话框"""

    #----------------------------------------------------------------------
    def __init__(self, parent=None):
        """Constructor"""
        super(BasicDialog, self).__init__(parent)

    #----------------------------------------------------------------------
    def hboxAddButton(self,hbox,name,style,func):
        """新增一行"""
        button = QPushButton(name)
        button.setObjectName(_fromUtf8(style))
        button.clicked.connect(func)
        hbox.addWidget(button)
        return button

    #----------------------------------------------------------------------
    def gridAddComboBox(self,gridlayout,name,listItems,index):
        """新增一行"""
        label = QLabel(name)
        lcbox = QComboBox()
        lcbox.addItems(listItems)
        gridlayout.addWidget(label, index, 0)
        gridlayout.addWidget(lcbox, index, 1)
        return lcbox

    #----------------------------------------------------------------------
    def gridAddLineEdit(self,gridlayout,name,index):
        """新增一行"""
        label = QLabel(name)
        ledit = QLineEdit()
        gridlayout.addWidget(label, index, 0)
        gridlayout.addWidget(ledit, index, 1)
        return ledit

    #----------------------------------------------------------------------
    def gridAddLineEditV(self,gridlayout,name,index):
        """新增一列"""
        label = QLabel(name)
        ledit = QLineEdit()
        gridlayout.addWidget(label, 0, index)
        gridlayout.addWidget(ledit, 1, index)
        return ledit

    #----------------------------------------------------------------------
    def gridAddComboBoxV(self,gridlayout,name,listItems,index):
        """新增一列"""
        label = QLabel(name)
        lcbox = QComboBox()
        lcbox.addItems(listItems)
        gridlayout.addWidget(label, 0, index)
        gridlayout.addWidget(lcbox, 1, index)
        return lcbox

    #----------------------------------------------------------------------
    def addButton(self,vbox):
        """添加确认退出按钮"""
        self.buttonEdit = QPushButton(u'确认')
        self.buttonClose = QPushButton(u'退出')
        
        # 界面美化
        self.buttonEdit.setObjectName(_fromUtf8("redButton"))
        self.buttonClose.setObjectName(_fromUtf8("blueButton"))

        self.connect(self.buttonEdit,                                 
          QtCore.SIGNAL('clicked()'),
          self.OnButtonEdit)
        self.connect(self.buttonClose,                                 
          QtCore.SIGNAL('clicked()'),
          self.close)

        hbox = QHBoxLayout()
        hbox.addWidget(self.buttonEdit)
        hbox.addWidget(self.buttonClose)

        vbox.addLayout(hbox)

    #重载方法keyPressEvent(self,event),即按键按下事件方法
    #----------------------------------------------------------------------
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Enter:
            self.OnButtonEdit()
        event.accept()

    #----------------------------------------------------------------------
    def OnButtonEdit(self):                                           
        self.close()

########################################################################
class StrategyAddWidget(BasicDialog):
    """新建回测实例对话框"""

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, eventEngine, parent=None):
        """Constructor"""
        super(StrategyAddWidget, self).__init__(parent)
        self.ctaEngine = ctaEngine
        self.eventEngine = eventEngine
        self.initUi()

    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        QWidget.__init__(self)      # 调用父类初始化方法
        self.setWindowTitle(u'新增策略')
        self.resize(400, 200)
        gridlayout = QGridLayout()

        self.sClass   = self.gridAddLineEdit(gridlayout, u'策略类',0)
        self.lineName = self.gridAddLineEdit(gridlayout, u'实例名（不可重复）',1)
        self.lineCap  = self.gridAddLineEdit(gridlayout, u'使用资金',2)
        self.sClass.setFocusPolicy(QtCore.Qt.NoFocus)

        vbox = QVBoxLayout()
        vbox.addLayout(gridlayout)
        self.addButton(vbox)
        self.setLayout(vbox)                                    

    #----------------------------------------------------------------------
    def OnButtonEdit(self):
        """确认"""
        cname = str(self.sClass.text())
        sname = str(self.lineName.text())
        cap   = str(self.lineCap.text())
        if sname == '':
            print u'策略名称不可为空'
            return
        self.ctaEngine.strategyDict[sname] = STRATEGY_CLASS[cname](self.ctaEngine,{'name':sname,'capital':cap})
        self.ctaEngine.saveSetting()
        self.ctaEngine.loadSetting()
        event = Event(EVENT_CTA_STRATEGY_LOAD)
        self.eventEngine.put(event)
        self.close()

########################################################################
class InfoInputWidget(BasicDialog):
    """参数扫描对话框"""

    ctaEngine = None
    name = ''
    paramList = []
    startEdit = {}
    stepEdit = {}
    stopEdit = {}

    #----------------------------------------------------------------------
    def __init__(self, name, ctaEngine, parent=None):
        """Constructor"""
        super(InfoInputWidget, self).__init__(parent)
        self.name = name
        self.parent = parent
        self.ctaEngine = ctaEngine
        paramDict = self.ctaEngine.getStrategyParam(self.name)
        self.paramList = paramDict.keys()
        self.startEdit = {}
        self.stepEdit = {}
        self.stopEdit = {}
        self.initUi()

    #----------------------------------------------------------------------
    def initUi(self):
        """"""
        QWidget.__init__(self)         # 调用父类初始化方法
        self.setWindowTitle(u'设置参数')
        self.resize(600, 400)                 # 设置窗口大小
        gridlayout = QGridLayout()     # 创建布局组件
        i = 0
        lName  = QLabel(u'变量名')
        lStart = QLabel('start')
        lStep  = QLabel('step')
        lStop  = QLabel('stop')
        gridlayout.addWidget(lName,  i, 0 )
        gridlayout.addWidget(lStart, i, 1 )
        gridlayout.addWidget(lStep,  i, 2 )
        gridlayout.addWidget(lStop,  i, 3 )
        for name in self.paramList:
            if not (name=='name' or name=='className' or name=='author'
                    or name=='vtSymbol' or name=='backtesting'):            
                i += 1
                label = QLabel(name)   # 创建单选框
                self.startEdit[name] = QLineEdit()
                self.stepEdit[name]  = QLineEdit()
                self.stopEdit[name]  = QLineEdit()
                gridlayout.addWidget(label, i, 0 )                    # 添加文本
                gridlayout.addWidget(self.startEdit[name], i,  1)   # 添加文本框
                gridlayout.addWidget(self.stepEdit[name],  i,  2)   # 添加文本框
                gridlayout.addWidget(self.stopEdit[name],  i,  3)   # 添加文本框
        
        vbox = QVBoxLayout()
        vbox.addLayout(gridlayout)
        self.addButton(vbox)
        self.setLayout(vbox)                                    

    #----------------------------------------------------------------------
    def OnButtonEdit(self):                                           # 按钮插槽函数
        startTime = str(self.parent.startEdit.text())
        endTime   = str(self.parent.endEdit.text())
        sp        = eval(str(self.parent.spEdit.text()))
        optimizationSetting = OptimizationSetting()
        for name in self.paramList:
            if not (name == 'name' or name == 'className' or name == 'author'
                    or name == 'vtSymbol' or name == 'backtesting'):            
                if str(self.startEdit[name].text()):
                    start = eval(str(self.startEdit[name].text()))
                    step  = eval(str(self.stepEdit[name].text()))
                    stop  = eval(str(self.stopEdit[name].text()))
                    optimizationSetting.addParameter(name, start, stop, step)
        optimizationSetting.setOptimizeTarget('capital')
        mode = self.parent.getBtMode()
        self.ctaEngine.optimizeStrategy(self.name,optimizationSetting,startTime,endTime,sp,mode)
        self.close()

########################################################################
class RollingInputWidget(BasicDialog):
    """滚动优化回测对话框"""

    ctaEngine = None
    name = ''
    paramList = []
    startEdit = {}
    stepEdit = {}
    stopEdit = {}

    #----------------------------------------------------------------------
    def __init__(self, name, ctaEngine, parent=None):
        """Constructor"""
        super(RollingInputWidget, self).__init__(parent)
        self.parent = parent
        self.ctaEngine = ctaEngine
        self.name = name
        paramDict = self.ctaEngine.getStrategyParam(self.name)
        self.paramList = paramDict.keys()
        self.ctaEngine = ctaEngine
        self.startEdit = {}
        self.stepEdit = {}
        self.stopEdit = {}
        self.initUi()

    #----------------------------------------------------------------------
    def initUi(self):
        """"""
        QWidget.__init__(self)         # 调用父类初始化方法
        self.setWindowTitle(u'设置参数')
        self.resize(600, 400)                 # 设置窗口大小
        gridlayout = QGridLayout()     # 创建布局组件
        i = 0
        lName  = QLabel(u'变量名')
        lStart = QLabel('start')
        lStep  = QLabel('step')
        lStop  = QLabel('stop')
        gridlayout.addWidget(lName,  i, 0 )
        gridlayout.addWidget(lStart, i, 1 )
        gridlayout.addWidget(lStep,  i, 2 )
        gridlayout.addWidget(lStop,  i, 3 )
        rdaysLabel  = QLabel(u'滚动日期')
        self.rdaysEdit = QLineEdit()
        for name in self.paramList:
            if not (name=='name' or name=='className' or name=='author'
                    or name=='vtSymbol' or name=='backtesting'):            
                i += 1
                label = QLabel(name)   # 创建单选框
                self.startEdit[name] = QLineEdit()
                self.stepEdit[name]  = QLineEdit()
                self.stopEdit[name]  = QLineEdit()
                gridlayout.addWidget(label, i, 0 )                    # 添加文本
                gridlayout.addWidget(self.startEdit[name], i,  1)   # 添加文本框
                gridlayout.addWidget(self.stepEdit[name],  i,  2)   # 添加文本框
                gridlayout.addWidget(self.stopEdit[name],  i,  3)   # 添加文本框
        
        gridlayout.addWidget(rdaysLabel, i+1, 0 )            
        gridlayout.addWidget(self.rdaysEdit, i+1,  1)   

        vbox = QVBoxLayout()
        vbox.addLayout(gridlayout)
        self.addButton(vbox)
        self.setLayout(vbox)                                    

    #----------------------------------------------------------------------
    def OnButtonEdit(self):                                           # 按钮插槽函数
        startTime = str(self.parent.startEdit.text())
        endTime   = str(self.parent.endEdit.text())
        sp        = eval(str(self.parent.spEdit.text()))
        rdays     = eval(str(self.rdaysEdit.text()))
        optimizationSetting = OptimizationSetting()
        for name in self.paramList:
            if not (name == 'name' or name == 'className' or name == 'author'
                    or name == 'vtSymbol' or name == 'backtesting'):            
                if str(self.startEdit[name].text()):
                    start = eval(str(self.startEdit[name].text()))
                    step  = eval(str(self.stepEdit[name].text()))
                    stop  = eval(str(self.stopEdit[name].text()))
                    optimizationSetting.addParameter(name, start, stop, step)
        optimizationSetting.setOptimizeTarget('capital')
        mode = self.parent.getBtMode()
        self.ctaEngine.backtestRollingStrategy(self.name,optimizationSetting,startTime,endTime,rdays,sp,mode)
        self.close()

########################################################################
class SplitInputWidget(BasicDialog):
    """分段回测对话框"""

    ctaEngine = None
    name = ''

    #----------------------------------------------------------------------
    def __init__(self, name, ctaEngine, parent=None):
        """Constructor"""
        super(SplitInputWidget, self).__init__(parent)
        self.parent = parent
        self.ctaEngine = ctaEngine
        self.name = name
        self.initUi()

    #----------------------------------------------------------------------
    def initUi(self):
        """"""
        QWidget.__init__(self)         # 调用父类初始化方法
        self.setWindowTitle(u'设置参数')
        self.resize(275, 205)                 # 设置窗口大小
        gridlayout = QGridLayout()     # 创建布局组件
        rdaysLabel  = QLabel(u'分段日期')
        self.rdaysEdit = QLineEdit()
        gridlayout.addWidget(rdaysLabel, 0, 0 )            
        gridlayout.addWidget(self.rdaysEdit, 0,  1)   
        vbox = QVBoxLayout()
        vbox.addLayout(gridlayout)
        self.addButton(vbox)
        self.setLayout(vbox)                                    

    #----------------------------------------------------------------------
    def OnButtonEdit(self):                                           # 按钮插槽函数
        startTime = str(self.parent.startEdit.text())
        endTime   = str(self.parent.endEdit.text())
        sp        = eval(str(self.parent.spEdit.text()))
        rdays     = eval(str(self.rdaysEdit.text()))
        mode      = self.parent.getBtMode()
        self.ctaEngine.backtestSplitStrategy(self.name,startTime,endTime,rdays,sp,mode)
        self.close()

########################################################################
class StratrgySettingWidget(BasicDialog):
    """策略配置对话框"""

    ctaEngine = None
    index     = 0
    name      = ''
    paramDict = {}
    valueEdit = {}

    #----------------------------------------------------------------------
    def __init__(self,  name, ctaEngine, eventEngine, master, parent=None):
        """Constructor"""
        super(StratrgySettingWidget, self).__init__(parent)
        self.ctaEngine = ctaEngine
        self.eventEngine = eventEngine
        self.name      = name
        self.master    = master
        self.valueEdit = {}
        self.paramDict = self.ctaEngine.getStrategyParam(self.name)
        self.initUi()

    #----------------------------------------------------------------------
    def initUi(self):
        """"""
        QWidget.__init__(self)         # 调用父类初始化方法
        self.setWindowTitle(u'设置参数')
        self.resize(300,400)                 # 设置窗口大小
        gridlayout = QGridLayout()     # 创建布局组件
        i = 0
        gridlayout.addWidget(QLabel(u'变量'),  i, 0 )   # 表头
        gridlayout.addWidget(QLabel(u'内容'),  i, 1 )   # 表头
        for name in self.paramDict:
           i += 1
           label = QLabel(name)   # 创建单选框
           self.valueEdit[name] = self.gridAddLineEdit(gridlayout,name,i)
           self.valueEdit[name].setText(str(self.paramDict[name]))

        vbox = QVBoxLayout()
        vbox.addLayout(gridlayout)
        self.addButton(vbox)
        self.setLayout(vbox)                                    

    #----------------------------------------------------------------------
    def OnButtonEdit(self):                                           # 按钮插槽函数
        for name in self.valueEdit:
            value = str(self.valueEdit[name].text())
            if value.isdigit():
                self.paramDict[name] = eval(value)
            else:
                self.paramDict[name] = value
        self.ctaEngine.setStrategyParam(self.name,self.paramDict)
        self.ctaEngine.saveSetting()
        event = Event(EVENT_CTA_STRATEGY_PARAM)
        event.dict_['data'] = self.name
        self.eventEngine.put(event)
        self.close()

