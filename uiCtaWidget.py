# encoding: UTF-8
'''
CTA模块相关的GUI控制组件
'''
import matplotlib
matplotlib.use('Qt4Agg')
import imp
import sip
API_NAMES = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
API_VERSION = 2
for name in API_NAMES:
    sip.setapi(name, API_VERSION)
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import os
os.environ['QT_API'] = 'pyqt'

from eventEngine import *
from uiBasicWidget import *
import ctaTaskPool
from ctaBase import *
from ctaFunction import *
from uiCtaKLine import ctaKLine
from uiCtaTaskWidget import TaskManager
from QIPythonWidget import QIPythonWidget

from tools.ctaHistoryData import *
from ctaEngine import CtaEngine

# 字符串转换
#---------------------------------------------------------------------------------------
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

########################################################################
class CtaKLineManager(QMainWindow):
    """K线管理组件"""

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, eventEngine, title = 'K线分析工具', parent=None):
        """Constructor"""
        super(CtaKLineManager, self).__init__(parent)
        
        self.ctaEngine = ctaEngine
        self.eventEngine = eventEngine
        self.title = title
        
        self.widgetDict = {}
        self.strategyLoaded = False
        
        self.initUi()
        
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(self.title)
        self.widgetCMDM,  dockCMDM    = self.createDock(QIPythonWidget, u'命令行',   QtCore.Qt.LeftDockWidgetArea)
        self.widgetVECM,  dockVECM    = self.createDock(VectorManager, u'向量回测', QtCore.Qt.LeftDockWidgetArea)
        self.widgetKLineM, dockKLineM = self.createDock(ctaKLine, u'K线工具', QtCore.Qt.RightDockWidgetArea)

        self.tabifyDockWidget(dockCMDM, dockVECM)
        dockVECM.raise_()
        
    #----------------------------------------------------------------------
    def createDock(self, widgetClass, widgetName, widgetArea):
        """创建停靠组件"""
        widget = widgetClass(self.ctaEngine, self.eventEngine, self)
        dock = QDockWidget(widgetName)
        dock.setWidget(widget)
        dock.setObjectName(widgetName)
        dock.setFeatures(dock.DockWidgetFloatable|dock.DockWidgetMovable)
        self.addDockWidget(widgetArea, dock)
        return widget, dock
        
########################################################################
class CtaEngineManager(QMainWindow):
    """CTA引擎管理组件"""

    signal    = QtCore.Signal(type(Event()))
    signalL   = QtCore.Signal(type(Event()))
    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, eventEngine, title = 'ctaStrategy', parent=None):
        """Constructor"""
        super(CtaEngineManager, self).__init__(parent)
        
        self.ctaEngine = ctaEngine
        self.eventEngine = eventEngine
        self.title = title
        
        self.widgetDict = {}
        self.strategyLoaded = False
        
        self.initUi()
        self.registerEvent()

        self.load()
        
        # 记录日志
        self.ctaEngine.writeCtaLog(u'CTA引擎启动成功')        
        
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(self.title)
        
        self.widgetFileM, dockFileM = self.createDock(FileManager, u'策略管理', QtCore.Qt.LeftDockWidgetArea)
        self.widgetBtM,   dockBtM   = self.createDock(StrategyBtManager, u'回测实例', QtCore.Qt.LeftDockWidgetArea)
        self.widgetPrmM,  dockPrmM  = self.createDock(StrategyParamManager, u'开始回测',   QtCore.Qt.RightDockWidgetArea)
        self.widgetTaskM, dockTaskM = self.createDock(TaskManager, u'任务管理', QtCore.Qt.RightDockWidgetArea)
        self.widgetLogM,  dockLogM  = self.createDock(ctaLogMonitor, u'日志',   QtCore.Qt.RightDockWidgetArea)

        self.tabifyDockWidget(dockFileM, dockBtM)
        dockBtM.raise_()
        
    #----------------------------------------------------------------------
    def initStrategyManager(self):
        """初始化策略管理组件界面"""        
        self.widgetBtM.modelBt.updateData()

    #----------------------------------------------------------------------
    def createDock(self, widgetClass, widgetName, widgetArea):
        """创建停靠组件"""
        widget = widgetClass(self.ctaEngine, self.eventEngine, self)
        dock = QDockWidget(widgetName)
        dock.setWidget(widget)
        dock.setObjectName(widgetName)
        dock.setFeatures(dock.DockWidgetFloatable|dock.DockWidgetMovable)
        self.addDockWidget(widgetArea, dock)
        return widget, dock
        
    #----------------------------------------------------------------------
    def updateParam(self,name):
        """刷新参数"""        
        self.widgetPrmM.updateParam(name)
        self.widgetBtM.modelBt.updateData(name)
        
    #----------------------------------------------------------------------
    def load(self):
        """加载策略"""
        self.ctaEngine.loadSetting()
        self.initStrategyManager()
        self.strategyLoaded = True
        self.ctaEngine.writeCtaLog(u'策略加载成功')
            
    #----------------------------------------------------------------------
    def delete(self, name):
        """删除策略"""
        del self.ctaEngine.strategyDict[name]
        self.ctaEngine.saveSetting()
        self.load()
            
    #----------------------------------------------------------------------
    def updateCtaLog(self, event):
        """更新CTA相关日志"""
        log = event.dict_['data']
        content = '\t'.join([log.logTime, log.logContent])
        self.widgetLogM.append(content)
    
    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.signal.connect(self.updateCtaLog)
        self.eventEngine.register(EVENT_CTA_LOG, self.signal.emit)
        self.signalL.connect(self.load)
        self.eventEngine.register(EVENT_CTA_STRATEGY_LOAD, self.signalL.emit)


