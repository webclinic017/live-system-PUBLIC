import os
import psutil
import argparse
import hist_update
import algo
import helpers.configs as configs

def main(tickers, tm):    
    configs.writePID(os.getpid())
    configs.writeCMD(os.getpid())
        
    hist_update.main(tickers, tm)
    algo.main(tickers, tm)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="$ python3 hist_update.py && python3 algo.py")
    parser.add_argument("--tickers", type=str, nargs="+", help="Ticker symbol(s), separated by 1 space | Ex: NG HG ")
    parser.add_argument("--date", type=str, nargs="+", help="Datetime in format 'YYYYMMDD HH:MM:SS'")
    args = parser.parse_args()
    
    tm = " ".join(args.date)
    main(args.tickers, tm)
    
