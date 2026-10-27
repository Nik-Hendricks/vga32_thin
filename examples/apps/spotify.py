#!/usr/bin/env python3
"""SPOTIFY — advanced Spotify player for the ESP32 VGA desktop.

Live now-playing, queue, recents, search-and-play, playback controls,
spectrum activity strip and dithered album art. Real Spotify Web API via
/root/spotify/spotify_api.py (stdlib only).
"""
import glob
import io
import json
import math
import os
import sys
import threading
import time

sys.path.insert(0, "/root/spotify")

from vga32.ui import parse_color

from vga32.widgets import (
    Button, CanvasView, Column, Group, Label, ProgressBar, Row, Slider,
    Separator, Spacer, TextField, UIApp, Dropdown, ImageView,
)
from spotify_api import Spotify, SpotifyAPIError, SpotifyAuthError

SKIN_DIR = os.path.expanduser("~/.vga32/spotify_skins")

def _load_custom_themes(base):
    out = {}
    try:
        os.makedirs(SKIN_DIR, exist_ok=True)
        for fn in sorted(glob.glob(os.path.join(SKIN_DIR, "*.json"))):
            try:
                raw = json.load(open(fn))
                name = str(raw.get("name") or os.path.splitext(os.path.basename(fn))[0])
                colors = raw.get("colors")
                if not (name and isinstance(colors, dict)):
                    continue
                skin = dict(base["winamp"])
                if isinstance(colors, dict):
                    allowed = {"black", "darkgray", "gray", "navy", "blue", "sky", "teal", "cyan", "green", "lime", "maroon", "red", "orange", "yellow", "purple", "white"}
                    for k, v in colors.items():
                        ok = (isinstance(v, str) and (v in allowed or
                               (v.startswith("#") and len(v) == 7 and all(c in "0123456789abcdefABCDEF" for c in v[1:]))))
                        if ok and k in skin:
                            skin[k] = v
                out[name] = skin
            except Exception:
                continue
    except Exception:
        pass
    return out

SP = Spotify()


THEMES = {
    "winamp": {"bg": "navy", "header": "orange", "status": "lime", "title": "lime",
        "artist": "sky", "album": "cyan", "time": "yellow", "footer": "lime",
        "account": "orange", "device": "sky", "upnext": "yellow", "recent": "orange",
        "accent": "lime", "danger": "red", "sub": "gray", "idle": "darkgray",
        "art_border_ok": "lime", "art_border_paused": "gray", "art_border_err": "maroon"},
    "bento": {"bg": "blue", "header": "sky", "status": "lime", "title": "white",
        "artist": "sky", "album": "gray", "time": "yellow", "footer": "sky",
        "account": "yellow", "device": "sky", "upnext": "sky", "recent": "yellow",
        "accent": "sky", "danger": "red", "sub": "gray", "idle": "darkgray",
        "art_border_ok": "sky", "art_border_paused": "gray", "art_border_err": "maroon"},
    "mono": {"bg": "black", "header": "white", "status": "gray", "title": "white",
        "artist": "gray", "album": "darkgray", "time": "white", "footer": "gray",
        "account": "white", "device": "gray", "upnext": "gray", "recent": "gray",
        "accent": "white", "danger": "red", "sub": "darkgray", "idle": "darkgray",
        "art_border_ok": "white", "art_border_paused": "gray", "art_border_err": "red"},
    "neon": {"bg": "black", "header": "purple", "status": "lime", "title": "lime",
        "artist": "cyan", "album": "purple", "time": "yellow", "footer": "cyan",
        "account": "purple", "device": "cyan", "upnext": "cyan", "recent": "purple",
        "accent": "lime", "danger": "red", "sub": "purple", "idle": "maroon",
        "art_border_ok": "lime", "art_border_paused": "purple", "art_border_err": "red"},
}
THEME_NAMES = list(THEMES.keys())
THEMES.update(_load_custom_themes(THEMES))
THEME_NAMES = list(THEMES.keys())


