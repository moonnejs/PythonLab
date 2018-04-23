# encoding: UTF-8
import talib
import numpy as np

def trends(pdBars):
    size  = len(pdBars.index)
    close = pdBars['close'].values
    ma10  = talib.SMA(close,5)
    ma20  = talib.SMA(close,26)
    sigOpen = np.zeros(size)
    sigOpen[(ma10<ma20)&np.roll(ma10>ma20,1)] = -1
    sigOpen[(ma10>ma20)&np.roll(ma10<ma20,1)] = 1
    return {"dealOpen":sigOpen,
            "deal":sigOpen,
            "pnl":np.zeros(size),
            "state":{'ma10':ma10,'ma20':ma20}}
