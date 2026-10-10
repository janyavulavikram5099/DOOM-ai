"""
DOOM AI - Real-Time Connectivity Monitor (Wi-Fi & Bluetooth)
Continuously monitors Wi-Fi and Bluetooth connection events and announces them audibly:
  - Wi-Fi connected: 'wifi "{wifi_name}" is connected'
  - Bluetooth connected: 'bluetooth "{device_name}" is connected'
"""

import logging
import re
import subprocess
import threading
import time
import winreg
from collections.abc import Callable
from typing import Any

from ..assistant.text_to_speech import tts

logger = logging.getLogger("vikram.monitoring.connectivity")


class ConnectivityMonitor:
    def __init__(self, wifi_interval: float = 2.0, bt_interval: float = 2.5):
        self.wifi_interval = wifi_interval
        self.bt_interval = bt_interval
        self._thread: threading.Thread | None = None
        self._running: bool = False
        self.broadcast_callback: Callable[[str, Any], None] | None = None

        # State tracking
        self.last_wifi_connected: bool | None = None
        self.last_wifi_ssid: str = ""
        self.last_bt_devices: set[str] = set()
        self.initial_checked: bool = False

    def set_broadcast_callback(self, callback: Callable[[str, Any], None]):
        self.broadcast_callback = callback

    def _broadcast(self, event_type: str, data: Any):
        if self.broadcast_callback:
            try:
                self.broadcast_callback(event_type, data)
            except Exception as e:
                logger.debug(f"Connectivity broadcast notice: {e}")

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="DoomConnectivityMonitor"
        )
        self._thread.start()
        logger.info("DOOM AI Connectivity Monitor started.")

    def stop(self):
        self._running = False
        logger.info("DOOM AI Connectivity Monitor stopped.")

    def _monitor_loop(self):
        last_bt_check = 0.0
        while self._running:
            try:
                # 1. Check Wi-Fi state
                self._check_wifi()
            except Exception as e:
                logger.debug(f"Wi-Fi check exception: {e}")

            now = time.time()
            if now - last_bt_check >= self.bt_interval:
                try:
                    # 2. Check Bluetooth state
                    self._check_bluetooth()
                    last_bt_check = now
                except Exception as e:
                    logger.debug(f"Bluetooth check exception: {e}")

            if not self.initial_checked:
                self.initial_checked = True

            time.sleep(self.wifi_interval)

    def _get_current_wifi(self) -> tuple[bool, str]:
        """Queries netsh wlan show interfaces to retrieve connection status & SSID."""
        try:
            res = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True,
                text=True,
                timeout=2.0
            )
            out = res.stdout
            state_m = re.search(r"^\s*State\s*:\s*(.+)$", out, re.M)
            ssid_m = re.search(r"^\s*SSID\s*:\s*(.+)$", out, re.M)
            state = state_m.group(1).strip() if state_m else "disconnected"
            ssid = ssid_m.group(1).strip() if ssid_m else ""
            is_connected = (state.lower() == "connected") and bool(ssid)
            return is_connected, ssid
        except Exception as e:
            logger.debug(f"netsh wlan query error: {e}")
            return False, ""

    def _get_connected_bluetooth(self) -> set[str]:
        """Ultra-fast query of active Bluetooth endpoints via Windows Audio/PnP Registry."""
        connected: set[str] = set()
        for cat in ("Render", "Capture"):
            base = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\{cat}"
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base) as k:
                    num_subkeys = winreg.QueryInfoKey(k)[0]
                    for i in range(num_subkeys):
                        sub = winreg.EnumKey(k, i)
                        try:
                            with winreg.OpenKey(k, sub) as subk:
                                state = None
                                num_values = winreg.QueryInfoKey(subk)[1]
                                for v in range(num_values):
                                    vn, vv, _ = winreg.EnumValue(subk, v)
                                    if vn == "DeviceState":
                                        state = vv
                                # DeviceState == 1 indicates active connected device
                                if state == 1:
                                    with winreg.OpenKey(subk, "Properties") as propk:
                                        is_bt = False
                                        name = None
                                        p_values = winreg.QueryInfoKey(propk)[1]
                                        for pv in range(p_values):
                                            pvn, pvv, _ = winreg.EnumValue(propk, pv)
                                            if pvn == "{b3f8fa53-0004-438e-9003-51a46e139bfc},6":
                                                name = pvv
                                            if "BTHENUM" in str(pvv) or "BTHLE" in str(pvv):
                                                is_bt = True
                                        if is_bt and name:
                                            # Normalize name by removing redundant 'Hands-Free' suffix
                                            clean_name = name.replace(" Hands-Free", "").strip()
                                            connected.add(clean_name)
                        except Exception:
                            continue
            except Exception:
                pass
        return connected

    def _check_wifi(self):
        is_connected, ssid = self._get_current_wifi()

        # On first run, record state without speaking alert
        if not self.initial_checked or self.last_wifi_connected is None:
            self.last_wifi_connected = is_connected
            self.last_wifi_ssid = ssid
            if not is_connected:
                from ..assistant.speech_to_text import stt_engine
                stt_engine.set_offline_mode(True)
            return

        # Trigger alert if newly connected or if connected SSID changed
        if is_connected and (not self.last_wifi_connected or ssid != self.last_wifi_ssid):
            logger.info(f"Wi-Fi connected: {ssid}")
            speech = f'wifi "{ssid}" is connected'
            tts.speak(speech)
            self._broadcast("wifi_event", {
                "event": "connected",
                "ssid": ssid,
                "message": speech
            })
            # Switch to online voice system (Local Whisper in standby)
            from ..assistant.speech_to_text import stt_engine
            stt_engine.set_offline_mode(False)

        elif not is_connected and self.last_wifi_connected:
            logger.info(f"Wi-Fi disconnected from {self.last_wifi_ssid}")
            self._broadcast("wifi_event", {
                "event": "disconnected",
                "ssid": self.last_wifi_ssid,
                "message": f'wifi "{self.last_wifi_ssid}" disconnected'
            })
            # Automatically switch to local Whisper STT
            from ..assistant.speech_to_text import stt_engine
            stt_engine.set_offline_mode(True)

        self.last_wifi_connected = is_connected
        self.last_wifi_ssid = ssid

    def _check_bluetooth(self):
        current_bt = self._get_connected_bluetooth()

        # On first run, initialize set
        if not self.initial_checked:
            self.last_bt_devices = current_bt
            return

        # Check newly connected devices
        newly_connected = current_bt - self.last_bt_devices
        for dev in newly_connected:
            logger.info(f"Bluetooth connected: {dev}")
            speech = f'bluetooth "{dev}" is connected'
            tts.speak(speech)
            self._broadcast("bluetooth_event", {
                "event": "connected",
                "device": dev,
                "message": speech
            })

        # Check disconnected devices
        disconnected = self.last_bt_devices - current_bt
        for dev in disconnected:
            logger.info(f"Bluetooth disconnected: {dev}")
            self._broadcast("bluetooth_event", {
                "event": "disconnected",
                "device": dev,
                "message": f'bluetooth "{dev}" disconnected'
            })

        self.last_bt_devices = current_bt


connectivity_monitor = ConnectivityMonitor()
