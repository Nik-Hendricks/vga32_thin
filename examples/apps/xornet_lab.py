import time
import numpy as np
from vga32.game import GameApp

W, H = 512, 320
HID = 6
GRIDX, GRIDY = 88, 55
NAMES = {1: "two blobs", 2: "xor", 3: "circle", 4: "ring", 5: "spiral"}


def forward(net, z):
    W1, b1, W2, b2 = net
    h = np.tanh(z @ W1 + b1)
    raw = h @ W2 + b2
    out = 1.0 / (1.0 + np.exp(-raw))
    return np.clip(out, 1e-7, 1.0 - 1e-7).ravel(), h


class NetApp(GameApp):
    app_id = "data.xornet"
    title = "NN Trainer"
    icon = "gear"
    category = "Data"
    width, height = 620, 340
    fps = 60

    def start(self):
        self.lr = 0.3
        self.epochs = 0
        self.speed = 2
        self.playing = True
        self.loss = None
        self.best_acc = 0.0
        self.camx, self.camy = W / 2.0, H / 2.0
        self.zoom = 1.0
        self._now = time.time()
        self._msg = ""
        self._mexp = 1e9
        self._load(2)
        self.splash("2-6-1 net training live on the boundary", 6.0)

    def splash(self, t, secs=3.5):
        self._msg = t
        self._mexp = self._now + secs

    def _load(self, key):
        r = np.random.default_rng(500 + key)
        if key == 1:
            p1 = r.uniform(-1.0, 0.0, (400, 2))
            p2 = r.uniform(0.0, 1.0, (400, 2))
            z = np.vstack([p1, p2])
            y = np.concatenate([np.zeros(400), np.ones(400)])
        elif key == 2:
            z = r.uniform(-1.0, 1.0, (900, 2))
            y = (z[:, 0] * z[:, 1] > 0).astype(float)
        elif key == 3:
            z = r.uniform(-1.0, 1.0, (900, 2))
            y = (np.hypot(z[:, 0], z[:, 1]) < 0.55).astype(float)
        elif key == 4:
            z = r.uniform(-1.0, 1.0, (900, 2))
            rad = np.hypot(z[:, 0], z[:, 1])
            y = ((rad > 0.42) & (rad < 0.78)).astype(float)
        else:
            t = np.linspace(0.0, 1.0, 420)
            a1 = t * 4.0 * np.pi + r.normal(0, 0.09, 420)
            p1 = np.stack([np.cos(a1), np.sin(a1)], 1) * (0.18 + 0.82 * t)
            p2 = -p1 + r.normal(0, 0.06, p1.shape)
            z = np.vstack([p1, p2])
            y = np.concatenate([np.zeros(420), np.ones(420)])
        self.z = z
        self.y = y
        self.prob = key
        r2 = np.random.default_rng(600 + key)
        self.net = [r2.normal(0, 0.5, (2, HID)), r2.normal(0, 0.1, HID),
                    r2.normal(0, 0.5, (HID, 1)), r2.normal(0, 0.1, 1)]
        self.epochs = 0
        self.best_acc = 0.0
        self.loss = None
        self.splash(NAMES[key] + "  " + str(len(z)) + " samples", 3.0)

    def _reinit(self):
        r = np.random.default_rng(int(time.time()) % 100000)
        self.net = [r.normal(0, 0.5, (2, HID)), r.normal(0, 0.1, HID),
                    r.normal(0, 0.5, (HID, 1)), r.normal(0, 0.1, 1)]
        self.epochs = 0
        self.best_acc = 0.0
        self.loss = None
        self.splash("weights reinit", 2.5)

    def _predict(self, z=None):
        z = self.z if z is None else z
        return forward(self.net, z)[0]

    def _train(self, n_epochs):
        z = self.z
        y = self.y
        m = len(z)
        for _ in range(n_epochs):
            W1, b1, W2, b2 = self.net
            h = np.tanh(z @ W1 + b1)
            out = np.clip(1.0 / (1.0 + np.exp(-(h @ W2 + b2))), 1e-7, 1.0 - 1e-7).ravel()
            dz2 = (out - y)[:, None]
            dW2 = (h.T @ dz2) / m
            db2 = dz2.mean(0)
            dh = dz2 @ W2.T * (1.0 - h * h)
            dW1 = (z.T @ dh) / m
            db1 = dh.mean(0)
            self.net = [W1 - self.lr * dW1, b1 - self.lr * db1,
                        W2 - self.lr * dW2, b2 - self.lr * db2]
            self.epochs += 1
        out = self._predict()
        pred = (out > 0.5).astype(float)
        acc = float((pred == y).mean())
        if acc > self.best_acc:
            self.best_acc = acc
            if acc >= 0.97 and self.epochs > 250:
                self.splash("converged  acc " + ("%.1f" % (acc * 100)) + "%", 5.0)
        self.loss = float(-(y * np.log(out) + (1.0 - y) * np.log(1.0 - out)).mean())

    def update(self, dt):
        self._now = time.time()
        if self._now > self._mexp and self._msg:
            self._msg = ""
        if self.pressed("space"):
            self.playing = not self.playing
            self.splash("paused" if not self.playing else "running", 2.0)
        if self.pressed("n"):
            self.playing = False
            self._train(1)
        if self.pressed(","):
            self.speed = max(1, self.speed - 1)
            self.splash("epochs/frame " + str(self.speed), 2.0)
        if self.pressed("."):
            self.speed = min(12, self.speed + 1)
            self.splash("epochs/frame " + str(self.speed), 2.0)
        for key in (1, 2, 3, 4, 5):
            if self.pressed(str(key)):
                self._load(key)
        if self.pressed("w"):
            self._reinit()
        if self.pressed("h"):
            self.camx, self.camy = W / 2.0, H / 2.0
            self.zoom = 1.0
            self.splash("home", 1.5)
        if self.pressed("x"):
            self.zoom = min(16.0, self.zoom * 1.35)
        if self.pressed("z"):
            self.zoom = max(0.5, self.zoom / 1.35)
        pan = (420.0 / self.zoom) * dt
        if self.held("left"):
            self.camx -= pan
        if self.held("right"):
            self.camx += pan
        if self.held("up"):
            self.camy -= pan
        if self.held("down"):
            self.camy += pan
        self.camx = max(0.0, min(float(W), self.camx))
        self.camy = max(0.0, min(float(H), self.camy))
        if self.playing:
            self._train(self.speed)

    def render(self, g):
        g.clear("black")
        zw = self.zoom
        cw, ch = self.width, self.height
        xs = (np.linspace(-1.0, 1.0, GRIDX + 1) + 1.0) * W / 2.0
        ys = (1.0 - np.linspace(-1.0, 1.0, GRIDY + 1)) * H / 2.0
        hx = cw / (2.0 * zw)
        hy = ch / (2.0 * zw)
        nx0 = max(0, int(((self.camx - hx) / W) * GRIDX))
        nx1 = min(GRIDX - 1, int(((self.camx + hx) / W) * GRIDX))
        ny0 = max(0, int(((self.camy - hy) / H) * GRIDY))
        ny1 = min(GRIDY - 1, int(((self.camy + hy) / H) * GRIDY))
        if nx0 <= nx1 and ny0 <= ny1:
            cxw = [(xs[i] + xs[i + 1]) / 2.0 for i in range(nx0, nx1 + 1)]
            cyw = [(ys[j] + ys[j + 1]) / 2.0 for j in range(ny0, ny1 + 1)]
            gx = np.array([2.0 * u / W - 1.0 for u in cxw])
            gy = np.array([1.0 - 2.0 * u / H for u in cyw])
            GX, GY = np.meshgrid(gx, gy)
            fz = np.stack([GX.ravel(), GY.ravel()], 1)
            out = forward(self.net, fz)[0].reshape(GX.shape)
            for j in range(ny0, ny1 + 1):
                rowc = out[j - ny0]
                for i in range(nx0, nx1 + 1):
                    v = rowc[i - nx0]
                    if v >= 0.53:
                        c = "blue"
                    elif v >= 0.47:
                        c = "lime"
                    else:
                        continue
                    x = int((xs[i] - self.camx) * zw + cw / 2)
                    y = int((ys[j] - self.camy) * zw + ch / 2)
                    g.rect(x, y, int((xs[i + 1] - xs[i]) * zw) + 1,
                           int((ys[j] - ys[j + 1]) * zw) + 1, color=c)
        stride = 8 if zw < 1.2 else (4 if zw < 2.5 else 2)
        z = self.z
        y = self.y
        for i in range(0, len(z), stride):
            wx = (z[i, 0] + 1.0) * W / 2.0
            wy = (1.0 - z[i, 1]) * H / 2.0
            px = int((wx - self.camx) * zw + cw / 2)
            py = int((wy - self.camy) * zw + ch / 2)
            if px < -2 or px > cw + 2 or py < -2 or py > ch + 2:
                continue
            g.rect(px, py, 2, 2, color="cyan" if y[i] > 0.5 else "red")
        g.frame(0, 0, cw, ch, color="navy")
        loss_txt = "  LOSS " + ("%.3f" % self.loss) if self.loss else ""
        g.text(6, 4, "EPOCHS " + str(self.epochs) + "  ACC " + ("%.1f" % (self.best_acc * 100)) + "%" + loss_txt,
               color="yellow", size="small")
        state = "TRAIN" if self.playing else "PAUSED"
        g.text(6, self.height - 22, state + "  " + NAMES.get(self.prob, "?") + "  ZM " + ("%.1f" % self.zoom),
               color="lime" if state == "TRAIN" else "red", size="small")
        if self._msg:
            g.text(self.width // 2, 16, self._msg, color="white", size="medium", center=True)
        g.text(6, self.height - 12, "space=pause n=1 epoch ,/.=speed w=reinit h=home x/z=zoom arrows=pan", color="darkgray", size="small")
        g.text(6, self.height - 3, "1-5=problems  lime=decision boundary  cyan=class 1  red=class 0", color="darkgray", size="small")

    def game_state(self):
        return {
            "epochs": self.epochs,
            "acc": round(self.best_acc, 3),
            "loss": round(self.loss, 4) if self.loss else None,
        }
