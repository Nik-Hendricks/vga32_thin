import random
import time
from vga32.game import GameApp

RLE = {
  1: ('Glider', 'bob$2bo$3o!'),
  2: ('LWSS', 'bo2bo$o4b$o3bo$4o!'),
  3: ('Pulsar', '2b3o3b3o2b2$o4bobo4bo$o4bobo4bo$o4bobo4bo$2b3o3b3o2b2$2b3o3b3o2b$o4bobo4bo$o4bobo4bo$o4bobo4bo2$2b3o3b3o!'),
  4: ('R-pentomino', 'b2o$2ob$bo!'),
  5: ('Acorn', 'bo5b$3bo3b$2o2b3o!'),
  6: ('Diehard', '6bob$2o6b$bo3b3o!'),
  7: ('Gosper Gun', '24bo11b$22bobo11b$12b2o6b2o12b2o$11bo3bo4b2o12b2o$2o8bo5bo3b2o14b$2o8bo3bob2o4bobo11b$10bo5bo7bo11b$11bo3bo20b$12b2o!'),
}


def parse_rle(body, ox=0, oy=0):
    cells = set()
    r = c = 0
    n = 0
    for ch in body:
        if ch.isdigit():
            n = n*10 + int(ch)
        elif ch == 'b' or ch == 'o':
            for _ in range(n or 1):
                if ch == 'o':
                    cells.add((ox+c, oy+r))
                c += 1
            n = 0
        elif ch == '$':
            r += 1
            c = 0
            n = 0
        elif ch == '!':
            break
    return cells


