# encoding: UTF-8
'''
CTA回测任务模块相关的GUI控制组件
'''
import ctaTaskPool
import pandas as pd
from eventEngine import *
from uiBasicWidget import QtGui, QtCore, BASIC_FONT, BasicDialog

STYLESHEET_START = 'background-color: rgb(111,255,244); color: black'
STYLESHEET_STOP  = 'background-color: rgb(255,201,111); color: black'

# 字符串转换
#---------------------------------------------------------------------------------------
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

kLoader = None
########################################################################
class TaskActiveButton(QtGui.QPushButton):
    """激活按钮"""
    #----------------------------------------------------------------------
    def __init__(self, taskName='', parent=None):
        """Constructor"""
        super(TaskActiveButton, self).__init__(parent)
        
        self.active   = ctaTaskPool.taskPool.getTask(taskName).state
        self.taskName = taskName
        if not (self.active == u'已完成' or self.active==u'已停止'):
            self.setStarted()
        else:
            self.setStopped()
        
        self.clicked.connect(self.buttonClicked)
        
    #----------------------------------------------------------------------
    def buttonClicked(self):
        """改变运行模式"""
        if not (self.active == u'已完成' or self.active==u'已停止'):
            self.stop()
    
    #----------------------------------------------------------------------
    def stop(self):
        """停止"""
        ctaTaskPool.taskPool.stopTask(self.taskName)
        self.setStopped()        
            
    #----------------------------------------------------------------------
    def start(self):
        """启动"""
        ctaTaskPool.taskPool.startTask(self.taskName)
        self.setStarted()        
        
    #----------------------------------------------------------------------
    def setStarted(self):
        """算法启动"""
        self.setText(self.active)
        self.setStyleSheet(STYLESHEET_START)
        
    #----------------------------------------------------------------------
    def setStopped(self):
        """算法停止"""
        self.active = u'已停止'
        self.setText(self.active)
        self.setStyleSheet(STYLESHEET_STOP)
    
########################################################################
class TaskDisplayButton(QtGui.QPushButton):
    """显示回测结果"""
    #----------------------------------------------------------------------
    def __init__(self, taskName='', parent=None):
        """Constructor"""
        super(TaskDisplayButton, self).__init__(parent)
        name = ctaTaskPool.taskPool.getTask(taskName).results.get('capital',0)
        self.setText(str(name))
        self.setStyleSheet(STYLESHEET_STOP) 

        self.active   = False
        self.taskName = taskName
        self.clicked.connect(self.buttonClicked)
        
    #----------------------------------------------------------------------
    def buttonClicked(self):
        """显示回测结果"""
        ctaTaskPool.taskPool.getTask(self.taskName).show()
        datas = ctaTaskPool.taskPool.getTask(self.taskName).results.get('datas')
        if datas:
            kLoader.loadData(datas)

########################################################################
class TaskLogButton(QtGui.QPushButton):
    """显示回测结果"""
    #----------------------------------------------------------------------
    def __init__(self, taskName='', parent=None):
        """Constructor"""
        super(TaskLogButton, self).__init__(parent)
        name = ctaTaskPool.taskPool.getTask(taskName).results.get('totalResult',0)
        self.setText(str(name))
        self.setStyleSheet(STYLESHEET_STOP) 

        self.active   = False
        self.taskName = taskName
        self.clicked.connect(self.buttonClicked)
        
    #----------------------------------------------------------------------
    def buttonClicked(self):
        """显示回测结果"""
        ctaTaskPool.taskPool.getTask(self.taskName).log()

########################################################################
class TaskParamButton(QtGui.QPushButton):
    """查看参数按钮"""
    tp = None
    #----------------------------------------------------------------------
    def __init__(self, taskName='', parent=None):
        """Constructor"""
        super(TaskParamButton, self).__init__(parent)
        name = ctaTaskPool.taskPool.getTask(taskName).setting.get('symbolList','None')
        self.setText(str(name))
        self.setStyleSheet(STYLESHEET_STOP) 

        self.taskName = taskName
        self.clicked.connect(self.buttonClicked)
        
    #----------------------------------------------------------------------
    def buttonClicked(self):
        """显示回测结果"""
        filterList = ['name','className','mPrice','backtesting']
        kvList = ctaTaskPool.taskPool.getTask(self.taskName).setting.items()
        param = dict([it for it in kvList if it[0] not in filterList])
        self.__class__.tp = TaskParamWidget(param)
        self.__class__.tp.show()


