import argparse
import datetime as dt
import pandas as pd
import helpers.boot as boot
import helpers.utils as utils
import helpers.configs as configs
logger = configs.logger()

def updateDatasets(tickers, data, live_contracts):
    # new df with close prices of each ticker/leg as columns:
    df = pd.DataFrame()
    for k,v in data.items():
        df[k] = v['Close']       
        
    # calc annualised spread by dividing by time in years:
    for ticker in tickers: 
        df[f"{ticker}Spread"] = (df[f"{ticker}c1"] - df[f"{ticker}c2"]) / live_contracts[ticker][2]
    
    # export/appending data
    df['Datetime'] = pd.to_datetime(df.index)
    df.set_index('Datetime',inplace=True)
    for ticker in tickers:
        for leg in ['c1','c2']:
            contract = df[[f"{ticker}{leg}", f"{ticker}Spread"]]
            contract.columns = ['Close','Spread']
            
            original_data = pd.read_csv(configs.datafeed_path(ticker, leg))
            original_data['Datetime'] = pd.to_datetime(original_data["Datetime"])
            original_data.set_index("Datetime", inplace=True)
            original_data = original_data.dropna()
                        
            last_timestamp = original_data.index[-1]
            append_new_data = contract[(contract.index > last_timestamp)]
            append_new_data = append_new_data.dropna()
            
            updated_dataset = pd.concat([original_data, append_new_data])
            updated_dataset.to_csv(configs.datafeed_path(ticker, leg))
            print(f"Append {len(append_new_data)} lines to {ticker}{leg} data")
            logger.info(f"Append {len(append_new_data)} line(s) to {ticker}{leg} data")

def main(tickers, tm):
    app = boot.IBAPI(clientId=999, port=7497)
    live_contracts = utils.getActiveCarryContracts(tickers,tm)
    c1c2_hist_data = utils.getHistData(app, 
                                       tickers, 
                                       contract_set = live_contracts,
                                       end_time=tm, 
                                       duration="3 D", 
                                       candle_size="1 day")
    updateDatasets(tickers, c1c2_hist_data, live_contracts)
    app.disconnect()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Update historical database with updated EOD data")
    parser.add_argument("--tickers", type=str, nargs="+", help="Ticker symbol(s), separated by 1 space | Ex: NG HG ")
    parser.add_argument("--date", type=str, nargs="+", help="Datetime in format 'YYYYMMDD HH:MM:SS'")
    args = parser.parse_args()
        
    tickers = args.tickers
    tm = " ".join(args.date)
    
    main(tickers, tm)

    
    
    
    
    
    
    
    
    
    
    
    