########################################################################
class ctaLogMonitor(QTextEdit):
    """日志管理"""

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, eventEngine, parent=None):
        """Constructor"""
        super(ctaLogMonitor, self).__init__(parent)

        # CTA组件的日志监控
        self.setReadOnly(True)
        #self.setMaximumHeight(200)

########################################################################
class FileManager(BasicDialog):
    """文件管理"""

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, eventEngine, parent=None):
        """Constructor"""
        super(FileManager, self).__init__(parent)
      
        self.parent = parent
        self.ctaEngine = ctaEngine
        self.eventEngine = eventEngine
        self.setFixedWidth(420)
       
        self.widgetDict = {} 
        self.initUi()  

    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(u'策略管理')
        QtCore.QTextCodec.setCodecForTr(QtCore.QTextCodec.codecForName("utf-8"))  

        # 设置布局
        hbox = QHBoxLayout()
        self.hboxAddButton(hbox,u'导入','greenButton',self.data)
        self.hboxAddButton(hbox,u'发布','redButton',self.data)
        self.hboxAddButton(hbox,u'加载数据','redButton',self.data)
        hbox.addStretch()

        self.tbView = QTreeView()
  
        model=QFileSystemModel()
        model.setRootPath(QtCore.QDir.currentPath())
        model.setNameFilters(["*.py"])
        model.setNameFilterDisables(False);
        model.setHeaderData(0, QtCore.Qt.Horizontal, _fromUtf8(u"策略名称"))
          
        self.tbView.setModel(model)  
        self.tbView.setSelectionModel(QItemSelectionModel(model))  
        self.tbView.setRootIndex(model.index(".\\strategy"))
        self.tbView.setHeaderHidden(True)
        self.tbView.hideColumn(1)
        self.tbView.hideColumn(2)
        self.tbView.hideColumn(3)
        QtCore.QObject.connect(self.tbView,QtCore.SIGNAL("doubleClicked(QModelIndex)"),self.addStrategy)  

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.tbView)
        self.setLayout(vbox)
          
    #----------------------------------------------------------------------
    def addStrategy(self,index):
        """显示策略"""
        filename=self.tbView.model().data(index,0)
        if '.py' in filename:
            self.add(filename.split('.')[0])

    #----------------------------------------------------------------------
    def add(self,filename):
        """新增回测组合"""
        try:
            self.widgetDict['ssetW'].sClass.setText(filename)
            self.widgetDict['ssetW'].show()
        except KeyError:
            self.widgetDict['ssetW'] = StrategyAddWidget(self.ctaEngine, self.eventEngine, self)
            self.widgetDict['ssetW'].sClass.setText(filename)
            self.widgetDict['ssetW'].show()

    #----------------------------------------------------------------------
    def data(self):
        """加载数据"""
        print(u'\n'+'#'*60)
        print(u'正在加载数据..')
        temp_Path=['.\\historyData']
        for c in temp_Path :
            path = c
            loadAllFileTick(path,TICK_DB_NAME,mode='ctpen')
        print(u'数据加载完成')

