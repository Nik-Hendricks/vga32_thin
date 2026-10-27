from vga32.widgets import (Button, Column, Group, Label, Row, TextField, UIApp)
import json, urllib.request, urllib.error

HA_URL_DEFAULT = "http://homeassistant.local:8123"
HA_TOKEN_DEFAULT = "PUT_YOUR_LONG_LIVED_ACCESS_TOKEN_HERE"

class HomeAssistantCommander(UIApp):
    app_id = "home.commander"
    title = "Home Commander"
    icon = "cloud"
    category = "Utilities"
    size = (460, 320)

    _status = "Enter HA URL, token, entity and service."

    def build(self):
        return Column([
            Label("Home Commander", flex=0),
            Group("Connection", Column([
                Row([TextField(HA_URL_DEFAULT, placeholder="http://host:8123", id="url", flex=3)]),
                Row([TextField(HA_TOKEN_DEFAULT, placeholder="long-lived token", id="token", flex=3)]),
            ], gap=4, padding=2)),
            Group("Target", Column([
                Row([TextField("light.living_room", placeholder="entity_id", id="entity", flex=2),
                     TextField("light.turn_on", placeholder="domain.service", id="service", flex=3)]),
                Row([TextField("22", placeholder="value / temperature", id="value", flex=1)]),
            ], gap=4, padding=2)),
            Row([Button("Send", id="send", default=True),
                 Button("On", id="on"),
                 Button("Off", id="off"),
                 Button("Toggle", id="toggle")]),
            Row([Button("Lock", id="lock"),
                 Button("Unlock", id="unlock"),
                 Button("Climate +1", id="heat"),
                 Button("Scene", id="scene")]),
            Column([Label(self._status, id="status", flex=1)], gap=2, padding=2),
        ], gap=8, padding=6)

    def _settings(self):
        return {"url": (self.find("url").value or HA_URL_DEFAULT).strip(),
                "token": self.find("token").value or "",
                "entity": (self.find("entity").value or "").strip(),
                "service": (self.find("service").value or "").strip(),
                "value": (self.find("value").value or "").strip()}

    def _call(self, service, data_extra=None):
        s = self._settings()
        base = s["url"].rstrip("/")
        if "PUT_YOUR_LONG_LIVED" in (s["token"] or ""):
            self._set("status", "Set token first")
            return
        if not s["entity"]:
            self._set("status", "Set entity_id")
            return
        if not service:
            service = s["service"]
        domain, _, name = service.partition(".")
        if not (domain and name):
            self._set("status", "Bad service name")
            return
        data = {"entity_id": s["entity"]}
        if data_extra:
            data.update(data_extra)
        if "value" in data_extra and data_extra.get("value"):
            data["temperature"] = data_extra["value"]
        if s["value"] and "temperature" not in data:
            pass
        payload = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(base + "/api/services/%s/%s" % (domain, name), data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", "Bearer " + s["token"])
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                code = r.status
                body = r.read().decode("utf-8", "replace")[:160]
                self._set("status", "OK %d: %s" % (code, body or service))
        except urllib.error.HTTPError as e:
            try: extra = e.read().decode("utf-8", "replace")[:160]
            except Exception: extra = ""
            self._set("status", "HTTP %d %s" % (e.code, extra))
        except Exception as e:
            self._set("status", "Error: %s" % str(e))

    def _set(self, wid, text):
        try:
            widref = self.find(wid)
            if widref is not None:
                widref.text = str(text)
        except Exception:
            self._status = str(text)

    def on_click(self, w):
        sid = getattr(w, "id", None)
        if sid == "send":
            self._call(self._settings().get("service") or "homeassistant.toggle")
        elif sid == "on":
            self._call("light.turn_on")
        elif sid == "off":
            self._call("light.turn_off")
        elif sid == "toggle":
            self._call("homeassistant.toggle")
        elif sid == "lock":
            self._call("lock.lock")
        elif sid == "unlock":
            self._call("lock.unlock")
        elif sid == "heat":
            try: temp = int(self._settings().get("value") or "1")
            except Exception: temp = 1
            self._call("climate.set_temperature", {"temperature": temp, "entity_id": self._settings().get("entity")})
        elif sid == "scene":
            self._call("scene.turn_on")
        return None
