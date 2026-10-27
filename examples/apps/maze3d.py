"""A first-person maze: WASD / arrows to move, mouse to look (click to capture, Esc releases).
Collect the yellow orbs. Copy into ~/.vga32/apps/ or install with the install_app tool."""
import math

from vga32.game import GameApp
from vga32.render3d import Camera, Raycaster

MAP = ["################",
       "#......#.......#",
       "#.RR...#..BBB..#",
       "#.R....#....B..#",
       "#......####.B..#",
       "#..G...........#",
       "#..G....######.#",
       "#..GGG..#......#",
       "#.......#..RR..#",
       "################"]


class Maze3D(GameApp):
    app_id = "games.maze3d"
    title = "Maze 3D"
    icon = "star"
    category = "Games"
    width, height = 200, 125
    fps = 30
    mouse_look = True

    def start(self):
        self.world = Raycaster(MAP, colors={"#": "gray", "R": "red", "B": "blue", "G": "green"},
                               ceiling=("navy", "#3060a0"), floor=("#606060", "#202020"), fog=("#202030", 4, 14))
        self.cam = Camera(pos=(1.5, 0, 1.5), yaw=math.pi / 4, fov=66)
        self.orbs = [(5.5, 5.5), (13.5, 1.5), (10.5, 7.5), (2.5, 8.5), (14.5, 5.5)]

    def update(self, dt):
        dx, dy = self.mouse_delta()
        self.cam.look(dx, dy, 0.006)
        self.cam.yaw += self.axis("right", "left") * 2.2 * dt
        speed = 3.0 * dt
        self.world.move(self.cam, (self.axis("w", "s") + self.axis("up", "down")) * speed,
                        self.axis("d", "a") * speed)
        x, z = self.cam.pos[0], self.cam.pos[2]
        left = [o for o in self.orbs if (o[0] - x) ** 2 + (o[1] - z) ** 2 > 0.35]
        self.score += len(self.orbs) - len(left)
        self.orbs = left

    def render(self, g):
        bob = 0.08 * math.sin(self.time * 4)
        self.world.render(g, self.cam, sprites=[(ox, oz, "yellow", 0.35, 0.35 + bob) for ox, oz in self.orbs])
        g.dither()
        g.line(self.width // 2 - 3, self.height // 2, self.width // 2 + 3, self.height // 2, "white")
        g.line(self.width // 2, self.height // 2 - 3, self.width // 2, self.height // 2 + 3, "white")
        g.text(3, 2, f"orbs {self.score}/5" if self.orbs else "You found them all!", "yellow")

    def game_state(self):
        return {"pos": [round(float(self.cam.pos[0]), 2), round(float(self.cam.pos[2]), 2)],
                "yaw": round(self.cam.yaw, 2),
                "orbs_left": len(self.orbs)}
