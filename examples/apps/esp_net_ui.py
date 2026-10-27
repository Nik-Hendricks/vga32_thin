import importlib.util

PATH = "/root/.vga32/apps/esp_net_manager.py"
spec = importlib.util.spec_from_file_location("esp_net_manager", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
globals().update({name: value for name, value in vars(module).items() if not name.startswith("__")})

# the host registry only registers classes whose __module__ is this plugin module
for _name, value in list(globals().items()):
    if isinstance(value, type):
        value.__module__ = __name__
