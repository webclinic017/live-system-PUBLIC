import requests
import datetime as dt
import pandas as pd
import pytz
import itertools
from . import configs 
from . import management 
logger = configs.logger()

def send_message(where, message, code_block_fmt=False):
    token, chat_id, func = configs.auth_alert(where)
    utc_now = dt.datetime.utcnow().strftime("%Y%m%d %H:%M:%S\n")
    text = utc_now + message
    
    if code_block_fmt:
        text = f"<code>{text}</code>"

    params = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    resp = requests.post(func.format(token), params)
    resp.raise_for_status() 


def getActiveCarryContracts(tickers,date_str): 
    # returns dictionary of {tickers: (activemonth, carrymonth, distance in years)}
    df = pd.read_csv(configs.roll_schedule_path())
    df['StartDate'] = pd.to_datetime(df['StartDate'], format="%Y%m%d")
    
    date = dt.datetime.strptime(date_str, "%Y%m%d %H:%M:%S")
    live_contracts = {}
    for ticker in tickers:
        sortby_ticker = df.loc[df['Symbol']==ticker]
        contract_activated = [x for x in sortby_ticker['StartDate'] if date >= x] 
        most_recent_activation = contract_activated[-1]
        live_contract = sortby_ticker.loc[sortby_ticker['StartDate']==most_recent_activation]
        
        active_month = live_contract['ActiveMonth'].iloc[0]
        carry_month = live_contract['CarryMonth'].iloc[0]

        if ticker in ['ZC','ZW','ZS']: #ECBOT has different localsymbol, very unfortunate hardcoding here...
            all_months = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
            active_letter = active_month[-6:-3] # "ZC   DEC 21"[-6:-3] = DEC (december)
            carry_letter = carry_month[-6:-3] # "ZC   NOV 21"[-6:-3] = NOV (november)
            i = (all_months.index(active_letter) - all_months.index(carry_letter)) % len(all_months) 
            j = (all_months.index(carry_letter) - all_months.index(active_letter)) % len(all_months) 
            distance = min(i,j) / 12
                        
        else:  
            # calculating distance between carry and actives (in years)
            all_months = ['F','G','H','J','K','M','N','Q','U','V','X','Z']
            active_letter = active_month[-2] # "VXZ1"[-2] = Z (december)
            carry_letter = carry_month[-2] # "VXX1"[-2] = X (november)
            i = (all_months.index(active_letter) - all_months.index(carry_letter)) % len(all_months) 
            j = (all_months.index(carry_letter) - all_months.index(active_letter)) % len(all_months) 
            distance = min(i,j) / 12
        
        live_contracts[ticker] = (active_month, carry_month, distance)
    
    return live_contracts

def getHistData(app, tickers, contract_set, end_time, duration, candle_size):
    # returns dict {ticker/leg: histdata_df}
    data = {}
    for ticker in tickers:
        for leg in ["c1","c2"]:
            app.hist_end_event.clear()
            app.reqHistoricalData(reqId=tickers.index(ticker),
                                  contract=management.createContract(ticker, leg, contract_set),
                                  endDateTime=end_time,
                                  durationStr=duration,
                                  barSizeSetting=candle_size,
                                  whatToShow='TRADES',
                                  useRTH=0,
                                  formatDate=1,
                                  keepUpToDate=0,
                                  chartOptions=[])
            app.hist_end_event.wait()
            data[f"{ticker}{leg}"] = pd.DataFrame(app.histdf)
            data[f"{ticker}{leg}"].set_index("Date",inplace=True)
            app.histdf = None
    return data

