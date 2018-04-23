# encoding: UTF-8
'''
本文件中包含的是回测任务模块，用于回测任务的管理。
'''
import os
from datetime import datetime
import multiprocessing
########################################################################
def openLog(name):
    os.system('notepad log\{}.log'.format(name))

########################################################################
class ctaTask(multiprocessing.Process):
    """
    回测任务进程对象
    """
    #----------------------------------------------------------------------
    def __init__(self, name='', target= None, args=(), kwargs={},mode='front',showfunc=None,outq=None,runmode='bar'):
        """构造函数"""
        super(ctaTask,self).__init__(target=target,args=args,kwargs=kwargs)
        self.outq     = outq
        self.name     = name
        self.mode     = mode
        self.runmode  = runmode
        self.startTM  = None
        self.runTM    = None
        self.showfunc = showfunc
        if isinstance(args[0],dict) and 'name' in args[0]:
            args[0]['name'] = '.'.join([self.name,args[0]['name']])
            self.setting = args[0]
        else:
            self.setting = {}
        self.results  = {}
        self.state    = u'等待中'

    #----------------------------------------------------------------------
    def stopTask(self):
        """停止任务"""
        self.state = u'已停止'
        try:
            self.runTM = datetime.now()-self.startTM
            self.terminate()
        except:
            self.runTM = None
    
    #----------------------------------------------------------------------
    def startTask(self):
        """开始任务"""
        self.startTM = datetime.now()
        self.daemon = True
        self.start()
    
    #----------------------------------------------------------------------
    def update(self,setting,results,state):
        """更新任务完成"""
        if results:
            self.setting,self.results = setting,results
        self.state = state
        if self.state == u'已完成':
            self.runTM = datetime.now()-self.startTM

    #----------------------------------------------------------------------
    def run(self):
        """任务函数"""
        if self._target:
            setting,results = self._target(*self._args, **self._kwargs)
            self.outq.put(tuple([self.name,setting,results]))
    
    #----------------------------------------------------------------------
    def show(self):
        """显示结果"""
        if self.state == u'已完成':
            self.showfunc(self.results)

    #----------------------------------------------------------------------
    def log(self):
        """显示结果"""
        if self.state == u'已完成':
            p = multiprocessing.Process(target = openLog, args=(self.setting.get('name'),))
            p.start()
            


