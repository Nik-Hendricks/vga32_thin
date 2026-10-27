
from vga32.game import GameApp
import math, re, os

MAP_PATH = "/root/sm222/maps/sm222_dfl.map"

def parse_map(path):
    boxes = []
    start = (0.0, 0.0, 0.0)
    text = open(path, errors="ignore").read()
    # player start
    for m in re.finditer(r'"classname"\s+"info_player_start".*?"origin"\s+"([^"]+)"', text, flags=re.S):
        coords = [float(v) for v in m.group(1).split()]
        if len(coords) == 3:
            start = tuple(coords)
            break
    # brushes are all top-level blocks with plane definitions
    for brush in re.findall(r"\{([^{}]*\([^\{\}]*\)[^{}]*)\}", text, flags=re.S):
        pts = []
        for m in re.finditer(r"\(\s*([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s*\)", brush):
            pts.append((float(m.group(1)), float(m.group(2)), float(m.group(3))))
        if len(pts) >= 6:
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; zs = [p[2] for p in pts]
            if (max(xs)-min(xs) > 1 and max(ys)-min(ys) > 1 and max(zs)-min(zs) > 1):
                boxes.append((min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)))
    # dedup small
    uniq = []
    for b in boxes:
        if not any(abs(b[i]-u[i]) < 0.5 for u in uniq for i in range(6)):
            uniq.append(b)
    return uniq[:500], start

class QuakeMapWire3D(GameApp):
    app_id = "games.quakemapwire"
    title = "Quake Map Wire 3D"
    icon = "star"
    category = "Games"
    width, height = 320, 200
    fps = 12

    def start(self):
        try:
            self.boxes, self.start_pos = parse_map(MAP_PATH)
        except Exception as e:
            self.boxes, self.start_pos = [], (0,0,0)
            self.error = str(e)
            return
        # normalize origin at player start
        sx,sy,sz = self.start_pos
        norm = []
        for b in self.boxes:
            # map Quake X,Y(horizontal plane) Z(vertical) to x=X,y=Z(vertical),z=Y (depth), scale units
            norm.append(((b[0]-sx)/128.0, (b[2]-sz)/128.0, (b[1]-sy)/128.0,
                         (b[3]-sx)/128.0, (b[5]-sz)/128.0, (b[4]-sy)/128.0))
        self.boxes = norm[:240]  # cap for performance
        # camera angles and position in normalized units (units/128)
        self.px, self.py, self.pz = 0.0, 0.0, 0.0
        self.yaw = 0.0
        self.pitch = 0.0
        self.scale = 1.0 / 128.0

    def update(self, dt):
        if self.error:
            return
        if self.pressed("r"):
            self.start()
            return
        rot = 1.5 * dt
        if self.held("left") or self.held("a"):
            self.yaw -= rot
        if self.held("right") or self.held("d"):
            self.yaw += rot
        if self.held("up") or self.held("w"):
            self.pitch += 1.2 * dt
        if self.held("down") or self.held("s"):
            self.pitch -= 1.2 * dt
        self.pitch = max(-1.2, min(1.2, self.pitch))
        # fly movement
        sp = 1.5 * dt
        fx = math.cos(self.yaw) * math.cos(self.pitch)
        fz = math.sin(self.yaw) * math.cos(self.pitch)
        fy = math.sin(self.pitch)
        if self.held("q"):
            # forward
            self.px += fx * sp
            self.py += fy * sp
            self.pz += fz * sp
        if self.held("e"):
            self.px -= fx * sp
            self.py -= fy * sp
            self.pz -= fz * sp
        if self.held("z"):
            self.px += -math.sin(self.yaw) * sp
            self.pz += math.cos(self.yaw) * sp
        if self.held("c"):
            self.px -= -math.sin(self.yaw) * sp
            self.pz -= math.cos(self.yaw) * sp

    def project(self, x, y, z):
        # world to camera: translate relative to player
        x -= self.px
        y -= self.py
        z -= self.pz
        # rotate yaw
        cy, sy = math.cos(-self.yaw), math.sin(-self.yaw)
        X = x*cy - z*sy
        Z = x*sy + z*cy
        # pitch
        cp, sp = math.cos(-self.pitch), math.sin(-self.pitch)
        Y = y*cp - Z*sp
        Z = y*sp + Z*cp
        Z += 0.2
        if Z <= 0.05:
            return None
        fov = 0.7
        f = fov / Z
        sx = int(self.width/2 + X * f * (self.width/2))
        sy = int(self.height/2 - Y * f * (self.height/2))
        if sx < -200 or sx > self.width+200 or sy < -200 or sy > self.height+200:
            return None
        return sx, sy

    def verts(self, b):
        x1,y1,z1,x2,y2,z2 = b
        return [(x1,y1,z1),(x2,y1,z1),(x1,y2,z1),(x2,y2,z1),
                (x1,y1,z2),(x2,y1,z2),(x1,y2,z2),(x2,y2,z2)]

    def edges(self):
        return [(0,1),(0,2),(0,4),(1,3),(1,5),(2,3),(2,6),(3,7),(4,5),(4,6),(5,7),(6,7)]

    def render(self, g):
        g.clear("black")
        # horizon
        g.rect(0, self.height//2, self.width, self.height//2, "darkgray")
        # wireframe brushes
        drawn = 0
        eis = self.edges()
        for box in self.boxes:
            pts = [self.project(*v) for v in self.verts(box)]
            for a,b in eis:
                pa, pb = pts[a], pts[b]
                if pa is not None and pb is not None:
                    g.line(pa[0], pa[1], pb[0], pb[1], "cyan", 1)
                    drawn += 1
        # HUD
        g.text(4, 4, f"Quake map AABB wireframe: brushes={len(self.boxes)} edges~{drawn}", "white", size="small")
        g.text(4, 16, "Q/E fly, arrows/WASD look, Z/C strafe, R restart", "white", size="small")
        if self.error:
            g.text(4, 30, ("Load error: " + self.error)[:60], "red", size="small")

    def game_state(self):
        return {"brushes": len(self.boxes), "pos": [round(self.px,1), round(self.py,1), round(self.pz,1)],
                "yaw": round(self.yaw,2), "pitch": round(self.pitch,2), "error": self.error}
