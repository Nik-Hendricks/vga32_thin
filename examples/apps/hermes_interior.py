import random

from vga32.game import GameApp
from vga32.render3d import Scene, Mesh, Camera
import math

class HermesInterior3D(GameApp):
    app_id = "games.hermes_interior"
    title = "Hermes Interior 3D"
    icon = "star"
    category = "Games"
    width, height = 320, 200
    fps = 10
    mouse_look = True

    def start(self):
        self.scene = Scene(sky=("black", "black"), ground="#404040", fog=("black", 3, 12), ambient=0.45, light=(-0.5, -0.8, 0.4))
        # room floor and ceiling
        self.scene.add(Mesh.plane(8, 8, "#6a6a6a", double_sided=True), pos=(0, -1.0, 0))
        self.scene.add(Mesh.plane(8, 8, "#222233", double_sided=True), pos=(0, 2.8, 0), rot=(math.pi, 0, 0))
        # walls
        self.scene.add(Mesh.box(8, 3.8, 0.2, "#c8c8c8"), pos=(0, 0.9, 4))
        self.scene.add(Mesh.box(8, 3.8, 0.2, "#c8c8c8"), pos=(0, 0.9, -4))
        self.scene.add(Mesh.box(0.2, 3.8, 8, "#b0b0b0"), pos=(4, 0.9, 0))
        self.scene.add(Mesh.box(0.2, 3.8, 8, "#b0b0b0"), pos=(-4, 0.9, 0))
        # door frame (front wall opening)
        self.scene.add(Mesh.box(1.8, 3.0, 0.25, "#664422"), pos=(0, 0.5, -3.9))
        # furniture: sofa
        self.scene.add(Mesh.box(2.2, 0.6, 0.9, "blue"), pos=(-1.3, -0.4, 1.2))
        self.scene.add(Mesh.box(2.2, 0.9, 0.25, "blue"), pos=(-1.3, 0.1, 1.7))
        # table
        self.scene.add(Mesh.box(1.2, 0.08, 0.8, "#8b5a2b"), pos=(1.2, -0.15, 0.8))
        for dx in (-0.45, 0.45):
            for dz in (-0.28, 0.28):
                self.scene.add(Mesh.box(0.08, 0.6, 0.08, "#553311"), pos=(1.2+dx, -0.45, 0.8+dz))
        # chair
        self.scene.add(Mesh.box(0.7, 0.08, 0.7, "#4444ff"), pos=(1.9, -0.15, 0.0))
        self.scene.add(Mesh.box(0.7, 0.8, 0.1, "#4444ff"), pos=(1.9, 0.3, -0.28))
        # desk + monitor
        self.scene.add(Mesh.box(1.5, 0.08, 0.7, "#555555"), pos=(-1.2, -0.15, -1.8))
        for dx in (-0.6, 0.6):
            self.scene.add(Mesh.box(0.08, 0.65, 0.08, "#333333"), pos=(-1.2+dx, -0.45, -1.8+0.28 if False else -1.8+0.28*dx/0.6))
        self.scene.add(Mesh.box(0.7, 0.45, 0.05, "black"), pos=(-1.2, 0.18, -1.4))
        self.scene.add(Mesh.box(0.12, 0.06, 0.12, "#333333"), pos=(-1.2, -0.0, -1.4))
        # lamp
        self.scene.add(Mesh.cylinder(0.06, 1.4, "orange", segments=8), pos=(2.8, -0.3, 2.2))
        self.scene.add(Mesh.sphere(0.18, "yellow", segments=10, rings=6), pos=(2.8, 1.2, 2.2))
        # rug
        self.scene.add(Mesh.plane(2.5, 1.8, "maroon", double_sided=True), pos=(0, -0.98, 0))
        # bookshelf
        self.scene.add(Mesh.box(0.25, 1.8, 1.6, "#5a3a1a"), pos=(-3.6, 0.0, 1.6))
        for i in range(4):
            self.scene.add(Mesh.box(0.2, 0.15, 1.5, "red"), pos=(-3.6, -0.7 + i*0.45, 1.6))
        # potted plant
        self.scene.add(Mesh.cylinder(0.16, 0.4, "#5a3a1a", segments=8), pos=(3.0, -0.6, -2.0))
        self.scene.add(Mesh.sphere(0.35, "green", segments=10, rings=7), pos=(3.0, 0.1, -2.0))
        # window on right wall (blue rectangle frame)
        self.scene.add(Mesh.box(0.12, 1.2, 1.6, "sky"), pos=(3.9, 0.9, 0.0))
        self.scene.add(Mesh.frame(0.12, 1.2, 1.6, "white") if hasattr(Mesh,"frame") else Mesh.box(0.12,1.2,1.6,"white"))
        self.cam = Camera(pos=(0.0, 0.8, -2.8), yaw=0.0, pitch=0.0, fov=65)
        self.t = 0.0

    def update(self, dt):
        self.t += dt
        dx, dy = self.mouse_delta()
        self.cam.look(dx, dy, 0.006)
        sp = 2.2*dt
        mx = math.cos(self.cam.yaw + math.pi/2)*sp
        mz = math.sin(self.cam.yaw + math.pi/2)*sp
        if self.held("a"):  # strafe left
            self.cam.pos[0] += mx; self.cam.pos[2] += mz
        if self.held("d"):
            self.cam.pos[0] -= mx; self.cam.pos[2] -= mz
        if self.held("w"):
            self.cam.pos[0] += math.sin(self.cam.yaw)*sp
            self.cam.pos[2] += math.cos(self.cam.yaw)*sp
        if self.held("s"):
            self.cam.pos[0] -= math.sin(self.cam.yaw)*sp
            self.cam.pos[2] -= math.cos(self.cam.yaw)*sp
        if self.held("q"):
            self.cam.pos[1] += sp
        if self.held("z"):
            self.cam.pos[1] -= sp
        # clamp inside room
        self.cam.pos[0] = max(-3.6, min(3.6, self.cam.pos[0]))
        self.cam.pos[2] = max(-3.6, min(3.6, self.cam.pos[2]))
        self.cam.pos[1] = max(-0.2, min(2.4, self.cam.pos[1]))

    def render(self, g):
        self.scene.render(g, self.cam)
        g.dither()
        g.text(4, 4, "Hermes Interior 3D", "white", size="small")
        g.text(4, self.height-12, "WASD move  mouse look  Q/Z up/down  Esc release", "gray", size="small")

    def game_state(self):
        return {"pos": [round(float(self.cam.pos[0]),2), round(float(self.cam.pos[1]),2), round(float(self.cam.pos[2]),2)],
                "yaw": round(self.cam.yaw,2)}
