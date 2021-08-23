import os 
import argparse
import datetime as dt
import helpers.boot as boot
import helpers.utils as utils
import helpers.configs as configs
logger = configs.logger()

def main(tickers, tm):
    configs.writePID(os.getpid())
    configs.writeCMD(os.getpid())
    
    app = boot.IBAPI(clientId=1000, port=7497)
    
    next_session_open = utils.getNextSessionOpen(app, tickers, tm)
    configs.cron_update(next_session_open)
    logger.info("Updated cron-rotating")
    
    app.disconnect()

if __name__ == '__main__':    
    tickers = configs.full_asset_list()
    tm = (dt.datetime.utcnow()).strftime("%Y%m%d %H:%M:%S")
    main(tickers, tm)
