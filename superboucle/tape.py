from pyudev import Context, Monitor, MonitorObserver
from superboucle import client, gui, app

VENDOR_ID = '0cd5'
PRODUCT_ID = '0003'

class HardwareTapeLoop():

    def __init__(self) -> None:
        self.device_path = None

        context = Context()

        # Check if device is already plugged in
        for device in context.list_devices(subsystem='usb'):
            print(device)
        monitor = Monitor.from_netlink(context)
        monitor.filter_by('usb')
        observer = MonitorObserver(monitor, self.event_callback)
        observer.start()

    def event_callback(self, action, device):
        print(action)
        if 'usb' in device.subsystem:
            if action == 'add':
                if device.get('ID_VENDOR_ID') == VENDOR_ID and device.get('ID_MODEL_ID') == PRODUCT_ID:
                    self.device_path = device.sys_path
                    print(f"Device connected: {device.device_node}")
                    print(f"Device details: {device}")
            elif action == 'remove':
                if device.sys_path == self.device_path:
                    print(f"Device disconnected: {device.device_node}")
                    print(f"Device details: {device}")