def getRollsDue(app, tickers, utc_date_str):
    # check if rollover date == date_str, if True: return previous active and carry contract
    df = pd.read_csv(configs.roll_schedule_path())
    df['StartDate'] = pd.to_datetime(df['StartDate'], format="%Y%m%d")
        
    utc_dt = dt.datetime.strptime(utc_date_str, "%Y%m%d %H:%M:%S") 
    roll_today = {}
    for ticker in tickers:
        # get time zone 
        tz_offset = getTickerTimeZoneOffset(app, ticker)
        date = utc_dt + dt.timedelta(hours = tz_offset)
        
        # check if today is roll day (in contract tz)
        sortby_ticker = df.loc[df['Symbol']==ticker]
        contract_activated = [x for x in sortby_ticker['StartDate'] if date >= x] 
        most_recent_activation = contract_activated[-1]
        if date.date() == most_recent_activation.date():
            print(f"{ticker} Contract roll scheduled {date.date()}")
            old_contract = sortby_ticker.loc[sortby_ticker['StartDate']==contract_activated[-2]]
            old_active_month = old_contract['ActiveMonth'].iloc[0]
            old_carry_month = old_contract['CarryMonth'].iloc[0]
            roll_today[ticker] = (old_active_month, old_carry_month)             
    return roll_today

def rollContracts(app, tickers, contract_set):
    for ticker in tickers:
        if ticker in contract_set.keys():
            app.reqIds(-1)
            pos = management.getSpreadPosition(app, ticker, contract_set)
            if pos > 0:
                management.sendSpreadOrder(app, ticker, contract_set, "SELL", pos)
            elif pos < 0:
                management.sendSpreadOrder(app, ticker, contract_set, "BUY", abs(pos))
    # reset exec_df, we don't want this in getSlippage() calcs
    app.execution_df = pd.DataFrame(columns=['LocalSymbol', 'SecType', 'Time', 
                                              'Side', 'Shares', 'Price'])    

# trading hours
def getTradingHours(app, ticker):
    app.reqIds(-1)
    app.req_contract_event.clear()
    app.reqContractDetails(app.nextValidOrderId, management.createCONTFUT(ticker))
    app.req_contract_event.wait()
    contract_hours = app.contract_hours
    return contract_hours

def utcOffset(tz, utc_dt):
    offset = utc_dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(tz)).utcoffset().total_seconds() / 60 / 60
    return -1 * offset

def parseTradingHours(contract_hours):
    hours = contract_hours[0]    
    tz = contract_hours[1]
    utc_offset = utcOffset(tz, dt.datetime.utcnow())    
    # function must be invoked live, may not work on DST day --> TOFIX 
    
    utc_open_hours = []
    hours_list = [hour for hour in hours.split(";") if hour]
    
    for day in hours_list:
        if "CLOSED" in day:
            continue

        start, end = day.split("-")
        utc_start_dt = dt.datetime.strptime(start, "%Y%m%d:%H%M") + dt.timedelta(hours = utc_offset)
        utc_end_dt = dt.datetime.strptime(end, "%Y%m%d:%H%M") + dt.timedelta(hours = utc_offset)
        utc_open_hours.append((utc_start_dt, utc_end_dt))
    return utc_open_hours

def isMarketOpen(app, ticker):
    contract_hours = getTradingHours(app, ticker)
    utc_open_hours = parseTradingHours(contract_hours)

    now = dt.datetime.utcnow()    
    for day in utc_open_hours:
        if day[0] < now < day[1]:
            return True
    return False

def removeClosedTickers(app, tickers):
    open_tickers = []
    for ticker in tickers:
        if isMarketOpen(app, ticker) == True:
            open_tickers.append(ticker)
        else:
            logger.info(f"{ticker} market closed, pausing actions")
    return open_tickers

def getTickerTimeZoneOffset(app, ticker):
    contract_hours = getTradingHours(app, ticker)
    tz = contract_hours[1]
    utc_offset = utcOffset(tz, dt.datetime.utcnow())    
    return utc_offset

# getting session active dates
def getSessionStarts(utc_open_hours):
    # input = output of parseTradingHours()
    flattened_start_hours = [session[0] for session in utc_open_hours]
    
    session_starts = []
    for date, group in itertools.groupby(flattened_start_hours, key=lambda x: x.date()):
        group = list(group)
        session_starts.append(group[0])
    return session_starts

