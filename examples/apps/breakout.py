
from vga32.game import GameApp
import random

class Breakout(GameApp):
    app_id = "games.breakout"
    title = "Breakout"
    icon = "star"
    category = "Games"
    width, height = 320, 200
    fps = 30

    def start(self):
        self.pw, self.ph = 52, 8
        self.px, self.py = self.width//2 - self.pw//2, self.height - 20
        self.ball = [self.width//2, self.height//2, 3.2, -3.2]
        self.bricks = []
        for r in range(4):
            for c in range(7):
                self.bricks.append([c*44+14, 40 + r*16, 38, 12, ["red","orange","yellow","lime"][r]])
        self.score = 0
        self.lives = 3
        self.over = False

    def update(self, dt):
        if self.pressed("r"):
            self.start()
            return
        if self.over:
            return
        sp = 5.0
        if self.held("left") or self.held("a"):
            self.px -= sp
        if self.held("right") or self.held("d"):
            self.px += sp
        self.px = max(4, min(self.width - self.pw - 4, self.px))
        bx, by, vx, vy = self.ball
        bx += vx
        by += vy
        if by <= 4:
            by = 4
            vy = -vy
        if bx <= 2 or bx >= self.width - 4:
            vx = -vx
        # paddle
        if vy > 0 and by + 4 >= self.py and self.px <= bx <= self.px + self.pw:
            by = self.py - 4
            vy = -vy
            vx += (bx - (self.px + self.pw/2))*0.06
        # bricks
        hit = None
        for br in self.bricks:
            x,y,w,h,col = br
            if x <= bx <= x+w and y <= by <= y+h:
                hit = br; break
        if hit:
            self.bricks.remove(hit)
            self.score += 10
            vy = -vy
        if by > self.height + 10:
            self.lives -= 1
            if self.lives <= 0:
                self.over = True
            else:
                self.ball = [self.width//2, self.height//2, 3.2, -3.2]
        self.ball = [bx, by, vx, vy]
        if not self.bricks:
            self.over = True
            self.score += 100

    def render(self, g):
        g.clear("navy")
        for x, y, w, h, col in self.bricks:
            g.rect(x, y, w, h, col, outline="black")
        g.rect(self.px, self.py, self.pw, self.ph, "white")
        bx, by, _, _ = self.ball
        g.circle(int(bx), int(by), 3, "lime")
        g.text(2, 2, f"Score {self.score} Lives {self.lives}", "white", size="small")
        if self.over:
            g.text(self.width//2, self.height//2, "GAME OVER / CLEAR", "yellow", size="medium", center=True)
            g.text(self.width//2, self.height//2+16, "Press R", "white", size="small", center=True)

    def game_state(self):
        return {"score": self.score, "lives": self.lives, "bricks": len(self.bricks), "over": self.over}