########################################################################
class VectorManager(BasicDialog):
    """向量化回测管理"""

    signalBT  = QtCore.Signal(type(Event()))
    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, eventEngine, parent=None):
        """Constructor"""
        super(VectorManager, self).__init__(parent)
      
        self.parent = parent
        self.ctaEngine = ctaEngine
        self.eventEngine = eventEngine
        self.setFixedWidth(420)
        self.pdBars = None
        self.vecFunc = None
       
        self.widgetDict = {} 
        self.initUi()  
        self.signalBT.connect(self.vecBt)
        self.eventEngine.register(EVENT_F5, self.signalBT.emit)

    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(u'向量回测')
        QtCore.QTextCodec.setCodecForTr(QtCore.QTextCodec.codecForName("utf-8"))  

        # 设置布局
        hbox = QHBoxLayout()
        self.hboxAddButton(hbox,u'载入数据','greenButton',self.loadData)
        self.hboxAddButton(hbox,u'向量回测','redButton',self.vecBt)
        hbox.addStretch()

        gridlayout = QGridLayout()
        self.symbolEdit = self.gridAddLineEditV(gridlayout,u'合约',0)
        self.startEdit  = self.gridAddLineEditV(gridlayout,u'开始时间',1)
        self.endEdit    = self.gridAddLineEditV(gridlayout,u'结束时间',2)
        self.periodType = self.gridAddComboBoxV(gridlayout,u'周期',['','5','15','25','60','D'],3)

        self.tbView = QTreeView()
  
        model=QFileSystemModel()
        model.setRootPath(QtCore.QDir.currentPath())
        model.setNameFilters(["*.py"])
        model.setNameFilterDisables(False);
        model.setHeaderData(0, QtCore.Qt.Horizontal, _fromUtf8(u"策略名称"))
          
        self.tbView.setModel(model)  
        self.tbView.setSelectionModel(QItemSelectionModel(model))  
        self.tbView.setRootIndex(model.index(".\\vecsig"))
        self.tbView.setHeaderHidden(True)
        self.tbView.hideColumn(1)
        self.tbView.hideColumn(2)
        self.tbView.hideColumn(3)
        QtCore.QObject.connect(self.tbView,QtCore.SIGNAL("doubleClicked(QModelIndex)"),self.selStrategy)  

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(gridlayout)
        vbox.addWidget(self.tbView)
        self.setLayout(vbox)
          
    #----------------------------------------------------------------------
    def contextMenuEvent(self, evt):
        pos = evt.pos()
        if self.selectionModel().selection().indexes():
            for i in self.tbView.selectionModel().selection().indexes():
                row, column = i.row(), i.column()
            menu = QMenu()
            openAction = menu.addAction(u"打开")
            deleAction = menu.addAction(u"删除")
            renaAction = menu.addAction(u"重命名")
            action = menu.exec_(self.mapToGlobal(pos))
            if action ==openAction:
                self.openAction(row, column)
    
    #----------------------------------------------------------------------
    def openAction(self, row, column):
        pass

    #----------------------------------------------------------------------
    def selStrategy(self,index):
        """选择策略"""
        filename =self.tbView.model().data(index,0)
        path=self.tbView.model().filePath(index)
        if '.py' in filename: 
            self.path = path
            self.name = filename.split('.')[0]
            imp.load_source("vecsig", path.encode('gbk'))
            self.vecFunc = getattr(sys.modules['vecsig'], self.name)

    #----------------------------------------------------------------------
    def vecBt(self):
        """向量回测"""
        imp.load_source("vecsig", self.path.encode('gbk'))
        self.vecFunc = getattr(sys.modules['vecsig'], self.name)
        if not (self.pdBars is None or self.vecFunc is None):
            sigData = self.vecFunc(self.pdBars)
            kTool   = self.parent.widgetKLineM
            kTool.loadSig(sigData)
            wLimit    = kTool.getInputParamByName('wLimit')
            cLimit    = kTool.getInputParamByName('cLimit')
            size      = kTool.getInputParamByName('size')
            sLippage  = kTool.getInputParamByName('sLippage')
            tickers   = pd.DataFrame()
            tickers['askPrice1'] = kTool.pdBars['open']+sLippage
            tickers['bidPrice1'] = kTool.pdBars['open']-sLippage
            markets   = tickers.values
            signals   = np.array(kTool.signalsOpen)
            plotSigCaps(tickers.index.to_pydatetime(),signals,markets,cLimit,wLimit,size=size)

    #----------------------------------------------------------------------
    def loadData(self):
        """加载数据"""
        symbol    = str(self.symbolEdit.text())
        startTime = str(self.startEdit.text())
        endTime   = str(self.endEdit.text())
        pType     = 'B'+str(self.periodType.currentText())
        DB_NAME   = getDbByMode(pType)
        pdData    = loadHistoryData(DB_NAME, symbol, startTime, endTime,
        fields=['datetime','open','close','low','high','volume','openInterest'],pdformat=False)
        length    = pdData.count()
        if self.parent:
            self.parent.widgetKLineM.loadData({'bar':pdData,
                                               'state':{},
                                               'pnl':np.zeros(length),
                                               'deal':np.zeros(length),
                                               'dealOpen':np.zeros(length)})
        self.pdBars = self.parent.widgetKLineM.pdBars
        print(u'数据加载完成')
            
            
