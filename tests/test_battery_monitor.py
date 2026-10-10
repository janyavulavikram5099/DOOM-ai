import unittest
from unittest.mock import MagicMock, patch
import collections

from backend.monitoring.battery_monitor import BatteryMonitor

# Named tuple matching psutil.sensors_battery result
BatteryInfo = collections.namedtuple("BatteryInfo", ["percent", "secsleft", "power_plugged"])


class TestBatteryMonitor(unittest.TestCase):
    @patch("backend.monitoring.battery_monitor.tts")
    @patch("backend.monitoring.battery_monitor.psutil.sensors_battery")
    def test_full_charge_repeats_until_disconnect(self, mock_battery, mock_tts):
        mock_tts.is_speaking = False
        monitor = BatteryMonitor(check_interval=0.1, full_alert_repeat_interval=0.2)

        # 1. Start at 99% plugged in
        mock_battery.return_value = BatteryInfo(percent=99, secsleft=-1, power_plugged=True)
        monitor._check_battery()  # Initial check
        self.assertTrue(monitor.initial_checked)

        # 2. Battery reaches 100% while plugged in
        mock_battery.return_value = BatteryInfo(percent=100, secsleft=-1, power_plugged=True)
        monitor._check_battery()
        mock_tts.speak.assert_called_with("100% completed remove pin")

        # 3. Repeat alert when time elapses and still plugged in
        mock_tts.speak.reset_mock()
        monitor.last_full_alert_time -= 1.0  # Simulate 1 second elapsed (greater than 0.2s interval)
        monitor._check_battery()
        mock_tts.speak.assert_called_with("100% completed remove pin")

        # 4. Charger disconnected (pin removed)
        mock_tts.speak.reset_mock()
        mock_battery.return_value = BatteryInfo(percent=100, secsleft=-1, power_plugged=False)
        monitor._check_battery()
        mock_tts.speak.assert_called_with("charging stopped")
        self.assertEqual(monitor.last_full_alert_time, 0.0)

        # 5. Subsequent check while unplugged must NOT repeat alert
        mock_tts.speak.reset_mock()
        monitor._check_battery()
        mock_tts.speak.assert_not_called()


if __name__ == "__main__":
    unittest.main()
