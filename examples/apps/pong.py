
from vga32.game import GameApp

class Pong(GameApp):
    app_id = "games.pong"
    title = "Pong"
    icon = "star"
    category = "Games"
    width, height = 320, 200
    fps = 30

    def start(self):
        self.pw, self.ph = 6, 40
        self.player_y = self.height//2 - self.ph//2
        self.ai_y = self.height//2 - self.ph//2
        self.ball_x, self.ball_y = self.width//2, self.height//2
        self.vx, self.vy = -4.0, 3.0
        self.pscore = 0
        self.ascore = 0
        self.over = False

    def update(self, dt):
        if self.pressed("r"):
            self.start()
            return
        if self.over:
            return
        speed = 4.5
        if self.held("up") or self.held("w"):
            self.player_y -= speed
        if self.held("down") or self.held("s"):
            self.player_y += speed
        self.player_y = max(4, min(self.height - self.ph - 4, self.player_y))
        # AI tracks ball with slight error
        target = self.ball_y - self.ph//2
        if self.ai_y < target - 3:
            self.ai_y += 3.5
        elif self.ai_y > target + 3:
            self.ai_y -= 3.5
        self.ai_y = max(4, min(self.height - self.ph - 4, self.ai_y))
        self.ball_x += self.vx
        self.ball_y += self.vy
        if self.ball_y <= 2 or self.ball_y >= self.height - 4:
            self.vy = -self.vy
        # left paddle
        if self.ball_x <= 12 and self.player_y <= self.ball_y + 2 <= self.player_y + self.ph:
            self.vx = abs(self.vx)*1.05
            self.vy += (self.ball_y - (self.player_y + self.ph/2))*0.08
        # right paddle
        if self.ball_x >= self.width-18 and self.ai_y <= self.ball_y + 2 <= self.ai_y + self.ph:
            self.vx = -abs(self.vx)*1.05
            self.vy += (self.ball_y - (self.ai_y + self.ph/2))*0.08
        self.vx = max(-9, min(9, self.vx))
        self.vy = max(-9, min(9, self.vy))
        if self.ball_x < -10:
            self.ascore += 1
            self.reset_ball(1)
        if self.ball_x > self.width + 10:
            self.pscore += 1
            self.reset_ball(-1)
        if self.pscore >= 5 or self.ascore >= 5:
            self.over = True

    def reset_ball(self, direction):
        self.ball_x, self.ball_y = self.width//2, self.height//2
        self.vx, self.vy = (4.0*direction, random.choice([-3.0, -2.0, 2.0, 3.0]))

    def render(self, g):
        g.clear("black")
        g.rect(0, 0, self.width, 2, "darkgray")
        g.rect(0, self.height-2, self.width, 2, "darkgray")
        g.line(self.width//2, 0, self.width//2, self.height, "darkgray", 1)
        g.rect(6, self.player_y, self.pw, self.ph, "lime")
        g.rect(self.width-12, self.ai_y, self.pw, self.ph, "red")
        g.circle(int(self.ball_x), int(self.ball_y), 3, "white")
        g.text(2, 2, f"You {self.pscore}", "lime", size="small")
        g.text(self.width-42, 2, f"CPU {self.ascore}", "red", size="small")
        if self.over:
            g.text(self.width//2, self.height//2, "GAME OVER", "yellow", size="medium", center=True)
            g.text(self.width//2, self.height//2+16, "Press R", "white", size="small", center=True)

    def game_state(self):
        return {"score": self.pscore, "cpu": self.ascore, "over": self.over}