########################################################################
class StrategyParamManager(BasicDialog):
    """参数配置界面"""

    signal    = QtCore.Signal(type(Event()))
    signalBT  = QtCore.Signal(type(Event()))
    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, eventEngine, master=None):
        """Constructor"""
        super(StrategyParamManager, self).__init__(None)
      
        self.eventEngine = eventEngine
        self.ctaEngine = ctaEngine
        self.master = master
        self.name = None

        self.widgetDict = {}
        self.widgetDict['bktW'] = {}
        self.widgetDict['ssetW'] = {}
        self.widgetDict['infoW'] = {}
        self.widgetDict['rollingW'] = {}
        self.widgetDict['splitW'] = {}

        self.initUi()  
        self.registerEvent()

    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(u'策略参数')
        #self.setMaximumHeight(250)
        allModes = ['TICK','TICK(CPP)','TICK(PERF)','BAR','BAR(PERF)','BAR(DISPLAY)']
        gridlayout = QGridLayout()
        self.startEdit  = self.gridAddLineEditV(gridlayout,u'开始时间',0)
        self.endEdit    = self.gridAddLineEditV(gridlayout,u'结束时间',1)
        self.modeType   = self.gridAddComboBoxV(gridlayout,u'回测模式',allModes,2)
        self.periodType = self.gridAddComboBoxV(gridlayout,u'周期',['','5','15','25','60','D'],3)
        self.spEdit     = self.gridAddLineEditV(gridlayout,u'策略滑点',4)

        self.startEdit.setText('20161001')
        self.endEdit.setText('20161030')
        self.spEdit.setText('0')
        
        QtCore.QTextCodec.setCodecForTr(QtCore.QTextCodec.codecForName("utf-8"))  

        self.btView = QTableView()
  
        self.modelP=StrategyParam(self.eventEngine,self.ctaEngine)
        self.btView.setModel(self.modelP)  
          
        self.btView.horizontalHeader().setStretchLastSection(True)
        self.btView.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.btView.setEditTriggers(QTableWidget.NoEditTriggers)
        self.btView.setSelectionBehavior(QTableWidget.SelectRows)

        hbox = QHBoxLayout()     
        self.hboxAddButton(hbox,u'回测','redButton',self.backtest)
        self.hboxAddButton(hbox,u'分段回测','blueButton',self.splitBt)
        self.hboxAddButton(hbox,u'全部回测','redButton',self.btAll)
        self.hboxAddButton(hbox,u'参数扫描','blueButton',self.optimize)
        self.hboxAddButton(hbox,u'滚动优化','greenButton',self.rollingOp)
        self.hboxAddButton(hbox,u'聚合K线', 'redButton', self.createXbars)
        self.switchModeButton = self.hboxAddButton(hbox,u'切换模式（延时）','blueButton',self.switchMode)
        hbox.addStretch()

        hbox1 = QHBoxLayout()     
        hbox1.addLayout(gridlayout)
        hbox1.addStretch()

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(hbox1)
        vbox.addWidget(self.btView)
        self.setLayout(vbox)

        QtCore.QObject.connect(self.btView,QtCore.SIGNAL("doubleClicked(QModelIndex)"),self.editParam)  

    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.signal.connect(self.updateParam)
        self.eventEngine.register(EVENT_CTA_STRATEGY_PARAM, self.signal.emit)
        self.signalBT.connect(self.backtest)
        self.eventEngine.register(EVENT_F2, self.signalBT.emit)

    #----------------------------------------------------------------------
    def getBtMode(self):
        """获取回测模式"""
        pType = str(self.periodType.currentText())
        if str(self.modeType.currentText()) == 'TICK':
            mode = 'T'+pType
        elif str(self.modeType.currentText()) == 'TICK(PERF)':
            mode = 'TP'+pType
        elif str(self.modeType.currentText()) == 'TICK(CPP)':
            mode = 'TC'+pType
        elif str(self.modeType.currentText()) == 'BAR':
            mode = 'B'+pType
        elif str(self.modeType.currentText()) == 'BAR(PERF)':
            mode = 'BP'+pType
        elif str(self.modeType.currentText()) == 'BAR(DISPLAY)':
            mode = 'BV'+pType
        return mode

    #----------------------------------------------------------------------
    def backtest(self,evt=None,name=None):
        """启动回测"""
        name0 = self.name if not name else name
        if name0 is None: return 
        startTime = str(self.startEdit.text())
        endTime   = str(self.endEdit.text())
        sp        = eval(str(self.spEdit.text()))
        mode      = self.getBtMode()
        self.ctaEngine.backtestStrategy(name0,startTime,endTime,sp,mode)

    #----------------------------------------------------------------------
    def createXbars(self):
        """启动回测"""
        name = self.name
        startTime = str(self.startEdit.text())
        endTime   = str(self.endEdit.text())
        xMin      = str(self.periodType.currentText())
        mode      = self.getBtMode()
        symbol    = self.ctaEngine.getStrategyParam(self.name).get('vtSymbol')
        if xMin == '':
            loadHistoryBarByTick(TICK_DB_NAME, symbol, start=startTime, end=endTime, nMin = 1)
        else:
            generateXbars(symbol, startTime, endTime, xMin, mode)

    #----------------------------------------------------------------------
    def btAll(self):
        """全部回测"""
        for name in self.ctaEngine.strategyDict:
            self.backtest(name=name)
        
    #----------------------------------------------------------------------
    def editParam(self):
        """配置策略参数"""
        if self.name is None: return
        try:
            self.widgetDict['ssetW'][self.name].show()
        except KeyError:
            self.widgetDict['ssetW'][self.name] = StratrgySettingWidget(self.name,self.ctaEngine,self.eventEngine,self)
            self.widgetDict['ssetW'][self.name].show()
            
    #----------------------------------------------------------------------
    def optimize(self):
        """启动回测"""
        if self.name is None: return
        try:
            self.widgetDict['infoW'][self.name].show()
        except KeyError:
            self.widgetDict['infoW'][self.name] = InfoInputWidget(self.name,self.ctaEngine,self)
            self.widgetDict['infoW'][self.name].show()
        
    #----------------------------------------------------------------------
    def rollingOp(self,name):
        """启动滚动优化回测"""
        if self.name is None: return
        try:
            self.widgetDict['rollingW'][self.name].show()
        except KeyError:
            self.widgetDict['rollingW'][self.name] = RollingInputWidget(self.name,self.ctaEngine,self)
            self.widgetDict['rollingW'][self.name].show()

    #----------------------------------------------------------------------
    def splitBt(self,name):
        """启动滚动优化回测"""
        if self.name is None: return
        try:
            self.widgetDict['splitW'][self.name].show()
        except KeyError:
            self.widgetDict['splitW'][self.name] = SplitInputWidget(self.name,self.ctaEngine,self)
            self.widgetDict['splitW'][self.name].show()

    #----------------------------------------------------------------------
    def switchMode(self):
        """切换回测模式"""
        if not self.ctaEngine.optimism:
            self.ctaEngine.optimism = True
            self.switchModeButton.setText(u'切换模式（及时）')
        else:
            self.ctaEngine.optimism = False
            self.switchModeButton.setText(u'切换模式（延时）')
        
    #----------------------------------------------------------------------
    def updateParam(self,evt):
        """刷新数据"""
        name = evt.dict_['data']
        self.name = name
        self.modelP.updateData(name)
    
