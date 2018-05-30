# encoding: UTF-8
'''
本文件中包含的是回测任务模块，用于回测任务的管理。
'''
from Queue import Queue, Empty
import cProfile,pstats
import traceback
import multiprocessing
from ctaTask import ctaTask
from threading import Thread
from ctaBacktesting import backtesting,optimize,showBtResult,runParallelOptimization,backtestingRolling

# 无日志回测单个策略
#---------------------------------------------------------------------------------------
def optimizeB(setting_bt, StartTime = '', EndTime = '', slippage = 0, optimism = False, mode = 'T', q = False):
    """回测单个策略"""
    try:
        return optimize(setting_bt, {}, StartTime, EndTime, slippage, optimism, mode)
    except Exception, e:
        print(u'回测策略出错：%s' %e)
        print 'traceback.print_exc():'; traceback.print_exc()
        return setting_bt['name'],{},0

# 含日志回测单个策略
#---------------------------------------------------------------------------------------
def backtestingE(setting_bt, StartTime = '', EndTime = '', slippage = 0, optimism = False, mode = 'T', q = False):
    """回测单个策略"""
    try:
        return backtesting(setting_bt, StartTime, EndTime, slippage, optimism, mode, q)
    except Exception, e:
        print(u'回测策略出错：%s' %e)
        print 'traceback.print_exc():'; traceback.print_exc()
        return setting_bt['name'],{},0

# 使用C++引擎回测单个策略
#---------------------------------------------------------------------------------------
def backtestingC(setting_bt, StartTime = '', EndTime = '', slippage = 0, optimism = False, mode = 'T', q = False):
    """回测单个策略"""
    try:
        return backtesting(setting_bt, StartTime, EndTime, slippage, optimism, mode, q, runmode='CPP')
    except Exception, e:
        print(u'回测策略出错：%s' %e)
        print 'traceback.print_exc():'; traceback.print_exc()
        return setting_bt['name'],{},0

# 无日志回测单个策略，同时分析性能
#---------------------------------------------------------------------------------------
def backtestingPerfE(setting_bt, StartTime = '', EndTime = '', slippage = 0, optimism = False, mode = 'T', q = False):
    """回测单个策略,同时分析性能"""
    try:
        p = cProfile.Profile()       
        p.enable()
        res = backtesting(setting_bt, StartTime, EndTime, slippage, optimism, mode, q)
        p.disable()
        p.create_stats()
        stats = pstats.Stats(p)
        stats.sort_stats('tottime').print_stats(20)
        return res
    except Exception, e:
        print(u'回测策略出错：%s' %e)
        print 'traceback.print_exc():'; traceback.print_exc()
        return setting_bt['name'],{},0

# 滚动分析，回测单个策略
#---------------------------------------------------------------------------------------
def backtestingRollingE(setting_bt, optimizationSetting, StartTime = '', EndTime = '', RollingDays = 20,  slippage = 0, optimism = False, mode = 'T', q = False):
    """滚动回测单个策略"""
    try:
        return backtestingRolling(setting_bt, optimizationSetting, StartTime, EndTime, RollingDays, slippage, optimism, mode, q)
    except Exception, e:
        print(u'回测策略出错：%s' %e)
        print 'traceback.print_exc():'; traceback.print_exc()
        return setting_bt['name'],{},0

# 参数扫描
#---------------------------------------------------------------------------------------
def optimizeE(setting_bt, optimizationSetting, StartTime = '20161001', EndTime = '20161030', slippage = 0, optimism = False, mode = 'T',q=False):
    """对策略参数扫描"""
    try:
        return runParallelOptimization(setting_bt,optimizationSetting,optimism,StartTime,EndTime,slippage,mode)
    except Exception, e:
        print(u'回测策略出错：%s' %e)
        print 'traceback.print_exc():'; traceback.print_exc()
        return setting_bt['name'],{},0

taskPool = None
########################################################################
class ctaTaskPool(object):
    """
    回测任务池
    """
    MAX_RUNNING_TASK = 4
    taskCount = 0
    allTask = {}
    #----------------------------------------------------------------------
    def __init__(self,ee=None):
        """构造函数"""
        self.ee          = ee
        self.inq         = Queue()
        self.outq        = multiprocessing.Queue()
        self.thread      = Thread(target=self.runTask) 
        self.__active    = False
        self.workingTask = []
        self.startTaskPool()
    
    #---------------------------------------------------------------------------------------
    def runTask(self):
        """监听函数"""
        while self.__active:
            try:
                if len(self.workingTask) < self.MAX_RUNNING_TASK:
                    task = self.inq.get(block=True ,timeout=1)
                    task.update(None,None,u'运行中')
                    task.startTask()
                    self.workingTask.append(task) 
            except Empty:
                pass
            try:
                name,setting,results = self.outq.get(block=True ,timeout=1)
                self.allTask.get(name).update(setting,results,u'已完成')
                self.allTask.get(name).terminate()
                self.workingTask.remove(self.allTask.get(name))
            except Empty:
                pass
    
    #-----------------------------------------------
    def startTaskPool(self):
        """开始监听任务队列"""
        self.__active = True
        self.thread.start()
    
    #-----------------------------------------------
    def stopTaskPool(self):
        """结束监听任务队列"""
        self.__active = False
        self.thread.join()
    
    # 任务相关
    #---------------------------------------------------------------------------------------
    def addTask(self, name='', args=(), kwargs={}, mode='bt-f', runmode = 'bar'):
        """新增任务"""
        name0 = '-'.join([name,str(self.taskCount)])
        target  = backtestingE if mode == 'bt-f' else \
                  backtestingC if mode == 'bt-c' else\
                  backtestingPerfE if mode == 'bt-perf' else\
                  optimizeE if mode == 'op' else\
                  backtestingRollingE if mode == 'bt-r' else optimizeB
        self.allTask[name0] = ctaTask(name0, target, args, kwargs, mode, showfunc = showBtResult, outq=self.outq, runmode=runmode)
        self.inq.put(self.allTask[name0])
        self.taskCount +=1
        return name0
    
    #---------------------------------------------------------------------------------------
    def getTask(self, name=''):
        """获取任务"""
        return self.allTask[name]
    
    #---------------------------------------------------------------------------------------
    def startTask(self, name=''):
        """停止任务"""
        self.allTask[name].startTask()
    
    #---------------------------------------------------------------------------------------
    def stopTask(self, name=''):
        """停止任务"""
        self.allTask[name].stopTask()
        if self.allTask.get(name) in self.workingTask:
            self.workingTask.remove(self.allTask.get(name))

