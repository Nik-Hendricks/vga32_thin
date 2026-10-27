import math
import random

from vga32.game import GameApp
from vga32.render3d import Scene, Mesh, Camera

class HermesPersonaHuman3D(GameApp):
    app_id = "games.hermes_persona_human"
    title = "Hermes Persona Human 3D"
    icon = "star"
    category = "Games"
    width, height = 320, 200
    fps = 12
    mouse_look = True

    def start(self):
        self.scene = Scene(sky=("navy", "black"), ground="teal", fog=("black", 6, 16), ambient=0.45)
        # shoulders / torso
        self.torso = self.scene.add(Mesh.box(0.78, 1.0, 0.42, "blue"), pos=(0, 0.72, 0))
        self.scene.add(Mesh.box(0.34, 0.18, 0.20, "blue"), pos=(-0.62, 0.95, 0))  # left pauldron
        self.scene.add(Mesh.box(0.34, 0.18, 0.20, "blue"), pos=(0.62, 0.95, 0))   # right pauldron
        # neck
        self.scene.add(Mesh.cylinder(0.10, 0.16, "orange", segments=10), pos=(0, 1.27, 0))
        # head
        self.head = self.scene.add(Mesh.sphere(0.32, "orange", segments=26, rings=14), pos=(0, 1.55, 0))
        self.jaw = self.scene.add(Mesh.sphere(0.24, "orange", segments=16, rings=8), pos=(0, 1.38, 0.12), scale=(1.1, 0.7, 0.9))
        self.cheekL = self.scene.add(Mesh.sphere(0.09, "orange", segments=10, rings=6), pos=(-0.22, 1.50, 0.10))
        self.cheekR = self.scene.add(Mesh.sphere(0.09, "orange", segments=10, rings=6), pos=(0.22, 1.50, 0.10))
        self.chin  = self.scene.add(Mesh.sphere(0.12, "orange", segments=10, rings=6), pos=(0, 1.32, 0.16))
        # eyebrows
        self.browL = self.scene.add(Mesh.box(0.15, 0.03, 0.05, "black"), pos=(-0.12, 1.66, 0.29))
        self.browR = self.scene.add(Mesh.box(0.15, 0.03, 0.05, "black"), pos=(0.12, 1.66, 0.29))
        # nose bridge
        self.nose = self.scene.add(Mesh.box(0.08, 0.14, 0.08, "orange"), pos=(0, 1.52, 0.30))
        self.nosetip = self.scene.add(Mesh.pyramid(0.09, "red"), pos=(0, 1.43, 0.34))
        # mouth (curve using several spheres)
        for i in range(-3, 4):
            self.scene.add(Mesh.sphere(0.025, "red", segments=6, rings=4), pos=(i*0.055, 1.40 - abs(i)*0.015, 0.28))
        # ears
        self.scene.add(Mesh.sphere(0.07, "orange", segments=8, rings=5), pos=(-0.33, 1.50, 0.0))
        self.scene.add(Mesh.sphere(0.07, "orange", segments=8, rings=5), pos=(0.33, 1.50, 0.0))
        # hair volume
        self.hair = self.scene.add(Mesh.sphere(0.33, "darkgray", segments=16, rings=8), pos=(0, 1.62, -0.05))
        self.hair2 = self.scene.add(Mesh.box(0.62, 0.16, 0.30, "darkgray"), pos=(0, 1.72, 0))
        # ears
        self.scene.add(Mesh.sphere(0.05, "orange", segments=8, rings=5), pos=(-0.33, 1.55, 0.02))
        self.scene.add(Mesh.sphere(0.05, "orange", segments=8, rings=5), pos=(0.33, 1.55, 0.02))
        # cap band
        self.scene.add(Mesh.cylinder(0.32, 0.08, "blue", segments=14), pos=(0, 1.74, 0))
        # eyebrows
        self.scene.add(Mesh.box(0.13, 0.03, 0.04, "black"), pos=(-0.11, 1.64, 0.27))
        self.scene.add(Mesh.box(0.13, 0.03, 0.04, "black"), pos=(0.11, 1.64, 0.27))
        # eyes
        self.eyeL = self.scene.add(Mesh.sphere(0.06, "white", segments=10, rings=6), pos=(-0.11, 1.57, 0.24))
        self.eyeR = self.scene.add(Mesh.sphere(0.06, "white", segments=10, rings=6), pos=(0.11, 1.57, 0.24))
        self.pupilL = self.scene.add(Mesh.sphere(0.03, "black", segments=8, rings=5), pos=(-0.11, 1.57, 0.28))
        self.pupilR = self.scene.add(Mesh.sphere(0.03, "black", segments=8, rings=5), pos=(0.11, 1.57, 0.28))
        # nose
        self.scene.add(Mesh.box(0.08, 0.10, 0.06, "orange"), pos=(0, 1.50, 0.29))
        self.scene.add(Mesh.pyramid(0.08, "red"), pos=(0, 1.46, 0.30))
        # mouth: smile (flattened box row)
        self.mouth = self.scene.add(Mesh.box(0.20, 0.03, 0.04, "red"), pos=(0, 1.45, 0.25))
        self.mouth2 = self.scene.add(Mesh.box(0.10, 0.03, 0.04, "red"), pos=(-0.15, 1.44, 0.24))
        self.mouth3 = self.scene.add(Mesh.box(0.10, 0.03, 0.04, "red"), pos=(0.15, 1.44, 0.24))
        # arms
        self.larm = self.scene.add(Mesh.cylinder(0.08, 0.8, "orange", segments=8), pos=(-0.55, 0.6, 0))
        self.rarm = self.scene.add(Mesh.cylinder(0.08, 0.8, "orange", segments=8), pos=(0.55, 0.6, 0))
        # hands
        self.scene.add(Mesh.sphere(0.10, "orange", segments=10, rings=6), pos=(-0.55, 0.15, 0))
        self.scene.add(Mesh.sphere(0.10, "orange", segments=10, rings=6), pos=(0.55, 0.15, 0))
        # legs
        self.lleg = self.scene.add(Mesh.box(0.24, 0.9, 0.28, "blue"), pos=(-0.20, -0.15, 0))
        self.rleg = self.scene.add(Mesh.box(0.24, 0.9, 0.28, "blue"), pos=(0.20, -0.15, 0))
        # shoes
        self.scene.add(Mesh.box(0.28, 0.12, 0.34, "black"), pos=(-0.20, -0.66, 0.06))
        self.scene.add(Mesh.box(0.28, 0.12, 0.34, "black"), pos=(0.20, -0.66, 0.06))
        # floating badge
        self.orb = self.scene.add(Mesh.sphere(0.07, "cyan", segments=8, rings=5), pos=(0, 2.05, 0))
        self.cam = Camera(pos=(0.0, 1.10, -2.3), yaw=0.0, pitch=0.05, fov=50)
        self.t = 0.0
        self.blink = 0.0
        self.next_blink = random.uniform(2.0, 5.0)

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
        # blink
        if self.blink > 0:
            self.blink = max(0.0, self.blink - dt*5)
            s = 0.25
            self.eyeL.scale[1] = s
            self.eyeR.scale[1] = s
            self.pupilL.scale[1] = s
            self.pupilR.scale[1] = s
        else:
            self.next_blink -= dt
            if self.next_blink <= 0:
                self.blink = 0.16
                self.next_blink = random.uniform(2.5, 6.0)
            self.eyeL.scale[1] = 1.0
            self.eyeR.scale[1] = 1.0
            self.pupilL.scale[1] = 1.0
            self.pupilR.scale[1] = 1.0
        # idle
        self.head.rot[1] = math.sin(self.t*0.7)*0.18
        self.orb.pos[1] = 2.05 + math.sin(self.t*2.0)*0.12
        self.larm.rot[2] = math.sin(self.t*1.2)*0.16
        self.rarm.rot[2] = -math.sin(self.t*1.2)*0.16
        self.torso.pos[1] = 0.75 + math.sin(self.t*1.6)*0.02

    def render(self, g):
        self.scene.render(g, self.cam)
        g.dither()
        g.text(4, 4, "Hermes Human 3D Persona", "white", size="small")
        g.text(4, self.height-12, "Mouse click look  WASD view  R restart", "white", size="small")

    def game_state(self):
        return {"t": round(self.t,2), "yaw": round(self.cam.yaw,2), "pitch": round(self.cam.pitch,2)}
