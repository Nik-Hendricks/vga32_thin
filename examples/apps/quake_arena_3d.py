
import math

from vga32.game import GameApp
from vga32.viewer3d import Viewer3D
from vga32.quake import q2gl
from vga32.gl3d import MeshData, Material

try:
    from vga32.ui import C
except Exception:
    C = None

class QuakeArena3D(Viewer3D):
    app_id = "games.quake_arena3d"
    title = "Quake Arena 3D"
    icon = "star"
    category = "Games"
    width, height = 320, 200
    pixel = 2
    fps = 20
    mouse_look = True

    def __init__(self, desk, path=None, url=None, **kw):
        path = path or "/root/sm222/maps/sm222_ish.bsp"
        super().__init__(desk, path=path, url=url, **kw)
        self.health = 100
        self.score = 0
        self.kills = 0
        self.enemies = []
        self.enemy_nodes = []
        self._enemies_loaded = False

    def start(self):
        super().start()

    def _upload(self):
        super()._upload()
        if (self.renderer is not None and self.level is not None and not self._enemies_loaded):
            try:
                for e in self.level.entities:
                    cn = e.get("classname", "")
                    if cn.startswith("monster_"):
                        try:
                            o = [float(v) for v in e.get("origin", "0 0 0").split()]
                        except Exception:
                            continue
                        pos = q2gl(np.array(o)) if False else None
                        # q2gl expects ndarray; do manually
                        import numpy as np
                        pos = np.array([o[0], o[2], o[1]], dtype=float)
                        pos = pos + np.array([0, 16, 0])  # eye-ish height offset
                        node = self.renderer.add(MeshData.sphere(0.35, 8, 6), Material(color="#ff4444"), pos=tuple(pos.tolist()))
                        self.enemy_nodes.append(node)
                        self.enemies.append({"pos": pos.tolist(), "hp": 3, "alive": True, "node": node, "origin": pos.tolist()})
                self._enemies_loaded = True
            except Exception as ex:
                self.status = "enemy load failed: " + str(ex)[:80]

    def _kill_enemy(self, enemy):
        enemy["alive"] = False
        try:
            self.renderer.remove(enemy["node"])
        except Exception:
            pass
        self.kills += 1
        self.score += 100

    def update(self, dt):
        super().update(dt)
        if self.renderer is None or not self._enemies_loaded:
            return
        cam = self.cam
        for e in self.enemies:
            if not e["alive"]:
                continue
            # simple drift toward player
            v = np.array(cam.pos) - np.array(e["pos"])
            dist = np.linalg.norm(v)
            if dist > 0.35:
                step = min(0.9 * dt, dist)
                e["pos"][0] += v[0] / (dist + 1e-6) * step
                e["pos"][1] += v[1] / (dist + 1e-6) * step
                e["pos"][2] += v[2] / (dist + 1e-6) * step
            e["node"].pos = tuple(e["pos"])
            # damage if very close
            if dist < 1.0:
                self.health = max(0, self.health - 8*dt)
                if self.health <= 0:
                    self.health = 100
                    self.cam.pos = np.array(self.cam.pos) + 0  # keep
        # shoot with x
        if self.pressed("x"):
            # kill closest enemy within 6 units along forward
            best=None; best_d=1e9
            import numpy as np
            fwd = np.array([math.sin(self.cam.yaw), math.sin(self.cam.pitch), math.cos(self.cam.yaw)])
            for e in self.enemies:
                if not e["alive"]:
                    continue
                rel = np.array(e["pos"]) - np.array(self.cam.pos)
                d = np.dot(rel, fwd)
                if d > 0 and d < 12 and np.linalg.norm(rel - fwd*d) < 1.3:
                    if d < best_d:
                        best_d=d; best=e
            if best is not None:
                self._kill_enemy(best)

    def overlay(self, g):
        super().overlay(g)
        g.text(4, 18, f"HP {int(self.health)}  KILLS {self.kills}  SCORE {self.score}  enemies {sum(1 for e in self.enemies if e['alive'])}", "red" if self.health < 30 else "yellow", size="small")
        g.text(4, g.h - 26, "WASD move, mouse look, X shoot, F noclip, R respawn", "white", size="small")

    def game_state(self):
        s = super().game_state()
        s.update({"hp": self.health, "kills": self.kills, "score": self.score,
                  "enemies": sum(1 for e in self.enemies if e["alive"])})
        return s