########################################################################
class StrategyBtManager(BasicDialog):
    """回测实例管理"""

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, eventEngine, master=None):
        """Constructor"""
        super(StrategyBtManager, self).__init__(None)
      
        self.eventEngine = eventEngine
        self.ctaEngine = ctaEngine
        self.master = master
        self.name = None

        
        self.initUi()  

    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(u'策略管理')
        
        QtCore.QTextCodec.setCodecForTr(QtCore.QTextCodec.codecForName("utf-8"))  

        hbox = QHBoxLayout()     
        self.hboxAddButton(hbox,u'删除','greenButton',self.delete)
        self.hboxAddButton(hbox,u'组合报告','blueButton',self.report)
        hbox.addStretch()
        
        self.tbView = QTreeView()
        self.modelBt=StrategyBacktesting(self.eventEngine,self.ctaEngine,self.tbView)
        self.modelBt.updateData()

        self.tbView.setModel(self.modelBt)  
        self.tbView.setSelectionModel(QItemSelectionModel(self.modelBt))  

        self.tbView.setColumnWidth(0, 200)
        self.tbView.setItemsExpandable(False)
        self.tbView.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbView.setSelectionBehavior(QTableWidget.SelectRows)

        QtCore.QObject.connect(self.tbView,QtCore.SIGNAL("clicked(QModelIndex)"),self.showStrategy)  

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.tbView)
        self.setLayout(vbox)

    #----------------------------------------------------------------------
    def showStrategy(self,index):
        """显示策略"""
        item = self.tbView.model().itemFromIndex(index.sibling(index.row(),0))
        self.name = item.data(0)
        if self.name in self.tbView.model().nameItems:
            event = Event(EVENT_CTA_STRATEGY_PARAM)
            event.dict_['data'] = self.name
            self.master.updateParam(event)
            for i in range(self.tbView.model().nRow):
                self.tbView.model().checkName(self.name)

    #----------------------------------------------------------------------
    def delete(self):
        """删除策略"""
        if self.name is None: return
        self.master.delete(self.name)
        self.modelBt.updateData()
        self.tbView.expandAll()
            
    #----------------------------------------------------------------------
    def report(self):
        """启动报告"""
        self.ctaEngine.reportStrategy()
        
