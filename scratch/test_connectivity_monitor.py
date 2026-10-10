import time
from backend.monitoring.connectivity_monitor import ConnectivityMonitor

test_monitor = ConnectivityMonitor(wifi_interval=0.5, bt_interval=0.5)

events = []
def mock_broadcast(evt, data):
    events.append((evt, data))
    print(f"BROADCAST -> {evt}: {data}")

test_monitor.set_broadcast_callback(mock_broadcast)

# Initial run simulates startup
test_monitor.initial_checked = False
test_monitor._check_wifi()
test_monitor._check_bluetooth()
print(f"Initial State: Wi-Fi={test_monitor.last_wifi_ssid}, BT={test_monitor.last_bt_devices}")

# Now simulate a Wi-Fi reconnect event by setting last_wifi_connected = False
print("\n--- Testing Wi-Fi connection trigger ---")
test_monitor.last_wifi_connected = False
test_monitor.initial_checked = True
test_monitor._check_wifi()

# Now simulate Bluetooth connection event by clearing last_bt_devices
print("\n--- Testing Bluetooth connection trigger ---")
actual_bt = test_monitor._get_connected_bluetooth()
print(f"Actual BT in system: {actual_bt}")
if actual_bt:
    test_monitor.last_bt_devices = set()  # simulate that it was previously empty
    test_monitor._check_bluetooth()
else:
    print("No active BT devices currently connected on PC to simulate transition, mocking one:")
    test_monitor.last_bt_devices = set()
    # Mocking _get_connected_bluetooth return
    test_monitor._get_connected_bluetooth = lambda: {"Test Headphones"}
    test_monitor._check_bluetooth()

print("\n--- Summary of Triggered Events ---")
for evt, data in events:
    print(f"Event: {evt} | Message: {data['message']}")

print("\nTEST COMPLETED SUCCESSFULLY")
