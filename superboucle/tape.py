import u3
import time
from math import pi

from pyudev import Context, Monitor, MonitorObserver

VENDOR_ID = '0cd5'
PRODUCT_ID = '0003'
GEAR_DIAMETER = 4.5
TAPE_SIZE = 82

class HardwareTapeLoop():

    def __init__(self, midi_transport) -> None:
        self.device_path = None
        self.d = None
        self.midi_transport = midi_transport

        context = Context()

        # Check if device is already plugged in
        for device in context.list_devices(subsystem='usb'):
            self.processNewDevice(device)

        monitor = Monitor.from_netlink(context)
        monitor.filter_by('usb')
        observer = MonitorObserver(monitor, self.event_callback)
        observer.start()

    def device_match(self, device):
        return device.get('ID_VENDOR_ID') == VENDOR_ID and device.get('ID_MODEL_ID') == PRODUCT_ID

    def processNewDevice(self, device):
        if self.device_match(device):
            self.device_path = device.sys_path
            self.onConnect(device)

    def event_callback(self, action, device):
        print(action)
        if 'usb' in device.subsystem:
            if action == 'add':
                self.processNewDevice(device)
            elif action == 'remove':
                if device.sys_path == self.device_path:
                    self.onDisconnect(device)

    def onConnect(self, device):
        print(f"Device connected: {device.device_node}")
        print(f"Device details: {device}")
        self.d = u3.U3()
        self.d.debug = True
        # Setup quadrature mode on FIO4/5
        print(self.d.configIO(NumberOfTimersEnabled=2, TimerCounterPinOffset=4))
        self.d.getFeedback(u3.Timer0Config(8), u3.Timer1Config(8))


    def onDisconnect(self, device):
        print(f"Device disconnected: {device.device_node}")
        print(f"Device details: {device}")
        self.d = None
    
    def getAbsolutePositionIncm(self):
        try:
            if self.d is not None:
                response = self.d.getFeedback(u3.QuadratureInputTimer())
                position = response[0]
                position *= ((pi * GEAR_DIAMETER) / 4000)
                return position
            else:
                raise NoDeviceConnected()
        except u3.LabJackException:
            raise NoDeviceConnected()
    
    def getTapeSizeIncm(self):
        return TAPE_SIZE

    def getRelativePositionIncm(self):
        return self.getAbsolutePositionIncm() % self.getTapeSizeIncm()

class NoDeviceConnected(Exception):
    pass