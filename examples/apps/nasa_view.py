"""NASA Mission Control - live ISS tracking, Astronomy Picture of the Day (with
photo), moon phase, asteroid of the day. All data is fetched off-frame in a
worker thread and degrades gracefully to last-known-good values with per-source
status lights.
"""
import io
import json
import math
import threading
import time
import urllib.request
from collections import deque

from PIL import Image

from vga32.game import GameApp
from vga32.palette import C

APP_ID = "data.nasa"
NASA_KEY = "BJB7pNqThQTjjngR9TFPF6tDNcdFnRjTRwF8hnqQ"
APOD_URL = f"https://api.nasa.gov/planetary/apod?api_key={NASA_KEY}"
ISS_URL = "https://api.wheretheiss.at/v1/satellites/25544"
NEO_URL = "https://api.nasa.gov/neo/rest/v1/feed?start_date=%s&end_date=%s&api_key=%s" % (
    time.strftime("%Y-%m-%d"), time.strftime("%Y-%m-%d"), NASA_KEY)
IMGAPI_URL = "https://images-api.nasa.gov/search?q=galaxy&media_type=image&year_start=2010"

SYNODIC = 29.53058867
NEW_MOON = 947889840.0  # 2000-01-06 18:14 UTC

LAND = [
    [(-166, 66), (-140, 70), (-120, 72), (-95, 74), (-80, 72), (-62, 60), (-55, 52),
     (-65, 45), (-75, 35), (-81, 25), (-97, 26), (-105, 20), (-117, 32), (-125, 40),
     (-140, 58), (-166, 66)],
    [(-80, 10), (-60, 8), (-44, -2), (-35, -8), (-40, -22), (-48, -28), (-58, -38),
     (-68, -52), (-75, -45), (-71, -30), (-70, -18), (-77, -5), (-80, 10)],
    [(-10, 36), (5, 44), (20, 40), (35, 36), (43, 42), (52, 28), (60, 25), (72, 20),
     (77, 8), (90, 22), (105, 10), (117, 23), (122, 30), (122, 40), (135, 45),
     (155, 60), (162, 65), (179, 72), (170, 76), (140, 74), (110, 76), (90, 75),
     (70, 73), (50, 68), (30, 71), (15, 68), (5, 62), (-8, 58), (-6, 48), (-10, 36)],
    [(-17, 15), (-6, 35), (10, 37), (25, 32), (35, 25), (43, 12), (51, 12), (45, -1),
     (35, -25), (32, -34), (18, -28), (9, -2), (-8, 4), (-17, 15)],
    [(114, -22), (122, -17), (132, -11), (142, -12), (147, -18), (153, -27), (150, -37),
     (140, -38), (130, -32), (122, -34), (115, -33), (114, -22)],
    [(2, -49), (31, -47), (37, -38), (55, -43), (85, -49), (115, -66), (95, -66),
     (70, -68), (45, -66), (15, -64), (-5, -60), (-25, -53), (-2, -52), (2, -49)],
    [(68, 24), (72, 20), (77, 8), (80, 13), (88, 25), (82, 28), (75, 28), (68, 24)],
    [(5, 58), (12, 56), (28, 60), (30, 70), (20, 71), (10, 65), (5, 61), (5, 58)],
    [(130, 32), (140, 36), (142, 43), (145, 45), (140, 44), (135, 35), (130, 33), (130, 32)],
    [(-5, 50), (-2, 53), (0, 55), (-4, 58), (-8, 57), (-6, 53), (-5, 50)],
    [(-45, 60), (-30, 68), (-20, 78), (-30, 82), (-55, 80), (-52, 65), (-45, 60)],
    [(173, -35), (178, -38), (176, -42), (172, -44), (167, -46), (170, -42), (173, -38), (173, -35)],
    [(95, 5), (110, -2), (125, -5), (140, -6), (140, -9), (125, -9), (105, -5), (97, 2), (95, 5)],
]

LAT_TOP, LAT_BOT = 85, -70


def _fetch(url, timeout=8):
    return urllib.request.urlopen(url, timeout=timeout).read()