########################################################################
class TabWidget(QTabWidget):
    def __init__(self, eventEngine, ctaEngine, parent=None):
        super(TabWidget, self).__init__(parent)
        # 创建事件引擎
        import uiCtaTaskWidget
        self.ee = eventEngine
        self.ce = ctaEngine
        self.setWindowTitle(u'回测工具')
        self.fWindow = CtaEngineManager(ctaEngine,eventEngine,u'回测引擎')
        self.kWindow = CtaKLineManager(ctaEngine,eventEngine,u'结果分析')
        uiCtaTaskWidget.kLoader = self.kWindow.widgetKLineM
        iWindow = self.kWindow.widgetCMDM
        iWindow.execute_command('from ctaFunction import *')
        iWindow.pushVariables({'kTool':self.kWindow.widgetKLineM})
        self.addTab(self.fWindow,u"策略回测")
        self.addTab(self.kWindow,u"结果分析")

    #----------------------------------------------------------------------
    def closeEvent(self, event):
        """关闭事件"""
        self.ee.stop()
        ctaTaskPool.taskPool.stopTaskPool()
        event.accept()

#----------------------------------------------------------------------
def main():
    """主程序入口"""
    # 初始化Qt应用对象
    ee = EventEngine2()
    ce = CtaEngine(None,ee)
    ee.start()
    app = btQApp(sys.argv,ee)
    app.mainWindow = TabWidget(ee,ce)
    app.mainWindow.showMaximized()
    regHotKey(app.mainWindow.winId(),116)
    regHotKey(app.mainWindow.winId(),113)
    
    # 设置Qt的皮肤
    try:
        import qdarkstyle
    except:
        pass

    # 界面设置
    cfgfile = QtCore.QFile('css.qss')
    cfgfile.open(QtCore.QFile.ReadOnly)
    styleSheet = cfgfile.readAll()
    styleSheet = unicode(styleSheet, encoding='utf8')
    app.setStyleSheet(styleSheet)
    
    # 在主线程中启动Qt事件循环
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()
