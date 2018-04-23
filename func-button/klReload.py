# coding: utf-8
"""
插入所有需要的库，和函数
"""
#----------------------------------------------------------------------
def klReload(self):
    self.editDict['signalName'].clear()
    self.editDict['signalName'].addItems(ctaBase.ALL_BAR_SIGNALS)
