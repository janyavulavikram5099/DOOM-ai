"""
Test script to verify battery_monitor logic and state transitions.
"""

from unittest.mock import MagicMock, patch
from backend.monitoring.battery_monitor import BatteryMonitor

events = []
spoken = []

monitor = BatteryMonitor(check_interval=0.1)
monitor.set_broadcast_callback(lambda evt, data: events.append((evt, data)))

# Mock TTS
with patch("backend.monitoring.battery_monitor.tts.speak", side_effect=lambda text: spoken.append(text)):
    # 1. First run on battery (initialization: should not announce)
    mock_bat_unplugged = MagicMock(percent=50, power_plugged=False)
    with patch("backend.monitoring.battery_monitor.psutil.sensors_battery", return_value=mock_bat_unplugged):
        monitor._check_battery()
    assert len(spoken) == 0, f"Expected no speech on init, got {spoken}"

    # 2. Plug in charger: should announce "laptop is charging now"
    mock_bat_charging = MagicMock(percent=50, power_plugged=True)
    with patch("backend.monitoring.battery_monitor.psutil.sensors_battery", return_value=mock_bat_charging):
        monitor._check_battery()
    assert "laptop is charging now" in spoken, f"Expected 'laptop is charging now', got {spoken}"
    assert events[-1][1]["message"] == "laptop is charging now"

    # 3. Same charging state: should NOT announce again
    with patch("backend.monitoring.battery_monitor.psutil.sensors_battery", return_value=mock_bat_charging):
        monitor._check_battery()
    assert spoken.count("laptop is charging now") == 1

    # 4. Battery reaches 100% full: should announce "laptop charge full"
    mock_bat_full = MagicMock(percent=100, power_plugged=True)
    with patch("backend.monitoring.battery_monitor.psutil.sensors_battery", return_value=mock_bat_full):
        monitor._check_battery()
    assert "laptop charge full" in spoken, f"Expected 'laptop charge full', got {spoken}"
    assert events[-1][1]["message"] == "laptop charge full"

    # 5. Still at 100%: should NOT announce full repeatedly
    with patch("backend.monitoring.battery_monitor.psutil.sensors_battery", return_value=mock_bat_full):
        monitor._check_battery()
    assert spoken.count("laptop charge full") == 1

    # 6. Unplug charger: should announce "charging stopped"
    mock_bat_unplugged_full = MagicMock(percent=100, power_plugged=False)
    with patch("backend.monitoring.battery_monitor.psutil.sensors_battery", return_value=mock_bat_unplugged_full):
        monitor._check_battery()
    assert "charging stopped" in spoken, f"Expected 'charging stopped', got {spoken}"
    assert events[-1][1]["message"] == "charging stopped"

print("ALL BATTERY MONITOR TESTS PASSED SUCCESSFULLY!")
print("Spoken sequence:", spoken)
print("Events:", [e[1]["event"] for e in events])
