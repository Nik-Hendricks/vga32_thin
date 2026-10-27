"""A small polygon world: spinning shapes on a checkerboard. WASD to walk, mouse to look,
Space / C to fly up and down. Copy into ~/.vga32/apps/ or install with install_app."""
from vga32.game import GameApp
from vga32.render3d import Camera, Mesh, Scene


class Cubes3D(GameApp):
    app_id = "games.cubes3d"
    title = "3D Playground"
    icon = "star"
    category = "Games"
    width, height = 200, 125
    fps = 24
    mouse_look = True

    def start(self):
        s = Scene(sky=("navy", "#80b0ff"), fog=("#80b0ff", 10, 28))
        s.add(Mesh.grid(30, 30, 12, "#208040", "#40a060"))
        self.spinners = [s.add(Mesh.cube(1.2, ["red", "orange", "yellow", "lime", "sky", "purple"]), pos=(0, 1, 6)),
                         s.add(Mesh.sphere(0.8, "#ff8040", 12, 8), pos=(-3, 1, 9)),
                         s.add(Mesh.pyramid(1.6, "yellow"), pos=(3, 0, 8)),
                         s.add(Mesh.cylinder(0.5, 2.5, "#c0c0ff"), pos=(-5, 0, 4))]
        for i in range(6):
            s.add(Mesh.box(0.8, 3 + i % 3, 0.8, "#a0a0a0"), pos=(-12 + i * 5, (3 + i % 3) / 2, 16))
        self.scene = s
        self.cam = Camera(pos=(0, 1.6, 0), fov=70)

    def update(self, dt):
        self.cam.look(*self.mouse_delta())
        self.cam.yaw += self.axis("right", "left") * 2 * dt
        self.cam.walk((self.axis("w", "s") + self.axis("up", "down")) * 4 * dt, self.axis("d", "a") * 4 * dt,
                      self.axis("space", "c") * 3 * dt)
        for i, o in enumerate(self.spinners[:3]):
            o.rot[1] += dt * (1 + i * 0.3)
            o.rot[0] += dt * 0.5 if i == 0 else 0

    def render(self, g):
        self.scene.render(g, self.cam)
        g.dither()
        g.text(3, 2, f"{self.scene.stats.get('faces_drawn', 0)} faces", "white")

    def game_state(self):
        return {"cam": [round(v, 2) for v in self.cam.pos], **self.scene.stats}