def _moon(frac):
    illum = (1 - math.cos(2 * math.pi * frac)) / 2
    if frac < 0.07 or frac >= 0.93:
        name = "NEW MOON"
    elif frac < 0.22:
        name = "WAXING CRESCENT"
    elif frac < 0.28:
        name = "FIRST QUARTER"
    elif frac < 0.47:
        name = "WAXING GIBBOUS"
    elif frac < 0.57:
        name = "FULL MOON"
    elif frac < 0.72:
        name = "WANING GIBBOUS"
    elif frac < 0.78:
        name = "LAST QUARTER"
    else:
        name = "WANING CRESCENT"
    return name, round(illum * 100)


def _wrap(s, n):
    s = " ".join(str(s).split())
    out, cur = [], ""
    for word in s.split():
        if cur and len(cur) + len(word) + 1 > n:
            out.append(cur)
            cur = word
        else:
            cur = (cur + " " + word).strip()
    if cur:
        out.append(cur)
    return out or [""]


class App(GameApp):
    width, height = 640, 300
    fps = 5
    pause_unfocused = True
    background = "black"
    title = "NASA Mission Control"
    app_id = APP_ID
    category = "Data"
    icon = "star"
    single_instance = True

    def start(self):
        self.iss = None
        self.trail = deque(maxlen=20)
        self.apod = None
        self.neo = None
        self.stat = {"iss": (0.0, False), "apod": (0.0, False), "neo": (0.0, False)}
        self._photo = None
        self._force = True
        self._next_all = 0.0
        th = getattr(self, "_thread", None)
        if th is None or not th.is_alive():
            th = threading.Thread(target=self._loop, daemon=True)
            th.start()
            self._thread = th
        return super().start()

    # ---------------------------------------------------------------- data
    def _loop(self):
        while True:
            if self.pressed("r") or self._force or time.time() > self._next_all:
                self._force = False
                self._next_all = time.time() + 300
                self._all()
            try:
                b = _fetch(ISS_URL)
                d = json.loads(b)
                self.iss = {
                    "lat": float(d["latitude"]), "lon": float(d["longitude"]),
                    "alt": float(d["altitude"]), "vel": float(d["velocity"]),
                    "vis": d.get("visibility", "?").upper(), "ts": time.time(),
                }
                self.trail.append((self.iss["lat"], self.iss["lon"]))
                self.stat["iss"] = (time.time(), True)
            except Exception:
                self.stat["iss"] = (time.time(), False)
            time.sleep(20)

    def _archive_image(self):
        """NASA image archive (no key) -> {title,date,text,url} or None."""
        for q in ("galaxy", "nebula"):
            for _ in range(2):
                try:
                    d = json.loads(_fetch(
                        f"https://images-api.nasa.gov/search?q={q}&media_type=image&year_start=2010",
                        12))
                    item = d["collection"]["items"][0]["data"][0]
                    nid = item.get("nasa_id")
                    if not nid:
                        continue
                    return {
                        "title": item.get("title") or "NASA ARCHIVE",
                        "date": (item.get("date_created") or "")[:10] or "N/A",
                        "text": (item.get("description") or "")[:4000],
                        "url": f"https://images-assets.nasa.gov/image/{nid}/{nid}~orig.jpg",
                    }
                except Exception:
                    time.sleep(1)
        return None

    def _all(self):
        # --- APOD (retries; video APODs pair with an archive image)
        info, photo_url = None, None
        for _ in range(2):
            try:
                d = json.loads(_fetch(APOD_URL, 12))
                if d.get("title"):
                    info = {"title": d["title"][:60], "date": d.get("date", ""),
                            "text": (d.get("explanation") or "")[:4000],
                            "media": d.get("media_type", "image")}
                    if d.get("media_type") == "image" and d.get("url"):
                        photo_url = d["url"]
                    break
            except Exception:
                time.sleep(1)
        if not info or not photo_url:
            fb = self._archive_image()
            if fb:
                if not info:
                    info = dict(fb, media="archive")
                if not photo_url:
                    photo_url = fb["url"]
        if info:
            self.apod = dict(info, ts=time.time())
            self.stat["apod"] = (time.time(), True)
            if photo_url:
                try:
                    from vga32.palette import ordered_dither
                    raw = _fetch(photo_url, 20)[:4_000_000]
                    img = Image.open(io.BytesIO(raw)).convert("RGB")
                    img.thumbnail((220, 96))
                    self._photo = ordered_dither(img)
                except Exception:
                    self._photo = None
        else:
            self.stat["apod"] = (time.time(), False)
        # --- NEO of the day from the feed (astroidotd requires auth)
        try:
            d = json.loads(_fetch(NEO_URL, 12))
            cands = []
            for lst in d["near_earth_objects"].values():
                for n in lst:
                    for ca in n.get("close_approach_data") or []:
                        km = ca.get("miss_distance", {}).get("kilometers")
                        try:
                            km = float(km)
                        except (TypeError, ValueError):
                            continue
                        cands.append((km, n))
            if cands:
                km, n = min(cands)
                self.neo = {
                    "name": f"{n.get('name', '?')}{' *' if n.get('is_potentially_hazardous_astro') else ''}"[:22],
                    "mag": n.get("absolute_magnitude_h"), "km": km, "ts": time.time(),
                }
        except Exception:
            pass
        self.stat["neo"] = (time.time(), self.neo is not None)

    # ------------------------------------------------------------- helpers
    def _px(self, mx, my, MW, MH, lat, lon):
        x = mx + (lon + 180) / 360 * MW
        y = my + (LAT_TOP - lat) / (LAT_TOP - LAT_BOT) * MH
        return x, y

    def _moon_icon(self, g, cx, cy, r):
        frac = ((time.time() - NEW_MOON) / SYNODIC) % 1.0
        waxing = frac < 0.5
        cosv = math.cos(2 * math.pi * frac)
        rr = int(r)
        for y in range(-rr, rr + 1):
            xr = math.sqrt(max(0, r * r - y * y))
            for x in range(-int(xr), int(xr) + 1):
                lit = (x >= xr * cosv) if waxing else (x <= -xr * cosv)
                g.pixel(cx + x, cy + y, "white" if lit else "black")
        g.circle(cx, cy, r, None, "gray")

    # ----------------------------------------------------------------- UI
    def update(self, dt):
        self.pressed("r")

    def render(self, g):
        g.clear("black")
        now = time.time()
        # header
        g.rect(0, 0, 640, 28, "navy")
        g.line(0, 29, 640, 29, "gray")
        g.d.ellipse([4, 3, 25, 24], fill=C.blue)
        g.d.ellipse([2, 8, 27, 22], outline=C.white)
        g.d.polygon([(7, 19), (19, 8), (23, 11), (11, 22)], fill=C.red)
        for sx, sy in ((10, 7), (21, 6), (15, 17), (8, 14)):
            g.d.point((sx, sy), fill=C.white)
        g.text(34, 5, "NASA MISSION CONTROL", "white", "medium")
        if int(self.time * 1.5) % 2 == 0:
            g.text(212, 5, "LIVE", "red", "medium")
        date = time.strftime("%a %d %b").upper()
        clock = time.strftime("%H:%M:%S")
        dw = g.text_width(clock, "medium")
        cw = int(dw)
        dw2 = g.text_width(date, "small")
        g.text(634 - int(dw2) - cw - 10, 7, date, "gray", "small")
        g.text(634 - cw, 5, clock, "yellow", "medium")
        # --- ISS panel
        g.frame(6, 34, 396, 216, "darkgray")
        g.text(12, 39, "ISS LIVE TRACKING", "cyan", "small")
        mx, my, MW, MH = 14, 56, 380, 126
        g.rect(mx - 2, my - 2, MW, MH, "navy")
        g.d.rectangle([mx - 2, my - 2, mx + MW - 1, my + MH - 1], outline=C.darkgray)
        for p in LAND:
            pts = [self._px(mx, my, MW, MH, p[i][1], p[i][0]) for i in range(len(p) - 1)]
            g.poly(pts, "darkgray")
        for gl in range(-150, 181, 30):
            x = mx + (gl + 180) / 360 * MW
            g.line(x, my, x, my + MH, "blue")
        for ga in range(-60, 81, 30):
            y = my + (LAT_TOP - ga) / (LAT_TOP - LAT_BOT) * MH
            col = "gray" if ga == 0 else "blue"
            g.line(mx, y, mx + MW, y, col)
        if len(self.trail) > 1:
            tl = [self._px(mx, my, MW, MH, p[0], p[1]) for p in self.trail]
            for i in range(len(tl) - 1):
                g.line(tl[i][0], tl[i][1], tl[i + 1][0], tl[i + 1][1], "red")
        iss = self.iss
        if iss:
            ix, iy = self._px(mx, my, MW, MH, iss["lat"], iss["lon"])
            ring = 4 + (int(self.time * 3) * 4) % 18
            g.circle(ix, iy, max(2, ring), None, "cyan")
            g.circle(ix, iy, 3, "yellow")
        else:
            g.text(mx + MW // 2 - 40, my + MH // 2 - 7, "NO DATA", "gray", "small")
        # readouts
        if iss:
            g.text(14, 190, f"LAT {abs(iss['lat']):.1f}{'N' if iss['lat'] >= 0 else 'S'}", "white", "medium")
            g.text(134, 190, f"LON {abs(iss['lon']):.1f}{'E' if iss['lon'] >= 0 else 'W'}", "white", "medium")
            g.text(254, 190, f"ALT {iss['alt']:.0f} KM", "white", "medium")
            g.text(14, 212, f"VEL {iss['vel']:,.0f} KM/H", "white", "medium")
            g.text(186, 212, iss["vis"], "lime" if iss["vis"] == "DAYLIGHT" else "orange", "medium")
            age = int(now - iss["ts"])
            g.text(330, 212, f"{age}s OLD", "gray", "medium")
        else:
            g.text(14, 198, "AWAITING TELEMETRY...", "gray", "small")
        # --- APOD panel
        g.frame(408, 34, 226, 216, "darkgray")
        g.text(414, 39, "ASTRO PICTURE OF THE DAY", "yellow", "small")
        ph = self._photo
        if ph is not None:
            g.blit(ph, 414, 56)
            g.frame(414, 56, 220, 96, "gray")
        else:
            g.rect(414, 56, 220, 96, "black")
            g.frame(414, 56, 220, 96, "gray")
            g.text(460, 100, "NO SIGNAL", "gray", "small")
        ap = self.apod
        if ap:
            for i, ln in enumerate(_wrap(ap["title"], 27)[:2]):
                g.text(414, 158 + i * 15, ln, "white", "small")
            g.text(414, 188, f"{ap['date']}  ·  {ap['media'].upper()}", "gray", "small")
            for i, ln in enumerate(_wrap(ap["text"], 27)[:4]):
                g.text(414, 204 + i * 13, ln, "gray", "small")
        else:
            g.text(414, 162, "NO DATA", "gray", "small")
        # --- bottom strip
        g.frame(6, 258, 200, 38, "darkgray")
        self._moon_icon(g, 28, 277, 14)
        mn, il = _moon((time.time() - NEW_MOON) / SYNODIC % 1.0)
        g.text(52, 261, "MOON", "gray", "small")
        g.text(52, 272, mn, "white", "small")
        g.text(52, 284, f"ILLUM {il}%", "cyan", "small")
        g.frame(214, 258, 220, 38, "darkgray")
        g.text(220, 261, "ASTEROID OF THE DAY", "gray", "small")
        nd = self.neo
        if nd:
            g.text(220, 272, nd["name"][:22], "white", "small")
            km = f"{nd['km']:,.0f} KM" if nd["km"] else "?"
            mg = f"MAG {nd['mag']}" if nd["mag"] is not None else ""
            g.text(220, 284, f"{km}  {mg}"[:28], "cyan", "small")
        else:
            g.text(220, 272, "NO DATA", "gray", "small")
        g.frame(442, 258, 192, 38, "darkgray")
        g.text(448, 261, "UPLINK STATUS", "gray", "small")
        x = 448
        for key, label in (("iss", "ISS"), ("apod", "APOD"), ("neo", "NEO")):
            ts, ok = self.stat.get(key, (0, False))
            g.circle(x + 5, 279, 4, "lime" if ok else "red")
            g.text(x + 14, 272, label, "white" if ok else "orange", "small")
            x += 62
        g.text(448, 286, "REFRESH 20S · R=NOW", "gray", "small")

    def game_state(self):
        return {
            "iss": self.iss,
            "apod": (self.apod or {}).get("title"),
            "neo": (self.neo or {}).get("name"),
            "stat": {k: bool(v[1]) for k, v in self.stat.items()},
            "moon": _moon((time.time() - NEW_MOON) / SYNODIC % 1.0),
        }
