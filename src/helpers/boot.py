import threading
from . import configs
logger = configs.logger()
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
import pandas as pd

class IBAPI(EWrapper, EClient):
    def __init__(self, clientId, port=4002):
        EClient.__init__(self, self)
        self.connection_event = threading.Event()
        self.connect("127.0.0.1", port, clientId)
        connection_thread = threading.Thread(target=lambda:self.run(), daemon=True)
        connection_thread.start() 
        self.connection_event.wait()
        logger.info("Websocket connection successful")
        
        self.order_df = pd.DataFrame(columns=['PermId', 'ClientId', 'OrderId',
                                              'Account', 'Symbol', 'SecType',
                                              'Exchange', 'Action', 'OrderType',
                                              'TotalQty', 'CashQty', 'LmtPrice',
                                              'AuxPrice', 'Status'])
        self.execution_df = pd.DataFrame(columns=['LocalSymbol', 'SecType', 'Time', 
                                                  'Side', 'Shares', 'Price'])
        self.pos_df = pd.DataFrame(columns=['Account', 'Symbol', 
                                            'LocalSymbol', 'SecType',
                                            'Currency', 'Position', 'Avg cost'])
        self.histdf = None
        self.account_summary = None
        self.daily_pnl = None
        
        self.hist_end_event = threading.Event() 
        self.req_contract_event = threading.Event()
        self.req_pos_event = threading.Event()
        self.req_open_order = threading.Event()
        self.acc_sum_event = threading.Event()
        self.combo_order_executed_event = threading.Event()
        self.simple_order_executed_event = threading.Event()
        self.account_summary_event = threading.Event()
        self.daily_pnl_event = threading.Event()
    
    def connectionClosed(self):
        logger.info("Connection closed")
        
    def accountSummary(self, reqId, account, tag, value, currency):
        self.account_summary = value
        
    def accountSummaryEnd(self, reqId):
        self.cancelAccountSummary(self.nextValidOrderId)
        self.account_summary_event.set()
    
    def pnl(self, reqId, dailyPnL, unrealizedPnL, realizedPnL):
        self.daily_pnl = dailyPnL
        self.cancelPnL(self.nextValidOrderId)
        self.daily_pnl_event.set()
        
    def contractDetails(self, reqId, contractDetails):
        self.contract_dets = str(contractDetails.contract)
        self.contract_hours = (contractDetails.tradingHours, contractDetails.timeZoneId)

    def contractDetailsEnd(self, reqId):
         self.req_contract_event.set()

    def nextValidId(self, orderId): #will be called on self.connect()
        self.connection_event.set()
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        print("NextValidId:", orderId) 
    
    def historicalData(self, reqId, bar):
        if not self.histdf:
            self.histdf = [{"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume}]
        else:
            self.histdf.append({"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume})
    
    def historicalDataEnd(self, reqId, start, end):
        super().historicalDataEnd(reqId, start, end)
        print("HistoricalDataEnd. ReqId:", reqId, "from", start, "to", end)
        self.hist_end_event.set()
        
    def openOrder(self, orderId, contract, order, orderState):
        dictionary = {"PermId":order.permId, "ClientId": order.clientId, "OrderId": orderId, 
                      "Account": order.account, "Symbol": contract.symbol, "SecType": contract.secType,
                      "Exchange": contract.exchange, "Action": order.action, "OrderType": order.orderType,
                      "TotalQty": order.totalQuantity, "CashQty": order.cashQty, 
                      "LmtPrice": order.lmtPrice, "AuxPrice": order.auxPrice, "Status": orderState.status}
        self.order_df = self.order_df.append(dictionary, ignore_index=True)

    def openOrderEnd(self):
        self.req_open_order.set()
    
    def execDetails(self, reqId, contract, execution): 
        dictionary = {"LocalSymbol":contract.localSymbol,"SecType":contract.secType,
                      "Time":execution.time,
                      "Side":execution.side, "Shares":execution.shares, "Price":execution.price,
                      }
        self.execution_df = self.execution_df.append(dictionary, ignore_index=True)    
        self.execution_df.drop_duplicates(subset=["LocalSymbol","Time","Shares","Price"], inplace=True)

        self.simple_order_executed_event.set()
        if execution.execId.endswith("03.01"): # combolegs order returns 3 execIds, ending [01.01, 02.01, 03.01]
            self.combo_order_executed_event.set()
        
    def execDetailsEnd(self, reqId):
        pass
    
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, 
                    parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        pass
    
    def position(self, account, contract, position, avgCost):
        dictionary = {"Account":account, "Symbol": contract.symbol, 
                      "LocalSymbol": contract.localSymbol, "SecType": contract.secType,
                      "Currency": contract.currency, "Position": position, "Avg cost": avgCost}        

        self.pos_df = self.pos_df.append(dictionary, ignore_index=True)    
        self.pos_df.drop_duplicates(subset=["Symbol","LocalSymbol"], inplace=True)
        
    def positionEnd(self):
        self.cancelPositions()
        self.req_pos_event.set()