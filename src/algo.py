import argparse
import datetime as dt
import helpers.boot as boot
import helpers.management as management
import helpers.utils as utils
import helpers.strategy as strategy
import helpers.configs as configs
logger = configs.logger()

def main(tickers, tm):
    app = boot.IBAPI(clientId=1, port=7497)    

    logger.info("Running Algo()...")
    management.clearOpenOrders(app)

    expired_contracts = utils.getRollsDue(app, tickers, tm)    
    live_contracts = utils.getActiveCarryContracts(tickers,tm)
    
    open_tickers = utils.removeClosedTickers(app, tickers)
    forecast_dict = strategy.calcForecast(open_tickers, 
                                          [strategy.strategy1,
                                           strategy.strategy2,
                                           strategy.strategy3,]
                                          )
    utils.rollContracts(app, open_tickers, expired_contracts)
    strategy.executeBinarySystem(app, open_tickers, live_contracts, forecast_dict, entry_threshold=1, exit_threshold=0)
    utils.getSlippage(app, open_tickers, tm, live_contracts)
    
    app.disconnect()

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reads historical database, generates forecasts and executes orders.")
    parser.add_argument("--tickers", type=str, nargs="+", help="Ticker symbol(s), separated by 1 space | Ex: NG HG ")
    parser.add_argument("--date", type=str, nargs="+", help="Datetime in format 'YYYYMMDD HH:MM:SS'")
    args = parser.parse_args()
    
    tm = " ".join(args.date)        
    tickers = args.tickers

    main(tickers, tm)
    
    

    
    
    
    
    
    
    















































    
