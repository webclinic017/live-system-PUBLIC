from ibapi.contract import Contract
from ibapi.contract import ComboLeg
from ibapi.order import Order
import pandas as pd
from . import configs
logger = configs.logger()

# contracts
def createContract(symbol, leg, contract_set):
    exchange = configs.getExchange(symbol)     

    if leg == "c1":
        local_symbol = contract_set[symbol][0]
    elif leg == "c2":
        local_symbol = contract_set[symbol][1]
    
    contract = Contract()
    contract.localSymbol = local_symbol
    contract.secType = 'FUT'
    contract.currency = 'USD'
    contract.exchange = exchange     
    return contract

def createCONTFUT(symbol):
    exchange = configs.getExchange(symbol)
    
    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'CONTFUT'
    contract.currency = 'USD'
    contract.exchange = exchange     
    return contract

def getconId(app, symbol, leg, contract_set):
    app.req_contract_event.clear()
    app.reqContractDetails(app.nextValidOrderId, createContract(symbol, leg, contract_set))
    app.req_contract_event.wait()
    conid = app.contract_dets.split(",")[0]
    return conid

def comboSpread(app, symbol, contract_set):
    exchange = configs.getExchange(symbol)     

    contract = Contract()
    contract.symbol = symbol
    contract.secType = "BAG"
    contract.currency = "USD"
    contract.exchange = exchange
    
    active_conId = getconId(app, symbol, "c1", contract_set)
    carry_conId = getconId(app, symbol, "c2", contract_set)
        
    # Spread = leg1 - leg2 | Long spread = Long (buy leg1, short leg2), Short spread = Short (buy leg1, short leg 2) 
    leg1 = ComboLeg()
    leg1.conId = active_conId
    leg1.ratio = 1
    leg1.action = "BUY" 
    leg1.exchange = exchange
    
    leg2 = ComboLeg()
    leg2.conId = carry_conId
    leg2.ratio = 1
    leg2.action = "SELL"
    leg2.exchange = exchange
    
    contract.comboLegs = []
    contract.comboLegs.append(leg1)
    contract.comboLegs.append(leg2)
    
    return contract

# Orders
def marketOrder(direction,quantity):
    order = Order()
    order.action = direction
    order.orderType = "MKT"
    order.totalQuantity = quantity
    return order

def mooOrder(direction, quantity):
    order = Order()
    order.action = direction
    order.orderType = "MKT"
    order.totalQuantity = quantity
    order.tif = "OPG"

def sendSpreadOrder(app, ticker, contract_set, direction, quantity):
    app.combo_order_executed_event.clear()
    app.placeOrder(app.nextValidOrderId, 
                   comboSpread(app, ticker, contract_set), 
                   marketOrder(direction, quantity),
                   )
    logger.info(f"SpreadOrder sent: {direction} {quantity} {ticker}")
    app.combo_order_executed_event.wait()

def clearOpenOrders(app):
    app.reqGlobalCancel()
    
# update/get positions/orders
def getPositions(app):
    app.pos_df = pd.DataFrame(columns=['Account', 'Symbol', 
                                    'LocalSymbol', 'SecType',
                                    'Currency', 'Position', 'Avg cost'])
    app.req_pos_event.clear()
    app.reqPositions()
    app.req_pos_event.wait()
    
    return app.pos_df

def getSpreadPosition(app, ticker, contract_set):
    c1_local_symbol = contract_set[ticker][0]
    c2_local_symbol = contract_set[ticker][1]
    
    c1_pos = getLocalSymbolPosition(app, c1_local_symbol)
    c2_pos = getLocalSymbolPosition(app, c2_local_symbol)
    
    if c1_pos > 0 and c2_pos < 0:
        # LONG spread
        # return c2 position: We may have c1 contracts not part of the calendar spread, c2 pos = calendar spread position
        return abs(c2_pos)
    elif c1_pos < 0 and c2_pos > 0:
        # SHORT spread
        return -(c2_pos)
    else:
        return 0
    
def getLocalSymbolPosition(app, local_symbol):
    getPositions(app)
    local_symbol_ser = app.pos_df.loc[app.pos_df['LocalSymbol'] == local_symbol, "Position"]

    if local_symbol_ser.empty:
        return 0
    else:
        return local_symbol_ser.values.item()

def getOrders(app):
    app.order_df = pd.DataFrame(columns=['PermId', 'ClientId', 'OrderId',
                                         'Account', 'Symbol', 'SecType',
                                         'Exchange', 'Action', 'OrderType',
                                         'TotalQty', 'CashQty', 'LmtPrice',
                                         'AuxPrice', 'Status'])
    app.req_open_order.clear()
    app.reqAllOpenOrders()
    app.req_open_order.wait()   
    return app.order_df

