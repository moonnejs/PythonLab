# coding: utf-8
"""
插入所有需要的库，和函数
"""
from ctaFunction import *
#----------------------------------------------------------------------
def klPnl(self):
    s = self.getInputParamByName('signalName')
    plotVarVPnl(self.spdData,s)

