
from vga32.game import GameApp
from vga32.render3d import Scene, Mesh, Camera
import math

class HermesPersona3D(GameApp):
    app_id = "games.hermes_persona"
    title = "Hermes Persona 3D"
    icon = "star"
    category = "Games"
    width, height = 320, 200
    fps = 12
    mouse_look = True

    def start(self):
        self.scene = Scene(sky=("navy", "black"), ground="teal", fog=("black", 4, 12), ambient=0.4)
        # body / shoulders
        self.scene.add(Mesh.box(1.1, 0.9, 0.7, "navy"), pos=(0, -0.1, 0))
        # head
        self.head = self.scene.add(Mesh.sphere(0.55, "yellow", segments=14, rings=9), pos=(0, 0.65, 0))
        # cap band
        self.scene.add(Mesh.cylinder(0.56, 0.15, "blue", segments=14), pos=(0, 1.02, 0))
        # eyes
        self.scene.add(Mesh.sphere(0.07, "white"), pos=(-0.18, 0.72, 0.46))
        self.scene.add(Mesh.sphere(0.07, "white"), pos=(0.18, 0.72, 0.46))
        self.scene.add(Mesh.sphere(0.04, "black"), pos=(-0.18, 0.72, 0.50))
        self.scene.add(Mesh.sphere(0.04, "black"), pos=(0.18, 0.72, 0.50))
        # nose
        self.scene.add(Mesh.pyramid(0.18, "orange"), pos=(0, 0.55, 0.52))
        # mouth (thin box)
        self.scene.add(Mesh.box(0.34, 0.05, 0.08, "red"), pos=(0, 0.42, 0.50))
        # antennae / horns
        self.scene.add(Mesh.cylinder(0.03, 0.4, "cyan", segments=8), pos=(-0.35, 1.2, 0.1))
        self.scene.add(Mesh.cylinder(0.03, 0.4, "cyan", segments=8), pos=(0.35, 1.2, 0.1))
        # small floating orb
        self.orb = self.scene.add(Mesh.sphere(0.08, "lime", segments=8, rings=5), pos=(0, 1.35, 0.0))
        self.cam = Camera(pos=(0.0, 1.0, -2.6), yaw=0.0, pitch=0.0, fov=60)
        self.t = 0.0

    def update(self, dt):
        self.t += dt
        dx, dy = self.mouse_delta()
        self.cam.look(dx, dy, 0.006)
        if self.held("left") or self.held("a"):
            self.cam.yaw -= 1.2*dt
        if self.held("right") or self.held("d"):
            self.cam.yaw += 1.2*dt
        if self.held("up") or self.held("w"):
            self.cam.pitch = min(1.2, self.cam.pitch + 1.0*dt)
        if self.held("down") or self.held("s"):
            self.cam.pitch = max(-1.2, self.cam.pitch - 1.0*dt)
        # animate
        self.orb.pos[1] = 1.35 + math.sin(self.t*2.5)*0.12
        self.head.rot[1] = math.sin(self.t*0.8)*0.15
        self.cam.walk(0,0,0)

    def render(self, g):
        self.scene.render(g, self.cam)
        g.dither()
        g.text(4, 4, "Hermes 3D Persona", "white", size="small")
        g.text(4, self.height-12, "Mouse (click) look  WASD view  R restart", "white", size="small")

    def game_state(self):
        return {"t": round(self.t,2), "yaw": round(self.cam.yaw,2), "pitch": round(self.cam.pitch,2)}
