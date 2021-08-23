import os 
import argparse
import helpers.boot as boot
import helpers.utils as utils
import helpers.management as management
import helpers.configs as configs
logger = configs.logger()

def main(args.command):
    configs.writePID(os.getpid())
    configs.writeCMD(os.getpid())
    
    app = boot.IBAPI(clientId=0, port=7497)

    command_dict = {"orders":management.getOrders(app),
                    "positions":management.getPositions(app),
                    "value":utils.getAccountDetails(app, "TotalCashValue"),
                    "margin":utils.getAccountDetails(app, "InitMarginReq"),
                    "dailypnl":utils.getPNL(app),
                    }
    if args.message:
         utils.send_message("update", f"{args.command} : {command_dict[args.command]}", code_block_fmt=True)

    app.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse commands into script for debugging through CLI")
    parser.add_argument("--command", type=str, help="Commands: orders, positions, value, margin, dailypnl, logs")
    parser.add_argument("--message", type=str, help="Set True to send alert message")
    args = parser.parse_args()
    
    main()
   
    
    