########################################################################
class TaskTable(QtGui.QTableWidget):
    """任务管理组件"""

    #----------------------------------------------------------------------
    def __init__(self, parent=None):
        """Constructor"""
        super(TaskTable, self).__init__(parent)
        
        self.buttonActiveDict = {}
        
        self.initUi()
        
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化表格"""
        headers = [u'任务名',
                   u'策略类',
                   u'耗时',
                   u'模式',
                   u'状态',
                   u'参数',
                   u'日志',
                   u'结果']

        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(self.NoEditTriggers)
        self.setSortingEnabled(True)
        
    #----------------------------------------------------------------------
    def initCells(self):
        """初始化单元格"""
        
        l = ctaTaskPool.taskPool.allTask.items()
        self.setRowCount(len(l))
        row = 0
        
        for name, task in l:            
            cellTaskName  = QtGui.QTableWidgetItem(name)
            cellTaskTime  = QtGui.QTableWidgetItem(str(task.runTM))
            cellTaskRunM  = QtGui.QTableWidgetItem(task.runmode)
            cellStrCls    = QtGui.QTableWidgetItem(task.setting.get('className'))
            buttonActive  = TaskActiveButton(name)
            buttonParam   = TaskParamButton(name)
            buttonDisplay = TaskDisplayButton(name)
            buttonLog     = TaskLogButton(name)
            
            self.setItem(row, 0, cellTaskName)
            self.setItem(row, 1, cellStrCls)
            self.setItem(row, 2, cellTaskTime)
            self.setItem(row, 3, cellTaskRunM)
            self.setCellWidget(row, 4, buttonActive)
            self.setCellWidget(row, 5, buttonParam)
            self.setCellWidget(row, 6, buttonLog)
            self.setCellWidget(row, 7, buttonDisplay)
            
            self.buttonActiveDict[name] = buttonActive
            row += 1
            
    #----------------------------------------------------------------------
    def stopAll(self):
        """停止所有"""
        for button in self.buttonActiveDict.values():
            button.stop()     

    #----------------------------------------------------------------------
    def clearAll(self):
        """清空所有"""
        ctaTaskPool.taskPool.allTask = {}
        self.initCells()

########################################################################
class TaskManager(QtGui.QWidget):
    """任务管理主界面"""
    signal    = QtCore.pyqtSignal(type(Event()))
    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, eventEngine, parent=None):
        """Constructor"""
        super(TaskManager, self).__init__(parent)
       
        self.taskTab = TaskTable()
        self.eventEngine = eventEngine
        self.initUi()
        self.signal.connect(self.init)
        self.eventEngine.register(EVENT_TIMER, self.signal.emit)
        
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(u'任务管理')
        
        buttonStopAll = QtGui.QPushButton(u'全部停止')
        buttonStopAll.setObjectName(_fromUtf8('redButton'))
        buttonStopAll.clicked.connect(self.taskTab.stopAll)
        buttonClearAll = QtGui.QPushButton(u'清空所有')
        buttonClearAll.setObjectName(_fromUtf8('blueButton'))
        buttonClearAll.clicked.connect(self.taskTab.clearAll)
        hbox11 = QtGui.QHBoxLayout()     
        hbox11.addWidget(buttonStopAll)
        hbox11.addWidget(buttonClearAll)
        hbox11.addStretch()
        
        grid = QtGui.QVBoxLayout()
        grid.addLayout(hbox11)
        grid.addWidget(self.taskTab)

        self.setLayout(grid)
        
    #----------------------------------------------------------------------
    def show(self):
        """重载显示"""
        self.showMaximized()
        
    #----------------------------------------------------------------------
    def init(self):
        """初始化"""
        self.taskTab.initCells()

########################################################################
class TaskParamWidget(BasicDialog):
    """策略配置对话框"""

    index     = 0
    name      = ''
    paramDict = {}
    valueEdit = {}

    #----------------------------------------------------------------------
    def __init__(self, paramDict, parent=None):
        """Constructor"""
        super(TaskParamWidget, self).__init__(parent)
        self.valueEdit = {}
        self.paramDict = paramDict
        self.initUi()

    #----------------------------------------------------------------------
    def initUi(self):
        """"""
        QtGui.QWidget.__init__(self)         # 调用父类初始化方法
        self.setWindowTitle(u'设置参数')
        self.resize(300,400)                 # 设置窗口大小
        gridlayout = QtGui.QGridLayout()     # 创建布局组件
        i = 0
        lName  = QtGui.QLabel(u'参数')
        lValue = QtGui.QLabel(u'数值')
        gridlayout.addWidget(lName,  i, 0 )
        gridlayout.addWidget(lValue, i, 1 )
        for name in self.paramDict:
            i += 1
            label = QtGui.QLabel(name)                              # 创建单选框
            self.valueEdit[name] = QtGui.QLineEdit()
            self.valueEdit[name].setText(str(self.paramDict[name]))
            self.valueEdit[name].setFocusPolicy(QtCore.Qt.NoFocus)
            gridlayout.addWidget(label, i, 0 )                      # 添加文本
            gridlayout.addWidget(self.valueEdit[name], i,  1)       # 添加文本框

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(gridlayout)
        self.addButton(vbox)
        self.setLayout(vbox)                                    
