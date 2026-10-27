import random

from vga32.game import GameApp
from vga32.render3d import Scene, Mesh, Camera
import math

class HermesHuman3D(GameApp):
    app_id = "games.hermes_human3d"
    title = "Hermes Human 3D"
    icon = "star"
    category = "Games"
    width, height = 320, 200
    fps = 12

    def start(self):
        self.scene = Scene(sky=("sky", "black"), ground="teal", fog=("black", 6, 16), ambient=0.38)
        self.grid = self.scene.add(Mesh.grid(16, 16, 8, "darkgray", "gray"), pos=(0, 0, 0))
        # torso
        self.torso = self.scene.add(Mesh.box(0.55, 0.75, 0.32, "blue"), pos=(0, 0.9, 0))
        # head
        self.head = self.scene.add(Mesh.sphere(0.26, "orange", segments=18, rings=10), pos=(0, 1.62, 0))
        # hair cap
        self.scene.add(Mesh.sphere(0.27, "navy", segments=14, rings=7), pos=(0, 1.68, -0.04))
        # shoulders
        self.scene.add(Mesh.box(0.85, 0.18, 0.35, "blue"), pos=(0, 1.25, 0))
        # arms
        self.larm = self.scene.add(Mesh.cylinder(0.08, 0.62, "orange", segments=8), pos=(-0.52, 0.82, 0))
        self.rarm = self.scene.add(Mesh.cylinder(0.08, 0.62, "orange", segments=8), pos=(0.52, 0.82, 0))
        # hands
        self.scene.add(Mesh.sphere(0.08, "orange", segments=8, rings=5), pos=(-0.52, 0.45, 0))
        self.scene.add(Mesh.sphere(0.08, "orange", segments=8, rings=5), pos=(0.52, 0.45, 0))
        # legs
        self.lleg = self.scene.add(Mesh.box(0.18, 0.75, 0.24, "navy"), pos=(-0.14, 0.1, 0))
        self.rleg = self.scene.add(Mesh.box(0.18, 0.75, 0.24, "navy"), pos=(0.14, 0.1, 0))
        # feet
        self.scene.add(Mesh.box(0.22, 0.12, 0.32, "darkgray"), pos=(-0.14, -0.4, 0.06))
        self.scene.add(Mesh.box(0.22, 0.12, 0.32, "darkgray"), pos=(0.14, -0.4, 0.06))
        # face
        self.eyeL = self.scene.add(Mesh.sphere(0.05, "white", segments=8, rings=5), pos=(-0.11, 1.62, 0.24))
        self.eyeR = self.scene.add(Mesh.sphere(0.05, "white", segments=8, rings=5), pos=(0.11, 1.62, 0.24))
        self.scene.add(Mesh.sphere(0.025, "black", segments=6, rings=4), pos=(-0.11, 1.62, 0.27))
        self.scene.add(Mesh.sphere(0.025, "black", segments=6, rings=4), pos=(0.11, 1.62, 0.27))
        self.scene.add(Mesh.box(0.16, 0.03, 0.04, "black"), pos=(-0.10, 1.72, 0.25))
        self.scene.add(Mesh.box(0.16, 0.03, 0.04, "black"), pos=(0.10, 1.72, 0.25))
        self.scene.add(Mesh.box(0.18, 0.05, 0.06, "orange"), pos=(0,1.56,0.24))
        self.scene.add(Mesh.box(0.24, 0.03, 0.05, "red"), pos=(0, 1.50, 0.26))
        # name badge
        self.badge = self.scene.add(Mesh.box(0.7, 0.18, 0.05, "cyan"), pos=(0, 2.1, 0))
        # antennae
        self.scene.add(Mesh.cylinder(0.025, 0.35, "cyan", segments=6), pos=(0.0, 1.95, 0))
        self.scene.add(Mesh.sphere(0.05, "green", segments=6, rings=4), pos=(0, 2.13, 0))
        # obstacles around
        rng = random.Random(1)
        for _ in range(10):
            self.scene.add(Mesh.box(rng.uniform(0.6,1.2), rng.uniform(0.6,1.6), rng.uniform(0.6,1.2), rng.choice(["blue","red","yellow","green","purple"])),
                          pos=(rng.uniform(-8,8), rng.uniform(0.4,0.8), rng.uniform(-8,8)))
        self.cx, self.cz = 0.0, 0.0
        self.cyaw = 0.0
        self.anim = 0.0
        self.moving = False
        self.cam = Camera(pos=(0, 1.5, -3.2), yaw=0.0, pitch=0.1, fov=55)

    def update(self, dt):
        self.anim += dt
        turn = (1 if (self.held("right") or self.held("d")) else 0) - (1 if (self.held("left") or self.held("a")) else 0)
        self.cyaw += turn * 2.0 * dt
        forward = (1 if (self.held("w") or self.held("up")) else 0) - (1 if (self.held("s") or self.held("down")) else 0)
        speed = 2.2 * dt
        vx, vz = math.sin(self.cyaw)*forward*speed, math.cos(self.cyaw)*forward*speed
        self.cx += vx; self.cz += vz
        self.moving = abs(forward) > 0 or abs(turn) > 0
        # camera follow behind
        self.cam.pos[0] = self.cx - math.sin(self.cyaw)*4.0
        self.cam.pos[1] = 1.6
        self.cam.pos[2] = self.cz - math.cos(self.cyaw)*4.0
        self.cam.yaw = self.cyaw
        self.cam.pitch = 0.25
        self.cam.look(*self.mouse_delta(), 0.006)
        # update body positions (rigid)
        self.torso.pos[:] = [self.cx, 0.9 + (abs(math.sin(self.anim*8))*0.04 if self.moving else 0), self.cz]
        self.head.pos[:] = [self.cx, 1.55 + (abs(math.sin(self.anim*8))*0.04 if self.moving else 0), self.cz]
        self.larm.pos[:] = [-0.52 + self.cx, 0.82, self.cz]
        self.rarm.pos[:] = [0.52 + self.cx, 0.82, self.cz]
        self.lleg.pos[:] = [-0.14 + self.cx, 0.1, self.cz]
        self.rleg.pos[:] = [0.14 + self.cx, 0.1, self.cz]
        self.badge.pos[:] = [self.cx, 2.1 + (abs(math.sin(self.anim*8))*0.04 if self.moving else 0), self.cz]
        # limb swing
        if self.moving:
            self.larm.rot[0] = math.sin(self.anim*8)*0.45
            self.rarm.rot[0] = -math.sin(self.anim*8)*0.45
            self.lleg.rot[0] = -math.sin(self.anim*8)*0.35
            self.rleg.rot[0] = math.sin(self.anim*8)*0.35
        else:
            self.larm.rot[0] *= 0.9
            self.rarm.rot[0] *= 0.9
            self.lleg.rot[0] *= 0.9
            self.rleg.rot[0] *= 0.9

    def render(self, g):
        self.scene.render(g, self.cam)
        g.dither()
        g.text(4, 4, "Hermes Human 3D Persona", "white", size="small")
        g.text(4, 16, "Walk: WASD  Look: mouse/click  R restart", "white", size="small")
        g.text(4, self.height-12, f"pos {self.cx:.1f},{self.cz:.1f} moving={self.moving}", "gray", size="small")

    def game_state(self):
        return {"pos": [round(self.cx,2), round(self.cz,2)], "moving": self.moving, "yaw": round(self.cyaw,2)}
