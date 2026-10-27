
from vga32.ui import App
class CalcService(App):
    app_id = "tools.calc"
    title = "Calc Service"
    icon = "star"
    category = "Tools"
    size = (220, 120)
    def __init__(self, desk, **kw):
        super().__init__(desk, **kw)
        self.value = 0
    def service_add(self, a=0, b=0):
        self.value = int(a) + int(b)
        return self.value
    def state(self):
        return {"value": self.value}
    def draw(self, d, x, y, w, h):
        d.rectangle([x,y,x+w-1,y+h-1], fill=(10,10,20))
        d.text((x+6,y+6), f"Calc service value={self.value}", fill=(180,255,180))
