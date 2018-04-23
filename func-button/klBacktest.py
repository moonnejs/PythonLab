# coding: utf-8
"""
插入所有需要的库，和函数
"""
import numpy as np
from ctaFunction.calcFunction import *
from ctaFunction.visFunction import *

#----------------------------------------------------------------------
def klBacktest(self):
    wLimit    = self.getInputParamByName('wLimit')
    cLimit    = self.getInputParamByName('cLimit')
    size      = self.getInputParamByName('size')
    sLippage  = self.getInputParamByName('sLippage')
    tickers   = pd.DataFrame()
    tickers['bidPrice1'] = self.pdBars['open']-sLippage
    tickers['askPrice1'] = self.pdBars['open']+sLippage
    markets   = tickers.values
    signals   = np.array(self.signalsOpen)
    plotSigCaps(tickers.index.to_pydatetime(),signals,markets,cLimit,wLimit,size=size)
