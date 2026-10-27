from vga32.widgets import (
    Button, Column, Group, Label, ListBox, Row, TabView, TextField, TextArea, UIApp
)
import ipaddress, json, threading, time, urllib.request
from pathlib import Path

UNITS_FILE = Path("/root/.vga32/esp_network_units.json")
CHANNEL_POOL = [1,6,11,2,7,12,3,8,13,4,9,5,10]

def _http_json(ip, endpoint, timeout=3.0):
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    url = "http://%s%s" % (ip, endpoint)
    with urllib.request.urlopen(url, timeout=timeout) as response:
        data = response.read().decode("utf-8", "replace")
        return json.loads(data)

class EspNetworkManager(UIApp):
    app_id = "esp.network.manager"
    title = "ESP Net Manager"
    icon = "panel"
    category = "Utilities"
    size = (620, 390)
    fps = 3

    def _get_state(self):
        st = self.storage
        st.setdefault("units", [])
        st.setdefault("status", "Ready")
        st.setdefault("adopted_status", "Use Adopt tab")
        st.setdefault("last_data", "No ESP data")
        st.setdefault("collected_networks", {})
        st.setdefault("packet_data", "No packet data")
        st.setdefault("packet_live", False)
        st.setdefault("bt_data", "No Bluetooth data")
        st.setdefault("bt_live", False)
        return st

    def _load_units(self):
        st = self._get_state()
        units = st.setdefault("units", [])
        out = []
        for unit in units or []:
            out.append({
                "name": str(unit.get("name") or unit.get("ip") or "?"),
                "ip": str(unit["ip"]),
                "port": int(unit.get("port", 80)),
                "channel": int(unit.get("channel", 0)),
            })
        st["units"] = out
        try:
            self.save_storage()
        except Exception:
            pass
        return out

    def _save_units(self):
        try:
            self.save_storage()
        except Exception:
            self.log("storage save failed")

    def _selected_unit(self):
        units = self._load_units()
        raw = self._selected_index if hasattr(self, "_selected_index") else -1
        if isinstance(raw, str):
            for index, unit in enumerate(units):
                item = "%s | %s | channel=%d" % (unit["name"], unit["ip"], unit["channel"])
                if raw in (unit["ip"], item):
                    self._selected_index = index
                    return unit
        try:
            idx = int(raw)
        except (TypeError, ValueError, AttributeError):
            idx = -1
        if idx < 0 or idx >= len(units):
            if units:
                self._selected_index = 0
                return units[0]
            return None
        return units[idx]

    def _status_label(self, text):
        st = self._get_state()
        st["status"] = text[:200]
        try:
            self.find("manager_status").text = st["status"]
        except Exception:
            pass
        try:
            self.log(text[:120])
        except Exception:
            pass

    def _refresh_units_ui(self):
        try:
            lb = self.find("units_list")
            units = self._load_units()
            items = ["%s | %s | channel=%d" % (u["name"], u["ip"], u["channel"]) for u in units]
            if not items:
                items = ["No adopted ESP units"]
            lb.set_items(items)
            sel = getattr(self, "_selected_index", -1)
            try:
                sel = int(sel)
            except (TypeError, ValueError):
                sel = -1
            if 0 <= sel < len(items):
                lb.value = items[sel]
            self.find("units_count").text = "Adopted units: %d" % len(units)
        except Exception:
            pass

    def _refresh_found_ui(self):
        try:
            lb = self.find("found_list")
            found = getattr(self, "_found", [])
            items = ["%s (%s)" % (u.get("name", u.get("ip", "?")), u.get("ip", "?")) for u in found]
            if not items:
                items = ["No discovered ESPs"]
            lb.set_items(items)
        except Exception:
            pass

    def _refresh_data_ui(self):
        try:
            text = self._get_state().get("last_data", "No ESP data")
            self.find("data_view").set_value(text[:4000])
        except Exception:
            pass
    
    def _refresh_ssid_ui(self):
        try:
            network_map = self._get_state().get("collected_networks", {})
            networks = sorted(network_map.values(), key=lambda net: (net.get("ssid") or "", net.get("channel", 0)))
            lb = self.find("ssid_list")
            items = ["%s | ch %s | rssi %s | n=%d" % (net.get("ssid") if net.get("ssid") else "<hidden>", net.get("channel", "?"), net.get("rssi", "?"), net.get("seen", 1)) for net in networks]
            if not items:
                items = ["No collected SSIDs"]
            lb.set_items(items)
            self.find("ssid_count").text = "Collected networks: %d" % len(networks)
            details = ["SSID | BSSID | channels | best RSSI | sightings | worker", ""]
            for net in networks:
                details.append("%s | %s | %s | %s | %d | %s" % (
                    net.get("ssid") if net.get("ssid") else "<hidden>",
                    net.get("bssid") or "?",
                    ",".join(str(x) for x in sorted(net.get("channels", set()))),
                    net.get("rssi"),
                    net.get("seen", 1),
                    net.get("worker", "?")))
            self.find("ssid_view").set_value("\n".join(details)[:4000])
        except Exception:
            pass

    def _refresh_packet_ui(self):
        try:
            self.find("packet_view").set_value(self._get_state().get("packet_data", "No packet data")[:4000])
        except Exception:
            pass

    def _refresh_bt_ui(self):
        try:
            self.find("bt_view").set_value(self._get_state().get("bt_data", "No Bluetooth data")[:4000])
        except Exception:
            pass

    def packet_on_click(self, w):
        u = self._selected_unit()
        if not u:
            self._status_label("Select an ESP first")
            return
        try:
            _http_json(u["ip"], "/monitor_on")
            self._get_state()["packet_data"] = "Monitoring enabled for %s\n" % u["ip"]
            self._get_state()["packet_live"] = True
            self._refresh_packet_ui()
        except Exception as exc:
            self._status_label("Monitor error: %s" % str(exc)[:50])

    def packet_off_click(self, w):
        u = self._selected_unit()
        try:
            if u:
                _http_json(u["ip"], "/monitor_off")
        finally:
            self._get_state()["packet_live"] = False
            self._status_label("Packet monitor off")

    def packet_load_click(self, w):
        u = self._selected_unit()
        if not u:
            self._status_label("Select an ESP first")
            return
        try:
            data = _http_json(u["ip"], "/monitor_data")
            summary = self._format_packets(data)
            self._get_state()["packet_data"] = summary
            self._refresh_packet_ui()
        except Exception as exc:
            self._status_label("Packet load error: %s" % str(exc)[:50])

    def packet_auto_click(self, w):
        u = self._selected_unit()
        if not u:
            self._status_label("Select an ESP first")
            return
        try:
            _http_json(u["ip"], "/monitor_on")
        except Exception:
            pass
        self._get_state()["packet_live"] = True
        self._get_state()["packet_data"] = "Auto capture running for %s on channel %s\n" % (u["ip"], u.get("channel", 1))
        self._refresh_packet_ui()
        if not getattr(self, "_packet_thread", None) or not getattr(self, "_packet_thread", threading).is_alive():
            self._packet_thread = threading.Thread(target=self._packet_worker, daemon=True)
            self._packet_thread.start()
        self._status_label("Packet auto capture started")

    def packet_stop_click(self, w):
        self._get_state()["packet_live"] = False
        u = self._selected_unit()
        try:
            if u:
                _http_json(u["ip"], "/monitor_off")
        except Exception:
            pass
        self._status_label("Packet auto capture stopped")

    def _packet_worker(self):
        while self._get_state().get("packet_live"):
            u = self._selected_unit()
            if u:
                try:
                    data = _http_json(u["ip"], "/monitor_data")
                    self._get_state()["packet_data"] = self._format_packets(data)
                    self._refresh_packet_ui()
                except Exception as exc:
                    self._get_state()["packet_data"] = "Packet error: %s" % str(exc)[:100]
                    self._refresh_packet_ui()
            time.sleep(2)

    def bt_scan_click(self, w):
        u = self._selected_unit()
        if not u:
            self._status_label("Select an ESP first")
            return
        self._status_label("Scanning Bluetooth on %s..." % u["ip"])
        threading.Thread(target=self._bt_scan_worker, args=(u,), daemon=True).start()

    def _bt_scan_worker(self, u):
        try:
            data = _http_json(u["ip"], "/bt_scan?duration=4", timeout=10)
            lines = ["Bluetooth scan %s (%s s, %d devices)" % (u["ip"], data.get("duration", 4), data.get("count", len(data.get("devices", []))))]
            for dev in data.get("devices", []):
                lines.append("%s rssi=%s type=%s name=%s" % (
                    dev.get("addr", "?"), dev.get("rssi", "?"), dev.get("addr_type", "?"), dev.get("name") or "<unnamed>"))
            self._get_state()["bt_data"] = "\n".join(lines)
        except Exception as exc:
            self._get_state()["bt_data"] = "Bluetooth scan failed %s: %s" % (u["ip"], str(exc)[:140])
        self._refresh_bt_ui()
        self._status_label("Bluetooth scan complete")

    def _format_packets(self, data):
        from collections import Counter
        frames = data.get("frames", [])
        by_subtype = Counter(f.get("subtype") for f in frames)
        labels = {0: "assoc req", 1: "assoc resp", 2: "reassoc req", 3: "reassoc resp",
                  4: "probe req", 5: "probe resp", 8: "beacon", 9: "ATIM", 10: "disassoc",
                  11: "auth", 12: "deauth", 13: "action", 24: "data"}
        labels = {k: labels.get(k, str(k)) for k in labels}
        unique_tx = len(set(f.get("addr2") for f in frames))
        lines = ["Loaded %d frames (last ring)" % data.get("count", len(frames))]
        lines.append("Unique transmitters: %d" % unique_tx)
        lines.append("Type counts:")
        for subtype, count in sorted(by_subtype.items()):
            lines.append("  %s (subtype %s): %d" % (labels.get(subtype, str(subtype)), subtype, count))
        lines.append("")
        lines.append("Latest %d frames:" % min(40, len(frames)))
        for f in frames[:40]:
            lines.append("  ch=%s subtype=%s rssix=%s src=%s dst=%s bssid=%s" % (
                f.get("channel"), f.get("subtype"), f.get("rssi"),
                f.get("addr2"), f.get("addr1"), f.get("addr3")))
        return "\n".join(lines)

    def build(self):
        st = self._get_state()
        units = self._load_units()

        adopt = Column([
            Label("Adopt ESP32 DPI Units", flex=0),
            Row([
                TextField(value="192.168.1.0/24", id="subnet_field", label="Subnet", flex=1),
                Button("Discover subnet", id="discover_btn", on_click=self.discover_click),
            ], gap=4),
            Row([
                TextField(value="", placeholder="Manual IP add", id="manual_ip", flex=1),
                Button("Add IP", id="manual_add", on_click=self.manual_add_click),
                Button("Adopt found", id="adopt_found", on_click=self.adopt_found_click),
            ], gap=4),
            Label("Discovered:", flex=0),
            ListBox(["No discovered ESPs"], id="found_list", rows=7, flex=1),
            Label("Adoption assigns channels from 1,6,11,2,7,12 automatically.", flex=0),
        ], gap=6, padding=6)

        units_tab = Column([
            Label("Adopted ESP Units", flex=0),
            Label("Adopted units: %d" % len(units), id="units_count", flex=0),
            Row([
                Button("Refresh", id="refresh_units", on_click=self.refresh_units_click),
                Button("Apply channels", id="apply_channels", on_click=self.apply_channels_click),
                Button("Deep scan all", id="deep_scan_all", on_click=self.deep_scan_click),
            ], gap=4),
            ListBox(["No adopted ESP units"], id="units_list", rows=7, flex=1, on_activate=self.unit_activated),
            Group("Selected", Column([
                Label("Choose an ESP above.", id="selected_label", flex=0),
                Row([
                    Button("Scan", id="unit_scan", on_click=self.unit_scan_click),
                    Button("Monitor ON", id="unit_mon_on", on_click=self.unit_monitor_on_click),
                    Button("Monitor OFF", id="unit_mon_off", on_click=self.unit_monitor_off_click),
                    Button("All 14 ch", id="unit_deep", on_click=self.unit_deep_click),
                ], gap=4),
                Row([
                    Button("Load data", id="load_data", on_click=self.load_data_click),
                    Button("Set ch1", id="set_ch1", on_click=lambda b: self.set_selected_channel(1)),
                    Button("Set ch6", id="set_ch6", on_click=lambda b: self.set_selected_channel(6)),
                    Button("Set ch11", id="set_ch11", on_click=lambda b: self.set_selected_channel(11)),
                ], gap=4),
            ], gap=4, padding=4), flex=0),
        ], gap=6, padding=6)

        data = Column([
            Label("ESP Data View", flex=0),
            Row([
                Button("Refresh data", id="refresh_data", on_click=self.refresh_data_click),
                Button("Clear", id="clear_data", on_click=self.clear_data_click),
            ], gap=4),
            TextArea(value=st.get("last_data", "No ESP data"), id="data_view", rows=12, readonly=True, flex=1),
        ], gap=6, padding=6)

        ssids = Column([
            Label("Collected SSIDs", flex=0),
            Label("Collected networks: %d" % len(st.get("collected_networks", {})), id="ssid_count", flex=0),
            Row([
                Button("Refresh", id="refresh_ssids", on_click=self.refresh_ssids_click),
                Button("Clear", id="clear_ssids", on_click=self.clear_ssids_click),
            ], gap=4),
            ListBox(["No collected SSIDs"], id="ssid_list", rows=7, flex=1),
            TextArea(value="", id="ssid_view", rows=12, readonly=True, flex=1),
        ], gap=6, padding=6)

        packets = Column([
            Label("Promiscuous Packet Capture (selected unit)", flex=0),
            Row([
                Button("Monitor ON", id="packet_on", on_click=self.packet_on_click),
                Button("Monitor OFF", id="packet_off", on_click=self.packet_off_click),
                Button("Load", id="packet_load", on_click=self.packet_load_click),
                Button("Auto capture", id="packet_auto", on_click=self.packet_auto_click),
                Button("Stop", id="packet_stop", on_click=self.packet_stop_click),
            ], gap=4),
            Label("No packet data", id="packet_status", flex=0),
            TextArea(value=st.get("packet_data", "No packet data"), id="packet_view", rows=15, readonly=True, flex=1),
        ], gap=6, padding=6)

        bluetooth = Column([
            Label("Bluetooth scan (selected unit)", flex=0),
            Row([
                Button("Scan 4s", id="bt_scan", on_click=self.bt_scan_click),
                Button("Refresh view", id="bt_refresh", on_click=lambda w: self._refresh_bt_ui()),
            ], gap=4),
            Label("No Bluetooth data", id="bt_count", flex=0),
            TextArea(value=st.get("bt_data", "No Bluetooth data"), id="bt_view", rows=15, readonly=True, flex=1),
        ], gap=6, padding=6)
        try:
            self.find("bt_view").set_value(st.get("bt_data", "No Bluetooth data"))
        except Exception:
            pass

        tabs = TabView([("Adopt", adopt), ("Units", units_tab), ("Data", data), ("SSIDs", ssids), ("Packets", packets), ("Bluetooth", bluetooth)], id="tabs", flex=1)

        return Column([
            tabs,
            Label(st.get("status", "Ready"), id="manager_status", flex=0),
        ], gap=4, padding=6)

    def update(self, dt):
        try:
            if getattr(self, "_need_refresh_ui", True):
                self._need_refresh_ui = False
                self._refresh_units_ui()
                self._refresh_found_ui()
                self._refresh_data_ui()
                self._refresh_ssid_ui()
                self._refresh_packet_ui()
        except Exception:
            pass
        try:
            st = self._get_state()
            lbl = self.find("manager_status")
            if lbl is not None:
                lbl.text = st.get("status", "Ready")
        except Exception:
            pass

    def _set_refresh(self):
        self._need_refresh_ui = True

    def _mark_changed(self):
        self._set_refresh()

    def discover_click(self, w):
        subnet = self.find("subnet_field").value
        if not subnet:
            self._status_label("Enter a subnet to discover")
            return
        self._status_label("Discovering " + str(subnet) + "...")
        threading.Thread(target=self._discover_worker, args=(str(subnet),), daemon=True).start()

    def _discover_worker(self, subnet):
        found = []
        try:
            net = ipaddress.ip_network(subnet.strip(), strict=False)
            hosts = list(net.hosts())[:256]
            import concurrent.futures
            def probe(ip):
                try:
                    data = _http_json(str(ip), "/status", timeout=0.6)
                    if isinstance(data, dict) and data.get("type") == "status":
                        return {"name": str(ip), "ip": str(ip), "port": 80, "status": data}
                except Exception:
                    return None
                return None
            with concurrent.futures.ThreadPoolExecutor(max_workers=16) as exe:
                for res in exe.map(probe, hosts):
                    if res is not None:
                        found.append(res)
            self._found = found
            self._status_label("Discovered %d ESP unit(s)" % len(found))
        except Exception as exc:
            self._status_label("Discovery failed: %s" % str(exc)[:120])
            self._found = []
        self._set_refresh()

    def manual_add_click(self, w):
        value = (self.find("manual_ip").value or "").strip()
        if not value:
            return
        units = self._load_units()
        if not any(u["ip"] == value for u in units):
            units.append({"name": value, "ip": value, "port": 80, "channel": CHANNEL_POOL[len(units) % len(CHANNEL_POOL)]})
            self._get_state()["units"] = units
            self._save_units()
            self._selected_index = len(units)-1
        else:
            try:
                self._selected_index = next(i for i,u in enumerate(units) if u["ip"]==value)
            except StopIteration:
                self._selected_index = 0
        self._status_label("Added %s" % value)
        self._set_refresh()

    def adopt_found_click(self, w):
        found = getattr(self, "_found", [])
        if not found:
            self._status_label("No discovered units; discover first")
            return
        units = self._load_units()
        existing = {u["ip"] for u in units}
        added = 0
        for f in found:
            if f["ip"] in existing:
                continue
            units.append({"name": f["ip"], "ip": f["ip"], "port": 80, "channel": CHANNEL_POOL[len(units) % len(CHANNEL_POOL)]})
            added += 1
        self._get_state()["units"] = units
        self._save_units()
        if added:
            self._selected_index = len(units)-1
        self._status_label("Adopted %d new unit(s)" % added)
        self._set_refresh()

    def refresh_units_click(self, w):
        self._refresh_units_ui()
        self._status_label("Units refreshed")

    def unit_activated(self, w):
        lb = self.find("units_list")
        idx = int(lb._index())
        self._selected_index = idx
        units = self._load_units()
        if 0 <= self._selected_index < len(units):
            u = units[self._selected_index]
            try:
                self.find("selected_label").text = "Selected: %s (ch %d)" % (u["ip"], u["channel"])
            except Exception:
                pass

    def apply_channels_click(self, w):
        units = self._load_units()
        self._status_label("Applying channels to %d unit(s)" % len(units))
        def worker():
            for u in units:
                try:
                    _http_json(u["ip"], "/config?channel=%d" % u["channel"])
                except Exception as exc:
                    self._status_label("Channel apply failed for %s: %s" % (u["ip"], str(exc)[:40]))
                    return
            self._status_label("Channels applied")
        threading.Thread(target=worker, daemon=True).start()

    def deep_scan_click(self, w):
        units = self._load_units()
        if not units:
            self._status_label("No units to scan")
            return
        channels = list(range(1, 15))
        groups = [[] for _ in units]
        for idx, ch in enumerate(channels):
            groups[idx % len(units)].append(ch)
        self._status_label("Deep scanning %s channels across %d ESP(s)" % (len(channels), len(units)))
        def unit_sweep(unit, assigned):
            ip = unit["ip"]
            collected = []
            errors = []
            restore = None
            try:
                restore = int(_http_json(ip, "/status").get("scan_channel", unit.get("channel", 1)))
            except Exception:
                restore = int(unit.get("channel", 0) or 1)
            try:
                for ch in assigned:
                    try:
                        _http_json(ip, "/config?channel=%d" % ch)
                        scan = _http_json(ip, "/scan")
                        for ap in scan.get("aps", []):
                            collected.append((ip, ch, ap))
                    except Exception as exc:
                        errors.append("ch %d: %s" % (ch, str(exc)[:40]))
                        if "timeout" in str(exc).lower():
                            pass
            finally:
                ch_restore = restore if restore is not None else unit.get("channel", 0)
                if not ch_restore:
                    ch_restore = 1
                try:
                    _http_json(ip, "/config?channel=%d" % ch_restore)
                except Exception:
                    pass
            return {"ip": ip, "channels": assigned, "collected": collected, "errors": errors}
        def manager():
            lines = ["Deep sweep: %d ESP(s), %d channels" % (len(units), len(channels))]
            groups_desc = ", ".join("%s: %s" % (u["ip"], ",".join(str(x) for x in g)) for u, g in zip(units, groups))
            lines.append("Assignment: %s" % groups_desc)
            results = []
            import concurrent.futures
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(units), 14)) as exe:
                    for r in exe.map(lambda pair: unit_sweep(pair[0], pair[1]), list(zip(units, groups))):
                        results.append(r)
            except Exception as exc:
                lines.append("Sweep failed: %s" % str(exc)[:120])
            new_seen = 0
            channel_counts = {ch: 0 for ch in channels}
            network_map = dict(self._get_state().get("collected_networks", {}) or {})
            sweep_records = []
            for result in results:
                ip = result["ip"]
                for worker_ip, ch, ap in result.get("collected", []):
                    _ = worker_ip
                    ssid = ap.get("ssid") or "<hidden>"
                    bssid = ap.get("bssid") or "?"
                    key = bssid if bssid != "?" else "%s|%s" % (ssid, ch)
                    network = network_map.get(key, {"ssid": ssid, "bssid": bssid, "channels": set(), "seen": 0, "rssi": None, "worker": ip})
                    network["ssid"] = ssid
                    network["bssid"] = bssid
                    network["channel"] = int(ap.get("channel", ch) or ch)
                    network["channels"] = set(network.get("channels", [])) | {network["channel"]}
                    rssi = ap.get("rssi")
                    if network.get("rssi") is None or (rssi is not None and rssi > network["rssi"]):
                        network["rssi"] = rssi
                        network["worker"] = ip
                    network["seen"] = int(network.get("seen", 0)) + 1
                    network_map[key] = network
                    sweep_records.append((ip, ch, ssid, bssid, ap.get("rssi"), ap.get("authmode")))
                    channel_counts[ch] = channel_counts.get(ch, 0) + 1
                if result.get("errors"):
                    lines.append("%s errors: %s" % (ip, "; ".join(result["errors"][:3])))
            # Convert sets so storage can be persisted cleanly.
            serial_map = {}
            for key, network in network_map.items():
                serial = dict(network)
                serial["channels"] = sorted(list(serial["channels"]))
                serial_map[key] = serial
            self._get_state()["collected_networks"] = serial_map
            self._save_units()
            lines.append("Unique network map: %d" % len(serial_map))
            lines.append("AP sightings: %d" % len(sweep_records))
            lines.append("Channel coverage: %s" % ", ".join("ch%s=%d" % (ch, channel_counts.get(ch, 0)) for ch in channels))
            for result in results:
                lines.append("%s: best records from channels %s" % (result["ip"], ",".join(str(x) for x in result["channels"])))
            self._get_state()["last_data"] = "\n".join(lines)
            self._refresh_data_ui()
            self._refresh_ssid_ui()
            self._status_label("Deep sweep complete: %s AP sightings, %d unique SSIDs" % (len(sweep_records), len(serial_map)))
        threading.Thread(target=manager, daemon=True).start()

    def unit_scan_click(self, w):
        u = self._selected_unit()
        if not u:
            self._status_label("Select an ESP first")
            return
        self._status_label("Scanning %s..." % u["ip"])
        def worker():
            try:
                scan = _http_json(u["ip"], "/scan")
                aps = scan.get("aps", [])
                lines = ["Scan %s (%d):" % (u["ip"], len(aps))]
                for ap in aps:
                    lines.append("%s ch=%s rssi=%s auth=%s" % (ap.get("ssid") or "<hidden>", ap.get("channel"), ap.get("rssi"), ap.get("authmode")))
                self._get_state()["last_data"] = "\n".join(lines)
            except Exception as exc:
                self._get_state()["last_data"] = "Scan failed %s: %s" % (u["ip"], str(exc)[:120])
            self._refresh_data_ui()
            self._status_label("Scan complete")
        threading.Thread(target=worker, daemon=True).start()

    def unit_monitor_on_click(self, w):
        u = self._selected_unit()
        if not u:
            return
        threading.Thread(target=lambda: _http_json(u["ip"], "/monitor_on"), daemon=True).start()

    def unit_monitor_off_click(self, w):
        u = self._selected_unit()
        if not u:
            return
        threading.Thread(target=lambda: _http_json(u["ip"], "/monitor_off"), daemon=True).start()

    def unit_deep_click(self, w):
        u = self._selected_unit()
        if not u:
            return
        self._status_label("Deep sweep on %s..." % u["ip"])
        def worker():
            lines = []
            original = u.get("channel", 0)
            for ch in range(1, 15):
                try:
                    _http_json(u["ip"], "/config?channel=%d" % ch)
                    scan = _http_json(u["ip"], "/scan")
                    aps = scan.get("aps", [])
                    lines.append("Channel %d: %d AP(s)" % (ch, len(aps)))
                    for ap in aps:
                        lines.append("   %s rssi=%s ch=%s" % (ap.get("ssid") or "<hidden>", ap.get("rssi"), ap.get("channel")))
                except Exception as exc:
                    lines.append("Channel %d: %s" % (ch, str(exc)[:50]))
                    continue
            if original:
                try:
                    _http_json(u["ip"], "/config?channel=%d" % original)
                except Exception:
                    pass
            self._get_state()["last_data"] = "\n".join(lines)
            self._refresh_data_ui()
            self._status_label("Deep sweep complete")
        threading.Thread(target=worker, daemon=True).start()

    def set_selected_channel(self, channel):
        u = self._selected_unit()
        if not u:
            return
        u["channel"] = channel
        self._save_units()
        self._status_label("Set %s to channel %d (push with Apply)" % (u["ip"], channel))
        self._mark_changed()

    def load_data_click(self, w):
        u = self._selected_unit()
        if not u:
            self._status_label("Select an ESP first")
            return
        self._status_label("Loading data from %s..." % u["ip"])
        def worker():
            try:
                status = _http_json(u["ip"], "/status")
                frames = _http_json(u["ip"], "/monitor_data")
                lines = ["Unit: %s", "Status: %s" % json.dumps(status),
                         "Frames: %d" % int(frames.get("count", 0))]
                lines = ["Unit: " + u["ip"],
                         "Status: " + json.dumps(status),
                         "Frames captured: " + str(frames.get("count", 0))]
                for frame in frames.get("frames", [])[-25:]:
                    lines.append("%s -> %s ch=%s rssi=%s sub=%s" % (
                        frame.get("addr2"), frame.get("addr3"), frame.get("channel"),
                        frame.get("rssi"), frame.get("subtype")))
                self._get_state()["last_data"] = "\n".join(lines)
            except Exception as exc:
                self._get_state()["last_data"] = "Data load failed %s: %s" % (u["ip"], str(exc)[:120])
            self._refresh_data_ui()
            self._status_label("Data loaded")
        threading.Thread(target=worker, daemon=True).start()

    def refresh_data_click(self, w):
        self.load_data_click(w)

    def clear_data_click(self, w):
        self._get_state()["last_data"] = "No ESP data"
        self._refresh_data_ui()
    
    def clear_ssids_click(self, w):
        self._get_state()["collected_networks"] = {}
        self._save_units()
        self._refresh_ssid_ui()
    
    def refresh_ssids_click(self, w):
        self._refresh_ssid_ui()
        self._status_label("Collected SSIDs refreshed")

    def on_click(self, widget):
        # Callbacks are attached per widget, so this is mostly a fallback.
        pass

    def cmd_status(self):
        return {"units": self._load_units(), "status": self._get_state().get("status")}

    def cmd_units(self):
        return {"items": self._load_units()}

    def cmd_discover(self, subnet="192.168.1.0/24"):
        self._discover_worker(subnet)
        return {"found": getattr(self, "_found", [])}

    def cmd_deep_scan(self):
        self.deep_scan_click(None)
        return {"result": "started"}

    def cmd_data(self, ip=None):
        if ip:
            units = self._load_units()
            for u in units:
                if u["ip"] == ip:
                    self._selected_index = units.index(u)
        self.load_data_click(None)
        return {"last_data": self._get_state().get("last_data")}

    def state(self):
        st = self._get_state()
        return {"units": self._load_units(), "status": st.get("status"), "last_data": st.get("last_data")}
