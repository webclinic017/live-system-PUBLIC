# live-system
This repository contains my live trading system hosted on a Debian 10 server. Some code has been excluded for obvious reasons. 
### Architecture
- Debian 10 (buster)
- IBGateway 987
- pandas>=1.2.0
- numpy>=1.16.6
- ibapi >=9.81.1.post1
- requests>=2.26.0
- psutil>=5.8.0
- pytz==2021.1

### Basic System Architecture
1. Establish websocket connection with IBGateway
2. update_cron.py calls at EOD and parses contractDetails() from IBAPI to obtain the next day's open time
	- This is converted to UTC, taking into account DST/holidays/events.
	- Next day's open time for each symbol > bin/crons/cron-rotating
	- Crontab self updates to run main() at next day's open timing 
3. main() runs hist_update.py && algo.py
	- hist_update.py obtains previous day's EOD close and appends to the database
	- algo.py checks for roll dates scheduled via active-contracts.txt and rolls accordingly
	- algo.py reads database and generates forecast for each traded symbol
		- Forecasts are translated into a portfolio allocation; orders are sent to achieve target positions
4. bin/watchdog contains the reset mechanism for websocket connection loss/other outages.
