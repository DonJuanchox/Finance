import asyncio

try:
    # Get the currently running event loop
    loop = asyncio.get_running_loop()
    print("A background event loop is running. Stopping it...")

    # Stop the loop
    loop.stop()
    print("Event loop stopped.")
except RuntimeError:
    print("No event loop is currently running.")
