# encoding: UTF-8
import talib
import numpy as np

def reverse(pdBars,rLimit=0.01):
    size   = len(pdBars.index)
    pclose = pdBars['close'].values
    phigh  = pdBars['high'].values
    plow   = pdBars['low'].values
    popen  = pdBars['open'].values
    pratio = (pclose-popen)/pclose
    hhv    = popen + rLimit*pclose
    llv    = popen - rLimit*pclose
    sigOpen = np.zeros(size)
    sigOpen[pratio>rLimit] = -1
    sigOpen[pratio<-rLimit] = 1
    return {"dealOpen":sigOpen,
            "deal":sigOpen,
            "pnl":np.zeros(size),
            "state":{'hhv':hhv,'llv':llv}}
