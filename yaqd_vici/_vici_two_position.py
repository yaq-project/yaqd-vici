__all__ = ["ViciTwoPosition"]

import asyncio
from typing import Dict, Any, List

from yaqd_core import aserial, logging
from yaqd_core import UsesUart, UsesSerial, IsDiscrete, HasPosition, IsDaemon


class ViciTwoPosition(UsesUart, UsesSerial, IsDiscrete, HasPosition, IsDaemon):
    _kind = "vici-two-position"
    _serial_objects: Dict[str, aserial.ASerial] = dict()

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        if self._config["serial_port"] in ViciTwoPosition._serial_objects:
            self._serial = ViciTwoPosition._serial_objects[self._config["serial_port"]]
        else:
            self._serial = aserial.ASerial()
            self._serial.port = self._config["serial_port"]
            self._serial.baudrate = self._config["baud_rate"]
            self._serial.eol = b"\r"
            self._serial.open()
            ViciTwoPosition._serial_objects[self._config["serial_port"]] = self._serial

    def close(self):
        self._serial.close()

    def direct_serial_write(self, message):
        self._serial.write(message)

    def _set_position(self, position):
        to_write = ""
        # device_id
        if self._config["device_id"] is not None:
            to_write += str(self._config["device_id"])
        # position
        if position > 0.5:
            to_write += "CC"  # position B
        else:
            to_write += "CW"  # position A
        # finish
        self._serial.write((to_write + "\r").encode())
        self._serial.flush()

    async def update_state(self):
        while True:
            if self._config["device_id"] is not None:
                message = f"{self._config['device_id']}CP"
            else:
                message = "CP"
            message += "\r"
            message = message.encode()
            response = await self._serial.awrite_then_readline(message)
            print(message, response)
            try:
                response = response.decode()
            except UnicodeDecodeError:
                continue
            if "A" in response:
                self._state["position_identifier"] = "A"
                self._state["position"] = 0
            elif "B" in response:
                self._state["position_identifier"] = "B"
                self._state["position"] = 1
            else:
                self._state["position_identifier"] = None
                self._state["position"] = float("nan")
            if self._state["position"] == self._state["destination"]:
                self._busy = False
            await asyncio.sleep(0.025)
