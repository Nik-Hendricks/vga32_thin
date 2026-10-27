"""Every native widget in one window; switch themes to see them restyle.
Copy into ~/.vga32/apps/ or install with install_app."""
from vga32.widgets import (Button, Checkbox, Column, Dropdown, Group, Label, ListBox, ProgressBar, Radio, Row,
                           Slider, TextField, UIApp)


class WidgetGallery(UIApp):
    app_id = "demo.widgets"
    title = "Widget Gallery"
    icon = "panel"
    category = "Demos"
    size = (420, 330)

    def build(self):
        return Column([
            Label("Native widgets", size="medium"),
            Row([TextField(id="name", placeholder="Your name", flex=1),
                 Dropdown(["Classic", "Platinum", "Aqua"], "Aqua", id="theme")]),
            Row([Group("Options", Column([Checkbox("Sound", True, id="sound"), Checkbox("Music", id="music")],
                                         gap=4, padding=2), flex=1),
                 Group("Speed", Radio(["Slow", "Normal", "Fast"], "Normal", id="speed"), flex=1)]),
            Slider(0, 100, 40, label="Volume", id="volume"),
            ProgressBar(40, id="progress"),
            Row([ListBox(["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot"], "Bravo", rows=3, id="list",
                         flex=1),
                 Column([Button("Apply", id="apply", default=True), Button("Reset", id="reset")], gap=6,
                        padding=0)]),
        ], gap=8)

    def on_change(self, w):
        if w.id == "volume":
            self.find("progress").value = w.value
        elif w.id == "theme":
            self.desk.set_theme(w.value.lower())

    def on_click(self, w):
        if w.id == "apply":
            self.desk.notify(f"Hello {self.find('name').value or 'there'}: {self.values()}")
        elif w.id == "reset":
            self.rebuild(keep_values=False)
