from ib_insync import *


# Initialize the IB connection
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# Define the contract for EUR/USD Forex pair
contract = Forex('EURUSD')

# Request market data
ticker = ib.reqMktData(contract)

# Wait for the data to be populated
ib.sleep(2)

# Print the current market price
if ticker.last:
    print(f"EUR/USD current price: {ticker.marketPrice()} USD")
else:
    print("No market data available. Please check subscriptions.")

# Disconnect from IB
ib.disconnect()