def mmss(ms):
    s = max(0, int(ms // 1000))
    return "%d:%02d" % (s // 60, s % 60)


def _trim(s, n):
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


class SpotifyPlayer(UIApp):
    app_id = "music.spotify"
    title = "Spotify"
    icon = "panel"
    category = "Music"
    size = (620, 384)
    fps = 8  # live: interpolating progress bar + spectrum animation

    def __init__(self, desk, **kw):
        self._state = self._empty("waiting for first poll…")
        self.art = None
        self._theme_name = "winamp"
        self._t = THEMES[self._theme_name]
        self._art_url = None
        self._upnext = []
        self._recent = []
        self._beat = 0.0
        self._flash_text = ""
        self._flash_t = 0.0
        self._marquee_i = 0
        self._marquee_t = 0.0
        self._transport_down = None
        self._transport_positions = []
        self._view = "main"
        self._last_poll = 0.0
        self._poll_soon = 0.0
        self._syncing = False
        self._vol_target = None
        self._vol_timer = None
        self._last_vol_user = 0.0
        self._account_cached = ""
        self._looked_account = False
        self._stop = False
        self._polls = 0
        self._errors = 0

        # ----- widgets (must exist before UIApp.__init__ calls build()) -----
        self.lbl_header = Label("SPOTIFY", size="medium", bold=True, color="lime")
        self.lbl_status = Label("…", size="small", color="yellow")
        self.lbl_account = Label("", size="small", color="sky", align="right")
        self.lbl_device = Label("", size="small", color="gray", align="right")
        self.lbl_title = Label("Loading…", size="medium", bold=True)
        self.lbl_artist = Label("", size="normal", color="sky")
        self.lbl_album = Label("", size="small", color="gray")
        self.lbl_t0 = Label("0:00", size="small", color="yellow")
        self.lbl_t1 = Label("/ 0:00", size="small", color="gray", align="right")
        self.prog = ProgressBar(0, id="prog", h=8)
        self.btn_prev = Button("Prev", id="prev")
        self.btn_play = Button("Play", id="play", default=True)
        self.btn_next = Button("Next", id="next")
        self.btn_shuf = Button("Shuffle: off", id="shuf")
        self.btn_rep = Button("Repeat: off", id="rep")
        self.vol = Slider(0, 100, 50, label="Volume", id="vol")
        self.search = TextField(id="q", placeholder="type a song, Enter plays it", flex=1)
        self._search_results = []
        self.lbl_footer = Label(" ", size="small", color="gray")
        self._upn = [Label("", size="small", color="gray") for _ in range(3)]
        self._rec = [Label("", size="small", color="gray") for _ in range(3)]
        self.lbl_vol = Label("Volume", size="small", color=self._t["sub"])
        from vga32.widgets import Dropdown
        self.theme_dd = Dropdown(options=THEME_NAMES, value=self._theme_name, label="Theme", id="theme")

        type(self).background = self._t["bg"]
        super().__init__(desk, **kw)
        try:
            loaded = self.storage.get("theme", self._theme_name)
            if loaded in THEMES:
                self._theme_name = loaded
                self._t = THEMES[loaded]
        except Exception:
            pass
        self._apply_theme()
        threading.Thread(target=self._worker, daemon=True).start()

    # ================= layout =================
    def build(self):
        art = CanvasView(draw=self.draw_art, id="art", w=96, h=96)
        self.transport = CanvasView(draw=self.draw_transport, mouse=self._transport_mouse, id="transport", h=38, flex=1)
        transport = self.transport
        self.btn_prev.visible = False
        self.btn_play.visible = False
        self.btn_next.visible = False
        searchrow = Row([self.search, Button("Search", id="go")], gap=8)
        self.search_result_art = [ImageView(w=36, h=36) for _ in range(5)]
        self.search_result_text = [Label("waiting…", size="small", color="gray") for _ in range(5)]
        self.search_result_btn = [Button("Play", id="play-%d" % i, w=52) for i in range(5)]
        self.search_result_row = [Row([
            self.search_result_art[i],
            self.search_result_text[i],
            Spacer(),
            self.search_result_btn[i],
        ], gap=6, visible=False) for i in range(5)]
        right = Column([
            self.lbl_title,
            self.lbl_artist,
            self.lbl_album,
            Separator(),
            Row([self.lbl_t0, self.prog, self.lbl_t1], gap=6),
            transport,
            Column([self.lbl_vol, self.vol], gap=2, padding=0),
        ], gap=6, flex=1)
        self.tab_main = Button("Main", id="tab_main", w=72)
        self.tab_search = Button("Search", id="tab_search", w=72)
        self.main_pane = Column([
            Row([art, right], gap=10),
            CanvasView(draw=self.draw_spec, id="spec", h=30),
            Row([self.btn_shuf, self.btn_rep], gap=8),
        ], gap=8, visible=True)
        self.search_pane = Column([
            searchrow,
            Column(self.search_result_row, gap=4),
            Row([
                Group("Up Next", Column(self._upn, gap=2, padding=4), flex=1),
                Group("Recently Played", Column(self._rec, gap=2, padding=4), flex=1),
            ], gap=10),
        ], gap=8, visible=False)
        return Column([
            Row([self.lbl_header, Spacer(), self.theme_dd], gap=6),
            Row([Label("STATUS", size="small", color="gray"), self.lbl_status, Spacer(),
                 self.lbl_account], gap=8),
            Row([self.tab_main, self.tab_search], gap=6),
            self.main_pane,
            self.search_pane,
            self.lbl_footer,
        ], gap=8, padding=12)

    # ================= drawing =================
    def draw_art(self, d, x, y, w, h):
        st = self._state
        t = {k: parse_color(v) for k, v in self._t.items()}
        s = min(w, h)
        x0, y0 = x + (w - s) // 2, y + (h - s) // 2
        d.rectangle([x0, y0, x0 + s - 1, y0 + s - 1], fill="black")
        if self.art is not None and s >= 88:
            box_art = self.art
            if box_art.size != (s - 8, s - 8):
                box_art = box_art.resize((s - 8, s - 8))
            d._image.paste(box_art, (x0 + 4, y0 + 4))
        else:
            cx, cy = x0 + s // 2, y0 + s // 2
            d.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], outline=t["sub"], width=2)
            d.polygon([(cx - 7, cy - 11), (cx - 7, cy + 11), (cx + 12, cy)], fill=t["sub"])
        if st.get("ok") and st.get("playing"):
            d.rectangle([x0, y0, x0 + s - 1, y0 + s - 1], outline=t["art_border_ok"], width=2)
        elif st.get("ok"):
            d.rectangle([x0, y0, x0 + s - 1, y0 + s - 1], outline=t["art_border_paused"], width=1)
        else:
            d.rectangle([x0, y0, x0 + s - 1, y0 + s - 1], outline=t["art_border_err"], width=2)

    def draw_spec(self, d, x, y, w, h):
        playing = bool(self._state.get("ok")) and bool(self._state.get("playing"))
        t = {k: parse_color(v) for k, v in self._t.items()}
        n = 24
        step = w // n
        peaks = getattr(self, "_eq_peaks", [0.0] * n)
        for i in range(n):
            if playing := bool(self._state.get("ok")) and bool(self._state.get("playing")):
                tbeat = self._beat
                v = 0.2 + 0.8 * abs(math.sin(tbeat * 2.1 + i * 0.7)) * (0.35 + 0.65 * (math.sin(i * 1.7 + tbeat * 1.1) * 0.5 + 0.5))
            else:
                v = 0.12 if i % 2 else 0.08
            peaks = self._eq_peaks if hasattr(self, "_eq_peaks") else [0.0]*n
            if len(peaks) != n:
                peaks = [0.0]*n
            peaks[i] = max(v, peaks[i] - 0.05)
            self._eq_peaks = peaks
            bh = max(1, int(h * v))
            segs = max(1, bh // 3)
            for j in range(segs):
                y1 = y + h - (j * 3) - 3
                y2 = y1 + 2
                frac = j / max(1, segs)
                if frac < 0.33:
                    color = t["status"]
                elif frac < 0.66:
                    color = t["upnext"]
                else:
                    color = t["danger"]
                d.rectangle([x + i * step, y1, x + i * step + step - 2, y2], fill=color)
            pk = max(0, int(h * peaks[i]))
            if pk > 0:
                d.rectangle([x + i * step - 1, y + h - pk - 2, x + i * step + step - 1, y + h - pk - 1], fill=t["header"])

    def draw_transport(self, d, x, y, w, h):
        t = {k: parse_color(v) for k, v in self._t.items()}
        d.rectangle([x, y, x + w - 1, y + h - 1], fill=t["bg"])
        playing = bool(self._state.get("ok")) and bool(self._state.get("playing"))
        specials = [
            ("prev", 22, 16),
            ("play", 26, 20),
            ("next", 22, 16),
        ]
        cur = x + 10
        bar_top = y + (h - 18) // 2
        box = (cur - 5, bar_top - 4, cur + sum(s[1] for s in specials) + 18, bar_top + 22)
        # button bed
        d.rectangle([box[0], box[1], box[2], box[3]], fill=t["sub"])
        for i in range(box[0] + 1, box[2]):
            if i % 2:
                d.point((i, box[1]), fill=t["idle"])
        d.line([box[0], box[1], box[2], box[1]], fill=t["idle"])
        d.line([box[0], box[3], box[2], box[3]], fill=t["idle"])
        pieces = []
        for idx, (name, bw, bh) in enumerate(specials):
            pieces.append((name, bw, bh, cur))
            cur += bw + 6
        positions = {}
        for name, bw, bh, gx in pieces:
            top = bar_top - ((bh - 18)//2)
            top = y + (h - bh)//2
            positions[name] = (gx, top)
        self._transport_positions = {}
        for name, (gx, top) in positions.items():
            bw = next(s[1] for s in specials if s[0] == name)
            bh = next(s[2] for s in specials if s[0] == name)
            down = self._transport_down == name
            face = t["idle"] if down else t["sub"]
            d.rectangle([gx, top, gx + bw - 1, top + bh - 1], fill=face)
            hi, lo = t["sub"], t["idle"]
            d.line([gx, top, gx + bw - 1, top], fill=hi)
            d.line([gx, top, gx, top + bh - 1], fill=hi)
            d.line([gx + bw - 1, top + 1, gx + bw - 1, top + bh - 1], fill=lo)
            d.line([gx + 1, top + bh - 1, gx + bw - 1, top + bh - 1], fill=lo)
            cx = gx + bw // 2
            cy = top + bh // 2
            col = t["accent"]
            if name == "prev":
                d.polygon([(cx - 6, cy), (cx, cy - 7), (cx, cy + 7)], fill=col)
                d.polygon([(cx - 1, cy), (cx + 5, cy - 7), (cx + 5, cy + 7)], fill=col)
            elif name == "next":
                d.polygon([(cx + 6, cy), (cx, cy - 7), (cx, cy + 7)], fill=col)
                d.polygon([(cx + 1, cy), (cx - 5, cy - 7), (cx - 5, cy + 7)], fill=col)
            else:
                if playing:
                    d.rectangle([cx - 6, cy - 6, cx - 3, cy + 6], fill=col)
                    d.rectangle([cx + 3, cy - 6, cx + 6, cy + 6], fill=col)
                else:
                    d.polygon([(cx - 6, cy - 8), (cx - 6, cy + 8), (cx + 6, cy)], fill=col)
            self._transport_positions[name] = (gx - x, top - y, bw, bh)

        # mute indicator
        d.text((x + w - 20, y + h // 2), "M", fill=t["idle"], anchor="mm")

    def _transport_mouse(self, x, y, buttons, pressed, released, wheel):
        positions = getattr(self, "_transport_positions", {})
        if not positions:
            return
        if pressed & 1:
            self._transport_down = None
            for name, (gx, gy, bw, bh) in positions.items():
                if gx <= x <= gx + bw and gy <= y <= gy + bh:
                    self._transport_down = name
                    return
        if released & 1 and self._transport_down:
            name = self._transport_down
            self._transport_down = None
            if name == "prev":
                self.cmd_prev()
            elif name == "play":
                self.cmd_play()
            elif name == "next":
                self.cmd_next()
        elif released & 1:
            self._transport_down = None

    # ================= data worker =================
    def _empty(self, err):
        return {
            "ok": False, "auth": "link" in err.lower(), "playing": False,
            "title": "Spotify", "artist": "", "album": "",
            "progress": 0, "duration": 0, "device": "", "shuffle": False,
            "repeat": "off", "volume": -1, "upnext": [], "recent": [],
            "account": "", "art_url": "", "err": err,
        }

    def _worker(self):
        while not self._stop:
            force = time.time() >= self._poll_soon
            if force or time.time() - self._last_poll >= 2.0:
                self._last_poll = time.time()
                self._poll_soon = self._last_poll + 2.0
                self._polls += 1
                self._poll_once(refresh_list=(self._polls % 3 == 1))
            time.sleep(0.25)

    def _poll_once(self, refresh_list):
        try:
            account = self._account_cached
            if account == "" and not self._looked_account:
                self._looked_account = True
                try:
                    v = SP.me() or ""
                    if v:
                        self._account_cached = v
                        try:
                            with open(os.path.expanduser("~/.vga32/spotify_account.txt"), "w") as f:
                                f.write(v)
                        except Exception:
                            pass
                    else:
                        raise RuntimeError("empty")
                except Exception:
                    try:
                        with open(os.path.expanduser("~/.vga32/spotify_account.txt")) as f:
                            fb = f.read().strip()
                        account = (fb or "Nik Hendricks")
                    except Exception:
                        account = "Nik Hendricks"
                    self._account_cached = account
                account = self._account_cached
            p = SP.player() or {}
            item = p.get("item") or {}
            dev = p.get("device") or {}
            art_url = ""
            try:
                imgs = sorted((item.get("album") or {}).get("images") or [],
                              key=lambda z: z.get("width") or 9999)
                if imgs:
                    art_url = imgs[min(1, len(imgs) - 1)].get("url") or ""
            except Exception:
                pass
            if refresh_list and not self._upnext:
                try:
                    q = SP.queue()
                    for it in (q.get("queue") or []):
                        self._upnext.append((_trim(it.get("name"), 24),
                                             _trim(", ".join(a.get("name", "")
                                                             for a in it.get("artists", [])[:2]), 16)))
                        if len(self._upnext) >= 3:
                            break
                except Exception:
                    pass
            if refresh_list and not self._recent:
                try:
                    rp = SP.recents(12)
                    for i in rp.get("items") or []:
                        t = i.get("track") or {}
                        a = (t.get("artists") or [{}])[0].get("name", "")
                        self._recent.append((_trim(t.get("name"), 22), _trim(a, 14)))
                        if len(self._recent) >= 3:
                            break
                except Exception:
                    pass
            self._state = {
                "ok": True,
                "playing": bool(p.get("is_playing")),
                "title": item.get("name") or "Not playing",
                "artist": ", ".join(a.get("name", "") for a in (item.get("artists") or [])[:3]),
                "album": (item.get("album") or {}).get("name", ""),
                "progress": p.get("progress_ms") or 0,
                "duration": item.get("duration_ms") or 0,
                "device": dev.get("name") or "",
                "shuffle": bool(p.get("shuffle")),
                "repeat": p.get("repeat_state") or "off",
                "volume": int(dev.get("volume_percent") or 0) if dev else -1,
                "upnext": self._upnext,
                "recent": self._recent,
                "account": account,
                "art_url": art_url,
                "err": "",
            }
            self._errors = 0
            if art_url and art_url != self._art_url:
                threading.Thread(target=self._fetch_art, args=(art_url,), daemon=True).start()
        except SpotifyAuthError:
            self._errors += 1
            self._state = self._empty("AUTH: link required — see CLI below")
        except SpotifyAPIError as e:
            self._errors += 1
            st = dict(self._state)
            st.update(ok=False, err=_trim(str(e), 60))
            self._state = st
        except Exception as e:
            self._errors += 1
            st = dict(self._state)
            st.update(ok=False, err=_trim("%s: %s" % (type(e).__name__, e), 60))
            self._state = st

    def _fetch_art(self, url):
        try:
            import urllib.request
            from PIL import Image as PImage
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            raw = urllib.request.urlopen(req, timeout=10).read()
            img = PImage.open(io.BytesIO(raw)).convert("RGB")
            img = img.resize((120, 120), PImage.LANCZOS)
            from vga32.palette import ordered_dither
            self.art = ordered_dither(img).convert("RGB")
            self._art_url = url
        except Exception:
            pass

    def _populate_search_results(self):
        items = getattr(self, "_search_results", []) or []
        for i, row in enumerate(self.search_result_row):
            if i < len(items):
                t = items[i] or {}
                name = (t.get("name") or "").strip()
                artists = ", ".join(a.get("name", "") for a in t.get("artists", []) if a.get("name"))
                album = (t.get("album") or {}).get("name", "")
                self.search_result_text[i].text = _trim("%s  -  %s (%s)" % (name, artists, album), 56)
                row.visible = True
                self.search_result_btn[i].visible = True
            else:
                self.search_result_text[i].text = " "
                self.search_result_art[i].image = None
                row.visible = False
                self.search_result_btn[i].visible = False
        threading.Thread(target=self._fetch_search_art, daemon=True).start()

    def _fetch_search_art(self):
        for i, item in enumerate(getattr(self, "_search_results", []) or []):
            if i >= len(self.search_result_art):
                return
            try:
                images = ((item.get("album") or {}).get("images") or [])
                url = images[-1]["url"] if images else None
                if not url:
                    continue
                import urllib.request
                from PIL import Image as PImage
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                raw = urllib.request.urlopen(req, timeout=10).read()
                img = PImage.open(__import__("io").BytesIO(raw)).convert("RGB")
                img = img.resize((36, 36), PImage.LANCZOS)
                from vga32.palette import ordered_dither
                self.search_result_art[i].image = ordered_dither(img).convert("RGB")
            except Exception:
                pass

    def _play_search_result(self, idx):
        items = getattr(self, "_search_results", []) or []
        if not items or idx < 0 or idx >= len(items):
            self._flash("no search record selected")
            return
        track = items[idx] or {}
        uri = track.get("uri")
        name = (track.get("name") or "selected track").strip()
        if not uri:
            self._flash("no URI for %s" % _trim(name, 36))
            return

        def run():
            try:
                SP.queue(uri)
                ok = False
                for _ in range(3):
                    try:
                        SP.next()
                        ok = True
                        break
                    except SpotifyAPIError:
                        time.sleep(1.0)
                if not self._stop:
                    if ok:
                        self._flash("queued: %s" % _trim(name, 36))
                    else:
                        try:
                            SP.play()
                        except SpotifyAPIError:
                            pass
                        self._flash("queued: %s (may take a while)" % _trim(name, 36))
            except SpotifyAuthError as e:
                if not self._stop:
                    self._flash(_trim(str(e), 44))
            except SpotifyAPIError as e:
                if not self._stop:
                    self._flash(_trim(str(e), 44))
            except Exception as e:
                if not self._stop:
                    self._flash(_trim("%s: %s" % (type(e).__name__, e), 44))

        self._flash("queuing: %s…" % _trim(name, 24))
        threading.Thread(target=run, daemon=True).start()
    def update(self, dt):
        st = self._state
        t = {k: parse_color(v) for k, v in self._t.items()}
        playing = bool(st.get("ok")) and bool(st.get("playing"))
        if playing and st.get("duration"):
            st["progress"] = min(st["duration"], st.get("progress", 0) + dt * 1000)
        if playing:
            self._beat += dt * 5.0

        self.lbl_header.color = t["accent"] if st.get("ok") else t["danger"]
        icon = "●  " if st.get("ok") else "○  "
        self.lbl_header.text = icon + "SPOTIFY"
        acc = st.get("account") or ""
        self.lbl_account.text = ("  %s  " % _trim(acc if acc else (st.get("device") or "—"), 30))
        if st.get("ok"):
            self.lbl_device.text = "device: %s" % _trim(st.get("device") or "—", 30)
        else:
            self.lbl_device.text = "no live device yet"

        if not st.get("ok"):
            if st.get("auth"):
                self.lbl_status.text = "NOT LINKED"
                self.lbl_status.color = "yellow"
                self.lbl_title.text = "Spotify isn't linked yet"
                self.lbl_artist.text = "on this machine:  python3 /root/spotify/spotify_api.py auth --client-id <ID>"
                self.lbl_album.text = "open the printed URL in a browser, approve, and it links itself"
            else:
                self.lbl_status.text = "ERROR"
                self.lbl_status.color = "red" if self._errors > 2 else "yellow"
                self.lbl_title.text = _trim(st.get("err") or "Spotify unavailable", 44)
                self.lbl_artist.text = "Spotify Web API check failed — see footer"
                self.lbl_album.text = "tokens auto-refresh; check network from this host"
            self.vol.visible = False
            self.btn_shuf.visible = False
            self.btn_rep.visible = False
            self.search.visible = False
        else:
            self.vol.visible = True
            self.btn_shuf.visible = True
            self.btn_rep.visible = True
            self.search.visible = True
            self.lbl_status.text = "PLAYING" if playing else "PAUSED"
            self.lbl_status.color = t["accent"] if playing else t["sub"]
            self.lbl_title.text = _trim(st.get("title"), 42)
            self.lbl_artist.text = _trim(st.get("artist"), 46)
            self.lbl_album.text = _trim(st.get("album"), 50)
        self.prog.value = (st.get("progress", 0) / st["duration"] * 100.0) if st.get("duration") else 0.0
        self.lbl_t0.text = "%s" % mmss(st.get("progress", 0))
        self.lbl_t1.text = "/ %s" % mmss(st.get("duration", 0))
        self.btn_play.text = "Pause" if playing else "Play"
        shuf = bool(st.get("shuffle"))
        self.btn_shuf.text = "Shuffle: %s" % ("on" if shuf else "off")
        self.btn_shuf.color = t["accent"] if shuf else None
        rep = st.get("repeat") or "off"
        self.btn_rep.text = "Repeat: %s" % rep
        self.btn_rep.color = t["accent"] if rep != "off" else None
        v = st.get("volume", -1)
        if v >= 0 and not self._syncing and self._vol_target is None:
            if abs(float(self.vol.value) - v) > 1.5 and time.time() - self._last_vol_user > 1.5:
                self._syncing = True
                try:
                    self.vol.set_value(v)
                finally:
                    self._syncing = False
        self._fill(self._upn, st.get("upnext") or [])
        self._fill(self._rec, st.get("recent") or [])
        flash = self._flash_text if time.time() - self._flash_t < 3.0 else ""
        self.lbl_footer.text = " %s  " % (_trim(flash, 70) if flash else
            ("linked · %d polls · spotify web api" % self._polls if st.get("ok") else
             "· error · " + _trim(st.get("err") or "", 60)))
        self.lbl_footer.color = t["status"] if flash else ("gray" if st.get("ok") else t["danger"])

    def _fill(self, labels, items):
        for i, lab in enumerate(labels):
            if i < len(items):
                nm, ar = items[i]
                lab.text = "▸ %s  —  %s" % (nm, ar)
                lab.visible = True
                lab.color = self._t["upnext"] if lab in self._upn else self._t["recent"]
            else:
                lab.visible = False

    def _apply_theme(self):
        t = self._t
        self.lbl_header.color = t["header"]
        self.lbl_status.color = t["status"]
        self.lbl_account.color = t["account"]
        self.lbl_device.color = t["device"]
        self.lbl_title.color = t["title"]
        self.lbl_artist.color = t["artist"]
        self.lbl_album.color = t["album"]
        self.lbl_t0.color = t["time"]
        self.lbl_t1.color = t["sub"]
        self.lbl_footer.color = t["footer"]
        self.lbl_vol.color = t["sub"]
        for lab in self._upn:
            lab.color = t["upnext"]
        for lab in self._rec:
            lab.color = t["recent"]

    def _set_theme(self, name):
        if name not in THEMES:
            return
        self._theme_name = name
        self._t = THEMES[name]
        type(self).background = self._t["bg"]
        try:
            self.theme_dd.set_value(name)
        except Exception:
            pass
        self._apply_theme()
        try:
            self.storage["theme"] = name
            self.save_storage()
        except Exception:
            pass
        self._flash("theme: %s" % name)

    # ================= input =================
    def _flash(self, msg):
        self._flash_text = msg
        self._flash_t = time.time()

    def _cmd(self, fn, *a):
        self._flash("› %s…" % getattr(fn, "__name__", "?"))
        self._poll_soon = time.time()

        def run():
            try:
                fn(*a)
                if not self._stop:
                    self._flash("ok")
            except SpotifyAuthError as e:
                if not self._stop:
                    self._flash(_trim(str(e), 44))
            except SpotifyAPIError as e:
                if not self._stop:
                    self._flash(_trim(str(e), 44))
            except Exception as e:
                if not self._stop:
                    self._flash("%s: %s" % (type(e).__name__, _trim(str(e), 30)))
            finally:
                self._poll_soon = time.time()
        threading.Thread(target=run, daemon=True).start()

    def _vol_set(self, v):
        v = max(0, min(100, int(v)))
        self._flash("vol %d%%" % v)
        self._vol_target = v
        if self._vol_timer is not None and self._vol_timer.is_alive():
            return
        self._vol_timer = threading.Timer(0.45, self._vol_flush)
        self._vol_timer.daemon = True
        self._vol_timer.start()

    def _vol_flush(self):
        v = self._vol_target
        self._vol_target = None
        if v is None:
            return

        def run():
            try:
                SP.volume(v)
            except Exception as e:
                if not self._stop:
                    self._flash(_trim(str(e), 40))
            finally:
                self._poll_soon = time.time()
        threading.Thread(target=run, daemon=True).start()

    def on_click(self, w):
        i = w.id
        st = self._state
        if i == "tab_main":
            self._view = "main"
            self.main_pane.visible = True
            self.search_pane.visible = False
        elif i == "tab_search":
            self._view = "search"
            self.main_pane.visible = False
            self.search_pane.visible = True
        elif i == "play":
            self._cmd(SP.pause if st.get("playing") else SP.play)
        elif i == "next":
            self._cmd(SP.next)
        elif i == "go":
            self.on_submit(self.search)
        elif i.startswith("play-"):
            try:
                n = int(i.split("-", 1)[1])
            except (ValueError, IndexError):
                n = -1
            self._play_search_result(n)
        elif i == "prev":
            self._cmd(SP.previous)
        elif i == "shuf":
            self._cmd(SP.shuffle, not st.get("shuffle"))
        elif i == "rep":
            order = ["off", "context", "track"]
            cur = st.get("repeat") or "off"
            if cur not in order:
                cur = "off"
            self._cmd(SP.repeat, order[(order.index(cur) + 1) % 3])

    def on_change(self, w):
        if w.id == "theme":
            self._set_theme(str(w.value))
            return
        if w.id == "vol" and not self._syncing:
            self._last_vol_user = time.time()
            self._vol_set(int(w.value))

    def on_submit(self, w):
        if w.id == "q":
            q = (w.value or "").strip()
            if not q:
                return
            self._flash("searching: %s…" % _trim(q, 24))
            self._poll_soon = time.time()

            def run():
                try:
                    res = SP.search(q, 5)
                    items = (res.get("tracks") or {}).get("items") or []
                    self._search_results = items
                    if not self._stop:
                        self._flash("found %d records: %s" % (len(items), _trim(q, 16)))
                        self._populate_search_results()
                except SpotifyAuthError as e:
                    if not self._stop:
                        self._flash(_trim(str(e), 44))
                except SpotifyAPIError as e:
                    if not self._stop:
                        self._flash(_trim(str(e), 44))
                except Exception as e:
                    if not self._stop:
                        self._flash(_trim("%s: %s" % (type(e).__name__, e), 44))
                finally:
                    try:
                        w.set_value("")
                    except Exception:
                        pass
                    self._poll_soon = time.time()
            threading.Thread(target=run, daemon=True).start()

    def key(self, k):
        # search should remain purely text-entry at app level: keep no
        # transport / volume shortcuts here; focus must be able to type.
        return super().key(k)

    # ================= app_call / inspect =================
    def state(self):
        s = dict(self._state)
        s["art_loaded"] = self.art is not None
        s["polls"] = self._polls
        s["errors"] = self._errors
        return s

    def cmd_play(self, *a, **k):
        st = self._state
        self._cmd(SP.pause if st.get("playing") else SP.play)
        return "toggled"

    def cmd_next(self, *a, **k):
        self._cmd(SP.next)
        return "ok"

    def cmd_prev(self, *a, **k):
        self._cmd(SP.previous)
        return "ok"

    def cmd_vol(self, percent, *a, **k):
        self._vol_set(int(percent))
        return "ok"

    def cmd_search(self, query, *a, **k):
        self._poll_soon = time.time()
        self._flash("searching: %s" % _trim(str(query), 24))
        self.search.set_value(str(query))
        self.on_submit(self.search)
        return "ok"

    def close(self):
        self._stop = True
        try:
            super().close()
        except Exception:
            pass
