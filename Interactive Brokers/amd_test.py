from ib_insync import *

# ib.disconnect()
# import asyncio

# try:
#     # Get the currently running event loop
#     loop = asyncio.get_running_loop()
#     print("A background event loop is running. Stopping it...")

#     # Stop the loop
#     loop.stop()
#     print("Event loop stopped.")
# except RuntimeError:
#     print("No event loop is currently running.")
    
# Initialize the IB connection
# util.startLoop()
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=33)

# Define the contract for EUR/USD Forex pair
contract = Stock('AMD', 'SMART', 'USD')

bars = ib.reqHistoricalData(contract, endDateTime='',
                            durationStr='30 D',
                            barSizeSetting='1 hour',
                            whatToShow='MIDPOINT', useRTH=True)

# convert to df
df = util.df(bars)
print(df)
ib.disconnect()