class LifeGame(GameApp):
    app_id = 'data.life'
    title = 'Conways Life'
    icon = 'triangles'
    category = 'Data'
    width, height = 620, 340
    fps = 60

    def start(self):
        self.W = 512
        self.H = 320
        self.cells = set()
        self.heat = {}
        self.camx = 256.0
        self.camy = 160.0
        self.zoom = 4.0
        self.speed = 1
        self.playing = True
        self.trail = True
        self.grid = False
        self.gen = 0
        self.undo = []
        self.lmx = None
        self._now = time.time()
        self._msg = ''
        self._mexp = 1e9
        self.load_preset(7)
        self.splash('Gosper Gun live  (1-7 presets, space pause, z/x zoom)', 6.0)

    def splash(self, t, secs=3.5):
        self._msg = t
        self._mexp = self._now + secs

    def push_undo(self):
        self.undo.append(frozenset(self.cells))
        if len(self.undo) > 40:
            self.undo.pop(0)

    def load_preset(self, key):
        name, body = RLE[key]
        cs = parse_rle(body)
        xs = [p[0] for p in cs]
        ys = [p[1] for p in cs]
        ox = (self.W - (max(xs)-min(xs)+1))//2 - min(xs)
        oy = (self.H - (max(ys)-min(ys)+1))//2 - min(ys)
        cs = parse_rle(body, ox, oy)
        self.push_undo()
        self.cells = cs
        self.heat = {}
        self.gen = 0
        self.camx = (min(xs)+max(xs))/2.0 + ox
        self.camy = (min(ys)+max(ys))/2.0 + oy
        pw = max(1, max(xs)-min(xs)+1)
        ph = max(1, max(ys)-min(ys)+1)
        self.zoom = max(2.0, min(10.0, min(0.72*self.width/pw, 0.72*self.height/ph)))
        self.splash(name + '  ' + str(len(cs)) + ' cells')
        self.playing = True

    def soup(self, density=0.05):
        self.push_undo()
        self.cells = set()
        rnd = random.Random(0)
        for x in range(self.W):
            for y in range(self.H):
                if rnd.random() < density:
                    self.cells.add((x, y))
        self.heat = {}
        self.gen = 0
        self.camx = self.W/2.0
        self.camy = self.H/2.0
        self.zoom = 4.0
        self.splash('random soup  ' + str(len(self.cells)) + ' cells')
        self.playing = True

    def step(self):
        W = self.W
        Hh = self.H
        cells = self.cells
        cnt = {}
        for (x, y) in cells:
            for dx in (-1, 0, 1):
                nx = (x+dx) % W
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    ny = (y+dy) % Hh
                    k = (nx, ny)
                    cnt[k] = cnt.get(k, 0) + 1
        new = set()
        for k, n in cnt.items():
            if n == 3 or (n == 2 and k in cells):
                new.add(k)
        self.cells = new
        heat = self.heat
        for k in new:
            heat[k] = 1.0
        for k in list(heat):
            if k not in new:
                v = heat[k]*0.90
                if v < 0.16:
                    del heat[k]
                else:
                    heat[k] = v
        self.gen += 1

    def update(self, dt):
        self._now = time.time()
        if self._now > self._mexp and self._msg:
            self._msg = ''
        if self.pressed('space'):
            self.playing = not self.playing
            self.splash('paused' if not self.playing else 'playing', 2.0)
        if self.pressed('n'):
            self.playing = False
            self.step()
        if self.pressed(','):
            self.speed = max(1, self.speed-1)
            self.splash('speed ' + str(self.speed), 2.0)
        if self.pressed('.'):
            self.speed = min(8, self.speed+1)
            self.splash('speed ' + str(self.speed), 2.0)
        if self.pressed('x'):
            self.zoom = min(16.0, self.zoom*1.35)
        if self.pressed('z'):
            self.zoom = max(1.0, self.zoom/1.35)
        if self.pressed('t'):
            self.trail = not self.trail
            if not self.trail:
                self.heat = {}
        if self.pressed('g'):
            self.grid = not self.grid
        if self.pressed('b'):
            self.push_undo()
            self.cells = set()
            self.heat = {}
            self.gen = 0
            self.camx = self.W/2.0
            self.camy = self.H/2.0
            self.zoom = 4.0
            self.splash('blank')
        if self.pressed('r'):
            self.soup()
        if self.pressed('u'):
            if self.undo:
                self.cells = set(self.undo.pop())
                self.heat = {}
                self.splash('undo')
            else:
                self.splash('nothing to undo', 2.0)
        if self.pressed('h'):
            self.camx = self.W/2.0
            self.camy = self.H/2.0
            self.zoom = 4.0
            self.splash('home', 1.5)
        for key in RLE:
            if self.pressed(str(key)):
                self.load_preset(key)
        pan = (420.0/self.zoom) * dt
        if self.held('left'):
            self.camx -= pan
        if self.held('right'):
            self.camx += pan
        if self.held('up'):
            self.camy -= pan
        if self.held('down'):
            self.camy += pan
        self.camx = max(0.0, min(float(self.W), self.camx))
        self.camy = max(0.0, min(float(self.H), self.camy))
        if self.playing:
            for _ in range(self.speed):
                self.step()
        pw, ph, btns = self.pointer
        if (btns & 1) and (0 <= pw <= self.width) and (0 <= ph <= self.height):
            wx = int((pw - self.width/2.0)/self.zoom + self.camx)
            wy = int((ph - self.height/2.0)/self.zoom + self.camy)
            if 0 <= wx < self.W and 0 <= wy < self.H:
                if self.clicked(1):
                    if (wx, wy) in self.cells:
                        self.cells.discard((wx, wy))
                    else:
                        self.push_undo()
                        self.cells.add((wx, wy))
                elif self.lmx is not None and abs(wx-self.lmx[0]) <= 3 and abs(wy-self.lmx[1]) <= 3:
                    self.cells.add((wx, wy))
                self.lmx = (wx, wy)
        else:
            self.lmx = None

    def render(self, g):
        g.clear('black')
        zw = self.zoom
        cw, ch = self.width, self.height
        hx = cw/(2.0*zw)
        hy = ch/(2.0*zw)
        x0 = int(self.camx - hx) - 1
        x1 = int(self.camx + hx) + 1
        y0 = int(self.camy - hy) - 1
        y1 = int(self.camy + hy) + 1
        def sx(x):
            return int((x - self.camx)*zw + cw/2)
        def sy(y):
            return int((y - self.camy)*zw + ch/2)
        if self.grid and zw >= 3:
            for x in range(max(0, x0), min(self.W, x1+1)):
                px = sx(x)
                if 0 <= px <= cw:
                    g.line(px, 0, px, ch, color='navy', width=1)
            for y in range(max(0, y0), min(self.H, y1+1)):
                py = sy(y)
                if 0 <= py <= ch:
                    g.line(0, py, cw, py, color='navy', width=1)
        if self.trail and len(self.heat) <= 14000:
            sz = max(1, int(zw))
            for (x, y), h in self.heat.items():
                if x < x0 or x > x1 or y < y0 or y > y1:
                    continue
                px = sx(x)
                py = sy(y)
                if px < -sz or px > cw or py < -sz or py > ch:
                    continue
                if h > 0.82:
                    c = 'lime'
                elif h > 0.62:
                    c = 'green'
                elif h > 0.46:
                    c = 'cyan'
                elif h > 0.33:
                    c = 'sky'
                elif h > 0.24:
                    c = 'gray'
                else:
                    c = 'darkgray'
                g.rect(px, py, sz, sz, color=c)
        sz = max(2, int(zw))
        for (x, y) in self.cells:
            if x < x0 or x > x1 or y < y0 or y > y1:
                continue
            px = sx(x)
            py = sy(y)
            if px < 0 or px > cw-sz or py < 0 or py > ch-sz:
                continue
            g.rect(px, py, sz, sz, color='white')
        g.frame(0, 0, cw, ch, color='navy')
        self._hud(g)

    def _hud(self, g):
        head = 'GEN '+str(self.gen)+'   POP '+str(len(self.cells))+'   WORLD '+str(self.W)+'x'+str(self.H)
        state = 'PAUSED' if not self.playing else 'RUN'
        foot = 'SPD '+str(self.speed)+'x  ZM '+('%.1f'%self.zoom)+'  '+state
        g.text(6, 4, head, color='yellow', size='small')
        g.text(6, self.height-22, foot, color='red' if state=='PAUSED' else 'lime', size='small')
        if self._msg:
            g.text(self.width//2, 16, self._msg, color='white', size='medium', center=True)
        g.text(6, self.height-12, 'space=play n=step b=blank r=soup u=undo t=trail g=grid h=home', color='darkgray', size='small')
        g.text(6, self.height-3, '1-7=presets  ,/. =speed  z/x=zoom  arrows=pan  click/drag=edit', color='darkgray', size='small')

    def game_state(self):
        return {
            'generation': self.gen,
            'population': len(self.cells),
            'zoom': round(self.zoom, 2),
            'speed': self.speed,
            'playing': self.playing,
            'world': [self.W, self.H],
        }
