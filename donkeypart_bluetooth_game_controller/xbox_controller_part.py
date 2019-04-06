import argparse
import evdev
from evdev import ecodes
from itertools import cycle
import os
import time
from .part import BluetoothDevice

THROTTLE_MAX = 1023  # 0-1023
ANGLE_MAX = 65536
HALF_ANGLE_MAX = ANGLE_MAX // 2 # 0 - 65535


class XboxGameController(BluetoothDevice):

    def __init__(self, device=None, device_search_term=None, verbose=False):

        self.verbose = verbose
        self.running = False

        self.angle = 0.0
        self.throttle = 0.0

        self.drive_mode_toggle = cycle(['user', 'local_angle', 'local'])
        self.drive_mode = next(self.drive_mode_toggle)

        self.recording_toggle = cycle([False, True])
        self.recording = next(self.recording_toggle)
        if device is not None:
            self.device = device
        else:
            self.device_search_term = device_search_term
            self.load_device(device_search_term)

    def update_state(self, event):
        if event.code == evdev.ecodes.ABS_GAS:
            # Gas
            self.update_throttle(event)
        elif event.code == evdev.ecodes.BTN_A:
            # A
            self.toggle_recording(event)
        elif event.code == evdev.ecodes.BTN_B:
            # B
            self.toggle_drive_mode(event)
        elif event.code == evdev.ecodes.ABS_X:
            # Axis X
            self.update_angle(event)
        elif event.code == evdev.ecodes.BTN_TR:
            # TR
            pass
        elif event.code == evdev.ecodes.BTN_TL:
            # TL
            pass

        if self.verbose == True:
            print('Angle (%s), Throttle (%s), Drive Mode (%s), Recording (%s)' % (
                self.angle, self.throttle, self.drive_mode, self.recording))

    def run(self):
        try:
            self.running = True
            # Event loop
            for event in self.device.read_loop():
                if event.type == ecodes.EV_ABS or event.type == ecodes.EV_KEY:
                    self.update_state(event)
                    if not self.running:
                        print('Exiting.')
                        break
        except OSError as error:
            print('OSError: Likely lost connection with controller. Trying to reconnect now. Error: {}'.format(e))
            time.sleep(0.1)
            if self.device_search_term is not None:
                self.load_device(self.device_search_term)
                if self.device is not None:
                    self.run()

    def update(self):
        self.run()

    def run_threaded(self, img_arr=None):
        return self.angle, self.throttle, self.drive_mode, self.recording

    def shutdown(self):
        self.running = False
        time.sleep(0.1)

    def update_angle(self, event):
        value = self.clamp(event.value, 0, ANGLE_MAX)
        value -= HALF_ANGLE_MAX
        self.angle = value / HALF_ANGLE_MAX

    def update_throttle(self, event):
        value = self.clamp(event.value, 0, THROTTLE_MAX)
        self.throttle = value / THROTTLE_MAX

    def toggle_recording(self, event):
        if event.value == 1:
            self.recording = next(self.recording_toggle)

    def toggle_drive_mode(self, event):
        if event.value == 1:
            self.drive_mode = next(self.drive_mode_toggle)

    def clamp(self, val, min_value, max_value):
        return max(min(val, max_value), min_value)


if __name__ == "__main__":
    # python -m evdev.evtest
    controller = XboxGameController(device_search_term='xbox', verbose=True)
    controller.run()
