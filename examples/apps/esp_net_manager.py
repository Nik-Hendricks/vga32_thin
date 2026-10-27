from vga32.widgets import UIApp

class EspNetworkManager(UIApp):
    app_id = 'esp.network.manager'
    title = 'ESP Net Manager'
    icon = 'panel'
    category = 'Utilities'
    size = (620, 390)
    fps = 3

exec(open('/root/.vga32/apps/esp_net_manager_backup.py').read(), globals())
