# coding: utf-8
"""
插入所有需要的库，和函数
"""
from ctaFunction import *
#----------------------------------------------------------------------
def klAna(self):
    data = self.spdData.copy()
    data['pnl'] = ['p' if d > 0 else 'l' for d in data['pnl']]
    plotFactors(data)

