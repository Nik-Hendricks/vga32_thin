import random

from vga32.game import GameApp

class HermesFace(GameApp):
    app_id = "games.hermes_face"
    title = "Hermes Face"
    icon = "star"
    category = "Games"
    width, height = 200, 160
    fps = 6
    mouse_look = False

    def start(self):
        self.t = 0.0
        self.blink = 0.0
        self.next_blink = random.uniform(2.0, 5.0)

    def update(self, dt):
        self.t += dt
        if self.blink > 0:
            self.blink = max(0.0, self.blink - dt*4)
        else:
            self.next_blink -= dt
            if self.next_blink <= 0:
                self.blink = 0.18
                self.next_blink = random.uniform(2.5, 6.0)

    def render(self, g):
        g.clear("navy")
        cx, cy = self.width//2, self.height//2+4
        # head
        g.circle(cx, cy, 62, "yellow", outline="black")
        # hair/cap band
        g.rect(cx-64, cy-58, 128, 18, "blue")
        g.rect(cx-68, cy-46, 136, 8, "blue")
        # eyes
        eye_y = cy - 18
        for ex in (cx-24, cx+24):
            if self.blink < 0.05:
                g.circle(ex, eye_y, 11, "white", outline="black")
                g.circle(ex, eye_y, 5, "black")
                g.circle(ex+2, eye_y-3, 2, "white")
            else:
                g.line(ex-10, eye_y, ex+10, eye_y, "black", 2)
        # smile
        for i in range(-20, 21):
            x = cx + i
            y = cy + 18 + (i*i)//38
            g.pixel(x, y, "black")
            g.pixel(x, y+1, "black")
        # circuit cheeks
        for (px, py) in ((cx-48, cy+4),(cx+48,cy+4)):
            g.rect(px-8, py-2, 16, 4, "cyan")
            g.rect(px-2, py, 4, 10, "cyan")
        g.text(4, 4, "Hermes", "white", size="small")
        g.text(4, self.height-12, "Blinking AI face on VGA", "gray", size="small")

    def game_state(self):
        return {"blink": self.blink, "t": round(self.t,2)}

