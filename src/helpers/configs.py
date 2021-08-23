import pandas as pd
import psutil
import logging
import logging.handlers
import time

# code redacted

def writePID(pid):
    path = "~/live-system/bin/watchdog/pid"
    
    with open(path, "w") as file:
        file.write(str(pid))

def writeCMD(pid):   
    path = "~/live-system/bin/watchdog/cmd"
    process = psutil.Process(pid)
    command_str = " ".join(process.cmdline())
    
    with open(path, "w") as file:
        file.write(command_str)

def logger():
    path = r"~/live-system/logs/log"
    logger = logging.getLogger(__name__)  
    if not len(logger.handlers):
        logger.setLevel(logging.DEBUG)
        # handler
        fh = logging.handlers.TimedRotatingFileHandler(path, when="midnight", interval=1, backupCount=10)
        fh.suffix = "%Y%m%d"
        fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)
        # formatter
        formatter = logging.Formatter("%(asctime)s:%(levelname)s - %(message)s")
        logging.Formatter.converter = time.gmtime # standardise UTC 
        fh.setFormatter(formatter)
    return logger

def datetime_to_cron(dt):
    # convert datetime to crontab
    return f"{dt.minute} {dt.hour} {dt.day} {dt.month} *"
    
def cron_update(next_session_open):
    # formats list of tuples next_session_open into .cron file 
    cron_path = "~/live-system/bin/crons/cron-rotating"
    #cron_comd = "{cron} python3 ./src/hist_update.py --tickers {tickers} && python ./src/algo.py --tickers {tickers}"
    cron_comd = "{cron} python3 ~/live-system/src/main.py --tickers {tickers} --date {date}"
    
    full_cron = ""
    for cron, tickers, date in next_session_open: 
        cmd = cron_comd.format(cron=cron, tickers=tickers, date=date)
        full_cron += (cmd+"\n")
    
    with open(cron_path, "w") as file:
        file.write(full_cron)

def roll_schedule_path():
    path = r"~/live-system/database/active-contracts.txt"
    return path
    
def datafeed_path(ticker, leg):
    path = rf"~/live-system/database/c1c2/{ticker}{leg}.csv"
    return path

def contfut_datafeed_path(ticker):
    path = "$PATH_TO_CONTFUT"
    return path

def full_asset_list():
    assets = ['VIX','HG','SI','GC','PA','NG','CL','ZW','ZC','ZS']
    return assets

def getExchange(ticker):
    exchanges = (("GLOBEX", ['GE','ES','MES','NQ','MNQ','EUR','CAD','AUD']),
                  ("ECBOT", ['ZC','ZW','ZS','ZN']),
                  ("NYMEX", ['GC','MGC','SI','CL','NG','PA','HG']),
                  ("CFE", ['VIX'])
                  )
    exchange = next((x[0] for x in exchanges if ticker in x[1]), None)
    return exchange

def auth_alert(where):
    tokens = {"watchdog":'{$TOKEN}',
              "update":'{$TOKEN}'}
    token = tokens[where]
    chat_id = "{$CHAT_ID}"
    func = '{$FUNC}'
    return token, chat_id, func

          