def parseSessionsList(sessions_list):
    # returns list of tuples [(cron_fmt, tickers, date_string), (),]
    parsed_sessions = []
    for next_open, tickers in itertools.groupby(sessions_list, key=lambda x: x[1]):
        cron_fmt = configs.datetime_to_cron(next_open)
        date_str = next_open.strftime("%Y%m%d %H:%M:00")

        list_of_tuples = list(tickers)
        tickers = [tup[0] for tup in list_of_tuples]        
        tickers_str = " ".join(tickers)
        
        parsed_sessions.append((cron_fmt, tickers_str, date_str))
    return parsed_sessions

def getNextSessionOpen(app, tickers, tm):
    # get each ticker next session open
    tm = dt.datetime.strptime(tm,"%Y%m%d %H:%M:%S")
    sessions_list = []

    for ticker in tickers:
        contract_hours = getTradingHours(app, ticker)
        utc_open_hours = parseTradingHours(contract_hours)
        session_starts = getSessionStarts(utc_open_hours)
                
        next_open = next((time for time in session_starts if tm < time), None)
        if next_open:
            logger.info(f"getSessionCSV(): {ticker} next open {next_open}")
        else:
            logger.critical(f"getSessionCSV(): {ticker} next open returns None")
                        
        sessions_list.append((ticker, next_open))
        
    next_session_opens = parseSessionsList(sessions_list)
        
    return next_session_opens

# get account details
def getAccountDetails(app, tag):
    # tags: NetLiquidation, TotalCashValue, InitMarginReq, MaintMarginReq, ExcessLiquidity,
    app.reqIds(-1)
    app.account_summary_event.clear()
    app.reqAccountSummary(app.nextValidOrderId, "All", tag)
    app.account_summary_event.wait()
    return app.account_summary

def getPNL(app):
    app.reqIds(-1)
    app.daily_pnl_event.clear()
    app.reqPnL(app.nextValidOrderId, "DU2408613", "")
    app.daily_pnl_event.wait()
    return app.daily_pnl

def lastClose(app, tickers, date_str, contract_set):
    timestamp = dt.datetime.strptime(date_str, "%Y%m%d %H:%M:%S")
    last_close_dict = {}
    for ticker in tickers:
        c1_local_symbol = contract_set[ticker][0]
        c2_local_symbol = contract_set[ticker][1]
        for local_symbol, leg in [(c1_local_symbol, 'c1'), (c2_local_symbol,'c2')]:
            data = pd.read_csv(configs.datafeed_path(ticker, leg))
            data['Datetime'] = pd.to_datetime(data['Datetime'])
            data = data.set_index("Datetime", drop=True)
        
            close_ser = data['Close']
            last_close = close_ser[(close_ser.index < timestamp)].iloc[-1]        
            last_close_dict[local_symbol]=last_close
    
    return last_close_dict

def getSlippage(app, tickers, date_str, contract_set):
    last_closes = lastClose(app, tickers, date_str, contract_set)
    exec_df = app.execution_df
    
    slippage_list = []
    for local_symbol, prev_close in last_closes.items():
        if not local_symbol in exec_df["LocalSymbol"].values:
            continue
        
        time_of_trade = exec_df.loc[exec_df["LocalSymbol"] == local_symbol, "Time"].item()
        exec_px = exec_df.loc[exec_df["LocalSymbol"] == local_symbol, "Price"].item()
        exec_side = exec_df.loc[exec_df["LocalSymbol"] == local_symbol, "Side"].item()
        
        if exec_side == "BOT":
            slippage = exec_px - prev_close 
        elif exec_side == "SLD":
            slippage = prev_close - exec_px 
        
        slippage_list.append((local_symbol, time_of_trade, slippage))
        logger.info(f"{local_symbol} at {time_of_trade} slippage: {slippage}")

    return slippage_list
    
    
    
    
    



