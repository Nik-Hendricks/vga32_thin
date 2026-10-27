
from vga32.game import GameApp

class NeonSnake(GameApp):
    app_id = "games.neon_snake"
    title = "Neon Snake"
    icon = "star"
    category = "Games"
    width, height = 160, 100
    fps = 15

    def start(self):
        self.cx = 8
        self.cols = self.width // self.cx
        self.rows = self.height // self.cx
        self.reset()

    def reset(self):
        self.snake = [(self.cols//2, self.rows//2), (self.cols//2-1, self.rows//2), (self.cols//2-2, self.rows//2)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.acc = 0.0
        self.food = self.make_food()
        self.score = 0
        self.alive = True

    def make_food(self):
        taken = set(self.snake)
        while True:
            p = (self.rng.randrange(self.cols), self.rng.randrange(self.rows))
            if p not in taken:
                return p

    def update(self, dt):
        if self.pressed("r"):
            self.reset()
            return
        if self.pressed("left") or self.pressed("a"):
            if self.direction != (1, 0):
                self.next_direction = (-1, 0)
        if self.pressed("right") or self.pressed("d"):
            if self.direction != (-1, 0):
                self.next_direction = (1, 0)
        if self.pressed("up") or self.pressed("w"):
            if self.direction != (0, 1):
                self.next_direction = (0, -1)
        if self.pressed("down") or self.pressed("s"):
            if self.direction != (0, -1):
                self.next_direction = (0, 1)
        if not self.alive:
            return
        self.acc += dt
        if self.acc < 0.14:
            return
        self.acc = 0.0
        self.direction = self.next_direction
        head = (self.snake[0][0] + self.direction[0], self.snake[0][1] + self.direction[1])
        if head[0] < 0 or head[0] >= self.cols or head[1] < 0 or head[1] >= self.rows or head in self.snake[:-1]:
            self.alive = False
            return
        self.snake.insert(0, head)
        if head == self.food:
            self.score += 10
            self.food = self.make_food()
        else:
            self.snake.pop()

    def render(self, g):
        g.clear("navy")
        for y in range(0, self.height, self.cx):
            g.line(0, y, self.width, y, "black")
        for x in range(0, self.width, self.cx):
            g.line(x, 0, x, self.height, "black")
        fx, fy = self.food
        g.rect(fx*self.cx+2, fy*self.cx+2, self.cx-4, self.cx-4, "red")
        for i, (x, y) in enumerate(self.snake):
            g.rect(x*self.cx+1, y*self.cx+1, self.cx-2, self.cx-2, "lime" if i == 0 else "green")
        g.text(2, 2, f"Score {self.score}", "white", size="small")
        if not self.alive:
            g.text(self.width//2, self.height//2, "Game Over", "red", size="medium", center=True)
            g.text(self.width//2, self.height//2+14, "Press R", "yellow", size="small", center=True)

    def game_state(self):
        return {"score": self.score, "alive": self.alive, "length": len(self.snake)}
