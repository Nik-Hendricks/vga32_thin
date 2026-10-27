from vga32.widgets import (Button, Column, Group, Label, ListBox, Row, TabView, UIApp)
import json, subprocess, sys, time, urllib.request
from datetime import datetime
from pathlib import Path

SCAN_SCRIPT = "/root/network_scan.py"
CAST_CTL = "/root/casttools/venv/bin/python"
CAST_CTL_SCRIPT = "/root/casttools/cast_ctl.py"
HISTORY_FILE = Path("/root/.vga32/device_history.json")

STREAM_URL = "http://192.168.1.215:8123/vga.m3u8"
GEN_SCRIPT = "/root/casttools/gen_hls.py"
HLS_SERVER_SCRIPT = "/root/casttools/hls_server.py"
ALL_CASTS = ["Niks Room TV", "Living Room"]
ESP32_VIDEO = "6oCtmunfXB4"
BIG_BUCK_VIDEO = "aqz-KE-bpKQ"


class HomeCommander(UIApp):
    app_id = "home.commander"
    title = "Home Commander"
    icon = "panel"
    category = "Utilities"
    size = (500, 360)

    def _get_state(self):
        st = self.storage
        st.setdefault("lights", "Off")
        st.setdefault("door", "Locked")
        st.setdefault("temperature", "20")
        st.setdefault("scene", "None")
        st.setdefault("log", "Ready")
        st.setdefault("scan_summary", "Never scanned")
        st.setdefault("cast_summary", "No Cast action yet")
        st.setdefault("stream_summary", "Stream stopped")
        return st

    def _load_history_items(self):
        try:
            raw = HISTORY_FILE.read_text()
            history = json.loads(raw)
        except Exception:
            history = {"devices": {}, "scans": []}
        items = []
        for key, dev in sorted((history.get("devices") or {}).items()):
            ports = ",".join(str(p) for p in (dev.get("ports") or []))
            items.append("%s %s | %s | %s | ports=%s | first=%s | last=%s%s" % (
                "OK" if dev.get("last_online") else "OFF",
                str(dev.get("name", key)),
                str(dev.get("type", "Device")),
                str(dev.get("ip", "?")),
                ports or "-",
                str(dev.get("first_seen", ""))[:19],
                str(dev.get("last_seen", ""))[:19],
                (" UUID=" + str(dev.get("uuid")) if dev.get("uuid") else ""),
            ))
        if not items:
            items = ["No devices discovered yet"]
        return items

    def build(self):
        st = self._get_state()
        home = Column([
            Label("Home Commander", flex=0),
            Group("Status", Column([
                Label("Lights: " + st["lights"], id="light_status", flex=1),
                Label("Door: " + st["door"], id="door_status", flex=1),
                Label("Thermostat: " + st["temperature"] + "C", id="climate_status", flex=1),
                Label("Scene: " + st["scene"], id="scene_status", flex=1),
                Label("Last: " + st["log"], id="log_status", flex=1),
            ], gap=4, padding=4)),
            Group("Controls", Column([
                Row([Button("Lights On", id="lights_on"), Button("Lights Off", id="lights_off"), Button("Toggle Lock", id="lock_toggle")]),
                Row([Button("Thermostat +1", id="heat_up"), Button("Thermostat -1", id="heat_down")]),
                Row([Button("Scene Party", id="party"), Button("Scene Sleep", id="sleep"), Button("Scene All Off", id="alloff")]),
            ], gap=6, padding=4)),
            Label("Independent local home control. No network required.", flex=0),
        ], gap=8, padding=6)

        devices = Column([
            Label("Network + Cast Device History", flex=0),
            Label(st["scan_summary"], id="scan_status", flex=0),
            Row([Button("Scan Network + Cast", id="scan_now"), Button("Refresh View", id="scan_refresh")]),
            ListBox(self._load_history_items(), id="devices_list", rows=14, flex=1),
        ], gap=6, padding=6)

        cast = Column([
            Label("Chromecast Controls", flex=0),
            Label(st["cast_summary"], id="cast_status", flex=0),
            Label(st["stream_summary"], id="stream_status", flex=0),
            Group("Stream VGA Desktop Live", Column([
                Row([Button("Start Stream All TVs", id="stream_start_all"), Button("Stop Stream All TVs", id="stream_stop_all")]),
                Row([Button("Check Stream", id="stream_check")]),
            ], gap=4, padding=4)),
            Group("Play", Column([
                Row([Button("ESP32 Tutorial - Niks Room TV", id="cast_esp_niks"), Button("ESP32 Tutorial - Living Room", id="cast_esp_living")]),
                Row([Button("Big Buck Bunny - Niks Room TV", id="cast_buck_niks"), Button("Big Buck Bunny - Living Room", id="cast_buck_living")]),
            ], gap=4, padding=4)),
            Group("Apps", Column([
                Row([Button("Open YouTube - Niks Room TV", id="cast_yt_niks"), Button("Open YouTube - Living Room", id="cast_yt_living")]),
            ], gap=4, padding=4)),
        ], gap=6, padding=6)

        tabs = TabView([("Home", home), ("Devices", devices), ("Cast", cast)], id="tabs", flex=1)
        return Column([tabs], gap=4, padding=6)

    def _refresh_home(self, st):
        try:
            self.find("light_status").text = "Lights: " + st["lights"]
            self.find("door_status").text = "Door: " + st["door"]
            self.find("climate_status").text = "Thermostat: " + st["temperature"] + "C"
            self.find("scene_status").text = "Scene: " + st["scene"]
            self.find("log_status").text = "Last: " + st["log"]
        except Exception:
            pass

    def _refresh_devices(self, st):
        try:
            ref = self.find("devices_list")
            if ref is not None:
                ref.set_items(self._load_history_items())
            s = self.find("scan_status")
            if s is not None:
                s.text = st.get("scan_summary", "Never scanned")
        except Exception:
            pass

    def _refresh_cast(self, st):
        try:
            c = self.find("cast_status")
            if c is not None:
                c.text = st.get("cast_summary", "No Cast action yet")
        except Exception:
            pass
        self._refresh_stream(st)

    def _refresh_stream(self, st):
        try:
            s = self.find("stream_status")
            if s is not None:
                s.text = st.get("stream_summary", "Stream stopped")
        except Exception:
            pass

    def run_network_scan(self):
        st = self._get_state()
        try:
            cp = subprocess.run(
                ["python3", SCAN_SCRIPT, "--json"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            payload = json.loads(cp.stdout or "{}")
            scanned = payload.get("scan", {}).get("devices", [])
            count = len(scanned)
            now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
            st["scan_summary"] = "Scanned %d devices @ %s" % (count, now)
        except Exception as exc:
            st["scan_summary"] = "Scan failed: %s" % (str(exc)[:90])
            scanned = []
        try:
            self.save_storage()
        except Exception:
            pass
        self._refresh_devices(st)
        return scanned

    def cast_play(self, device, video_id):
        st = self._get_state()
        try:
            cp = subprocess.run(
                [CAST_CTL, CAST_CTL_SCRIPT, "youtube", device, video_id],
                capture_output=True,
                text=True,
                timeout=90,
            )
            tail = (cp.stdout or "").strip().splitlines()
            summary = tail[-1] if tail else "request sent"
            st["cast_summary"] = "%s on %s: %s" % (video_id, device, summary)
        except Exception as exc:
            st["cast_summary"] = "Cast play failed: %s" % (str(exc)[:90])
        try:
            self.save_storage()
        except Exception:
            pass
        self._refresh_cast(st)
        return st["cast_summary"]

    def cast_open_youtube(self, device):
        st = self._get_state()
        try:
            cp = subprocess.run(
                [CAST_CTL, CAST_CTL_SCRIPT, "app", device, "launch", "233637DE"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            tail = (cp.stdout or "").strip().splitlines()
            summary = tail[-1] if tail else "open requested"
            st["cast_summary"] = "Open YouTube on %s: %s" % (device, summary)
        except Exception as exc:
            st["cast_summary"] = "Cast open failed: %s" % (str(exc)[:90])
        try:
            self.save_storage()
        except Exception:
            pass
        self._refresh_cast(st)
        return st["cast_summary"]

    def _ensure_stream(self):
        st = self._get_state()
        for url in (STREAM_URL, STREAM_URL + "?ts=1"):
            try:
                with urllib.request.urlopen(url, timeout=3) as res:
                    if 200 <= int(getattr(res, "code", 200)) < 400:
                        st["stream_summary"] = "Stream ready: " + STREAM_URL
                        return True
            except Exception:
                pass
        try:
            subprocess.Popen(
                [sys.executable, HLS_SERVER_SCRIPT],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception:
            pass
        try:
            subprocess.Popen(
                [sys.executable, GEN_SCRIPT],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception:
            pass
        for _ in range(10):
            time.sleep(1)
            try:
                with urllib.request.urlopen(STREAM_URL, timeout=3) as res:
                    if 200 <= int(getattr(res, "code", 200)) < 400:
                        st["stream_summary"] = "Stream ready: " + STREAM_URL
                        return True
            except Exception:
                pass
        st["stream_summary"] = "Stream failed to start; check gen/server processes"
        return False

    def _discover_cast_tv_names(self):
        names = []
        try:
            scanned = self.run_network_scan()
            for d in (scanned or []):
                if str(d.get("type", "")).lower() == "chromecast":
                    name = str(d.get("name") or d.get("source_name", "")).strip()
                    if name and name not in names:
                        names.append(name)
        except Exception:
            pass
        if not names:
            names = list(ALL_CASTS)
        return names

    def stream_all(self):
        st = self._get_state()
        st["log"] = "Starting stream to all TVs"
        if not self._ensure_stream():
            try: self.save_storage()
            except: pass
            self._refresh_stream(st)
            return st["stream_summary"]
        names = self._discover_cast_tv_names()
        failures = []
        for name in names:
            try:
                subprocess.run([CAST_CTL, CAST_CTL_SCRIPT, "app", name, "launch", "CC1AD845"],
                               capture_output=True, text=True, timeout=60)
                time.sleep(2)
                url = STREAM_URL + "?ts=" + str(int(time.time()))
                cp = subprocess.run(
                    [CAST_CTL, CAST_CTL_SCRIPT, "play", name, url,
                     "--content-type", "application/vnd.apple.mpegurl",
                     "--live", "--title", "VGA Desktop Live"],
                    capture_output=True, text=True, timeout=90)
                if cp.returncode != 0:
                    failures.append(name + ":" + str((cp.stderr or cp.stdout or "")[-60:]))
            except Exception as exc:
                failures.append(name + ":" + str(exc)[-60:])
        if failures:
            st["stream_summary"] = "Stream sent with failures: " + "; ".join(failures)[:180]
        else:
            st["stream_summary"] = "Stream live on %d TV(s)" % len(names)
        try: self.save_storage()
        except: pass
        self._refresh_cast(st)
        return st["stream_summary"]

    def stream_stop_all(self):
        st = self._get_state()
        for name in ALL_CASTS:
            try:
                subprocess.run([CAST_CTL, CAST_CTL_SCRIPT, "stop", name],
                               capture_output=True, text=True, timeout=60)
            except Exception:
                pass
        st["stream_summary"] = "Stream stop requested on %d TV(s)" % len(ALL_CASTS)
        try: self.save_storage()
        except: pass
        self._refresh_cast(st)
        return st["stream_summary"]

    def cmd_stream_all(self):
        return {"result": self.stream_all()}

    def cmd_stream_stop_all(self):
        return {"result": self.stream_stop_all()}

    def _discover_cast_tv_names_unused_placeholder(self):
        return ALL_CASTS

    def on_click(self, w):
        sid = getattr(w, "id", None)
        st = self._get_state()
        if sid == "lights_on":
            st["lights"] = "On"
            st["log"] = "Lights set On"
        elif sid == "lights_off":
            st["lights"] = "Off"
            st["log"] = "Lights set Off"
        elif sid == "lock_toggle":
            st["door"] = ("Unlocked" if st["door"] == "Locked" else "Locked")
            st["log"] = "Door " + ("Unlocked" if st["door"] == "Unlocked" else "Locked")
        elif sid == "heat_up":
            try:
                temp = int(st["temperature"]) + 1
            except Exception:
                temp = 21
            st["temperature"] = str(temp)
            st["log"] = "Temperature " + str(temp)
        elif sid == "heat_down":
            try:
                temp = int(st["temperature"]) - 1
            except Exception:
                temp = 19
            st["temperature"] = str(temp)
            st["log"] = "Temperature " + str(temp)
        elif sid == "party":
            st["scene"] = "Party"
            st["lights"] = "On"
            st["log"] = "Party scene"
        elif sid == "sleep":
            st["scene"] = "Sleep"
            st["lights"] = "Off"
            st["log"] = "Sleep scene"
        elif sid == "alloff":
            st["scene"] = "All Off"
            st["lights"] = "Off"
            st["log"] = "Everything Off"
        elif sid == "scan_now":
            self.run_network_scan()
            st = self._get_state()
        elif sid == "scan_refresh":
            self._refresh_devices(st)
        elif sid == "stream_start_all":
            self.stream_all()
        elif sid == "stream_stop_all":
            self.stream_stop_all()
        elif sid == "stream_check":
            self._ensure_stream()
            st = self._get_state()
        elif sid == "cast_esp_niks":
            self.cast_play("Niks Room TV", ESP32_VIDEO)
        elif sid == "cast_esp_living":
            self.cast_play("Living Room", ESP32_VIDEO)
        elif sid == "cast_buck_niks":
            self.cast_play("Niks Room TV", BIG_BUCK_VIDEO)
        elif sid == "cast_buck_living":
            self.cast_play("Living Room", BIG_BUCK_VIDEO)
        elif sid == "cast_yt_niks":
            self.cast_open_youtube("Niks Room TV")
        elif sid == "cast_yt_living":
            self.cast_open_youtube("Living Room")

        try:
            self.save_storage()
        except Exception:
            pass
        self._refresh_home(st)
        self._refresh_devices(st)
        self._refresh_cast(st)
        return None

    def cmd_scan(self):
        return {"devices": self.run_network_scan()}

    def cmd_devices(self):
        items = self._load_history_items()
        return {"items": items}

    def cmd_cast_play(self, device="Niks Room TV", video_id=ESP32_VIDEO):
        return {"result": self.cast_play(device, video_id)}

    def cmd_cast_open_youtube(self, device="Niks Room TV"):
        return {"result": self.cast_open_youtube(device)}

    def cmd_cast_status(self, device="Niks Room TV"):
        try:
            cp = subprocess.run(
                [CAST_CTL, CAST_CTL_SCRIPT, "status", device, "--json"],
                capture_output=True, text=True, timeout=60)
            return json.loads(cp.stdout or "{}")
        except Exception as exc:
            return {"error": str(exc)}

    def state(self):
        st = self._get_state()
        return {
            "lights": st["lights"],
            "door": st["door"],
            "temperature": st["temperature"],
            "scene": st["scene"],
            "cast_summary": st["cast_summary"],
            "scan_summary": st["scan_summary"],
            "device_count": len(self._load_history_items()),
        }