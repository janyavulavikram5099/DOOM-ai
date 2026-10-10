"""
VIKRAM AI - Real-Time Battery & Power State Monitor
Continuously tracks AC power connection, disconnection, and full charge state.
Triggers immediate audible voice alerts:
  - Plugged in: "laptop is charging now"
  - Full charge: "laptop charge full"
  - Disconnected: "charging stopped"
"""

import logging
import threading
import time
from collections.abc import Callable
from typing import Any

import psutil

from ..assistant.text_to_speech import tts

logger = logging.getLogger("vikram.monitoring.battery")


class BatteryMonitor:
    def __init__(self, check_interval: float = 1.5, full_alert_repeat_interval: float = 10.0):
        self.check_interval = check_interval
        self.full_alert_repeat_interval = full_alert_repeat_interval
        self._thread: threading.Thread | None = None
        self._running: bool = False
        self.broadcast_callback: Callable[[str, Any], None] | None = None

        # State tracking
        self.last_plugged: bool | None = None
        self.last_full_alert_time: float = 0.0
        self.initial_checked: bool = False

    def set_broadcast_callback(self, callback: Callable[[str, Any], None]):
        self.broadcast_callback = callback

    def _broadcast(self, event_type: str, data: Any):
        if self.broadcast_callback:
            try:
                self.broadcast_callback(event_type, data)
            except Exception as e:
                logger.debug(f"Battery broadcast notice: {e}")

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="VikramBatteryMonitor"
        )
        self._thread.start()
        logger.info("DOOM AI Battery Monitor started.")

    def stop(self):
        self._running = False
        logger.info("DOOM AI Battery Monitor stopped.")

    def _monitor_loop(self):
        while self._running:
            try:
                self._check_battery()
            except Exception as e:
                logger.debug(f"Battery check exception: {e}")
            time.sleep(self.check_interval)

    def _check_battery(self):
        battery = psutil.sensors_battery()
        if not battery or battery.power_plugged is None:
            return

        is_plugged = bool(battery.power_plugged)
        percent = int(battery.percent)

        # First run: initialize state without false alert on startup
        if not self.initial_checked:
            self.last_plugged = is_plugged
            self.initial_checked = True
            # If already plugged in at 100% at startup, prepare to trigger alert
            if is_plugged and percent >= 100:
                self.last_full_alert_time = 0.0
            return

        # 1. State change: Plugged In vs Disconnected
        if is_plugged != self.last_plugged:
            if is_plugged:
                logger.info(f"Battery charging started ({percent}%).")
                msg = "laptop is charging now"
                tts.speak(msg)
                self._broadcast("battery_event", {
                    "event": "charging",
                    "message": msg,
                    "percent": percent,
                    "is_charging": True
                })
            else:
                logger.info(f"Battery charging disconnected ({percent}%).")
                msg = "charging stopped"
                tts.speak(msg)
                self._broadcast("battery_event", {
                    "event": "discharging",
                    "message": msg,
                    "percent": percent,
                    "is_charging": False
                })
                # Charger disconnected: reset full alert timer so repetition stops
                self.last_full_alert_time = 0.0

            self.last_plugged = is_plugged

        # 2. Continuous Full Charge Alert while plugged in at 100%
        # Repeats "100% completed remove pin" until the charging is disconnected
        if is_plugged and percent >= 100:
            now = time.time()
            if not tts.is_speaking and (now - self.last_full_alert_time >= self.full_alert_repeat_interval):
                logger.info("Battery at 100% and charging. Announcing: '100% completed remove pin'")
                msg = "100% completed remove pin"
                tts.speak(msg)
                self.last_full_alert_time = now
                self._broadcast("battery_event", {
                    "event": "full",
                    "message": msg,
                    "percent": percent,
                    "is_charging": True
                })
        else:
            if not is_plugged or percent < 100:
                self.last_full_alert_time = 0.0


battery_monitor = BatteryMonitor()
