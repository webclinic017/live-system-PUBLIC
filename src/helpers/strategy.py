import datetime as dt
import pandas as pd
import numpy as np
from . import configs
from . import management
logger = configs.logger()

#### code redacted ####

''' Systems '''
def executeBinarySystem(app, tickers, contract_set, forecast_dict:dict, entry_threshold, exit_threshold):
    pass

def executeContinuousSystem():
    pass

''' Forecast concatenation and calculation '''
def calcForecast(tickers, strategies:list):
    pass
    
def combine_forecasts(d:dict):
    # this is for combining raw forecast values together -- according to portfolio weights
    pass

''' Strategy / rules ''' 
# Strategies() return pd series with column = ['Forecast'] and datetimeindex
def strategy1(ticker, window):
    pass

def strategy2(ticker):
    pass

def strategy3(ticker, window):
    pass

''' Position sizing and vol normalisation '''
def positionSizer(ticker, forecast):
    pass
