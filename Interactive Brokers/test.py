import asyncio
from ib_insync import IB

ib = IB()

loop = asyncio.get_event_loop()

# Connect to IB
def connect():
    ib.connect('127.0.0.1', 7497, clientId=1)
    print("Connected to Interactive Brokers!")

# Stop the loop after some delay
async def stop_loop():
    await asyncio.sleep(5)  # Stop after 5 seconds
    ib.disconnect()
    print("Disconnected from Interactive Brokers!")
    loop.stop()

# Schedule the tasks
loop.create_task(stop_loop())
loop.run_forever()
