
from vga32.game import GameApp
import math

class QuakeWire3D(GameApp):
    app_id = "games.quakewire"
    title = "3D Quake Wiremap"
    icon = "star"
    category = "Games"
    width, height = 320, 200
    fps = 15

    def start(self):
        # sample brush world in Quake-ish units, normalized later
        brushes = [
            (-96, -32, -96, 96, 32, 96),      # room floor/box
            (-96, 32, -96, 96, 64, 96),        # upper wall band
            (-96, -64, -96, 96, -32, 96),      # lower pit
            (-80, -32, -80, -48, 32, 80),      # side block
            (48, -32, -80, 80, 32, 80),        # side block
            (-20, -20, -20, 20, 20, 20),        # center obelisk
        ]
        self.boxes = []
        for b in brushes:
            self.boxes.append([v / 64.0 for v in b])
        self.yaw = 0.4
        self.pitch = 0.2
        self.dist = 4.0
        self.scale = 100.0

    def verts(self, box):
        x1,y1,z1,x2,y2,z2 = box
        pts = []
        for x in (x1, x2):
            for y in (y1, y2):
                for z in (z1, z2):
                    pts.append((x,y,z))
        return pts

    def edges(self, pts):
        # box edges by index
        idx = [(0,1),(0,2),(0,4),(1,3),(1,5),(2,3),(2,6),(3,7),(4,5),(4,6),(5,7),(6,7)]
        return [(pts[a], pts[b]) for a,b in idx]

    def project(self, p):
        x,y,z = p
        cy, sy = math.cos(self.yaw), math.sin(self.yaw)
        X = x*cy - z*sy
        Z = x*sy + z*cy
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        Y = y*cp - Z*sp
        Z2 = y*sp + Z*cp
        Z2 += self.dist
        if Z2 <= 0.1:
            return None
        sx = self.width/2 + (X / Z2) * 120
        sy = self.height/2 - (Y / Z2) * 120
        if sx < -100 or sx > self.width+100 or sy < -100 or sy > self.height+100:
            return None
        return int(sx), int(sy)

    def update(self, dt):
        if self.held("left") or self.held("a"):
            self.yaw -= 1.2*dt
        if self.held("right") or self.held("d"):
            self.yaw += 1.2*dt
        if self.held("up") or self.held("w"):
            self.pitch += 1.0*dt
        if self.held("down") or self.held("s"):
            self.pitch -= 1.0*dt
        if self.held("q"):
            self.dist = max(1.5, self.dist - 1.0*dt)
        if self.held("e"):
            self.dist = min(8.0, self.dist + 1.0*dt)
        self.pitch = max(-1.0, min(1.0, self.pitch))

    def render(self, g):
        g.clear("black")
        # grid
        for i in range(-4,5):
            p1 = self.project((i, 0, -4))
            p2 = self.project((i, 0, 4))
            if p1 and p2:
                g.line(p1[0], p1[1], p2[0], p2[1], "darkgray", 1)
            p1 = self.project((-4, 0, i))
            p2 = self.project((4, 0, i))
            if p1 and p2:
                g.line(p1[0], p1[1], p2[0], p2[1], "darkgray", 1)
        # wireframe boxes
        for box in self.boxes:
            pts = self.verts(box)
            pr = [self.project(p) for p in pts]
            for a,b in self.edges(pts):
                pa, pb = self.project(a), self.project(b)
                if pa and pb:
                    g.line(pa[0], pa[1], pb[0], pb[1], "cyan", 1)
        # axes
        o = self.project((0,0,0))
        if o:
            for v,col in [((1,0,0),"red"),((0,1,0),"green"),((0,0,1),"blue")]:
                p = self.project(v)
                if p:
                    g.line(o[0], o[1], p[0], p[1], col, 2)
        # HUD
        g.text(4, 4, "3D Quake Wiremap (rot X/Z:Left/Right, pitch:Up/Down, zoom:Q/E)", "white", size="small")
        g.text(4, self.height-12, "Source: hardcoded sample brushes (Quake .map-like cubes)", "gray", size="small")

    def game_state(self):
        return {"yaw": round(self.yaw,2), "pitch": round(self.pitch,2), "dist": round(self.dist,2), "boxes": len(self.boxes)}
