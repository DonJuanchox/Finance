from ib_insync import IB

# List of all IB clients
clients = []

# Create multiple clients
for clientId in range(1, 5):  # Example with 3 clients
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=clientId)
    clients.append(ib)

print(f"Connected {len(clients)} clients.")

# Disconnect all clients
for ib in clients:
    ib.disconnect()

print("All clients disconnected.")
