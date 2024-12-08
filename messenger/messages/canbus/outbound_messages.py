from ..message import OutboundMessage
from ...utils import bit_write

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from railway.io_port import IOPort, I2CPin
    from railway.turnout import Turnout


class RequestInputsMessage(OutboundMessage):
    def __init__(self, input_port: "IOPort"):
        super().__init__(12)
        self.input_port = input_port

    def encode(self) -> list[int]:
        data = [self.input_port.module_id + self.input_port.interface_type << 4,
                self.input_port.address]
        return data


class DistributeTargetTurnoutPositionsMessage(OutboundMessage):
    def __init__(self, turnouts: list["Turnout"]):
        super().__init__(1)
        self.turnouts = turnouts

    def encode(self) -> list[int]:
        turnout_positions = [(s.servo_module, s.servo_number, s.target_pos) for s in self.turnouts]
        data = [0] * (max(p[0] for p in turnout_positions) + 1)  # get list-size (=count of servo modules)
        for module, s_number, pos in turnout_positions:
            data[module] += (pos << s_number)
        return data


class DistributeTurnoutIOReference(OutboundMessage):
    def __init__(self, requested_turnout: int, pin: "I2CPin", cohesive_turnout_state: bool):
        super().__init__(2)
        self.requested_turnout = requested_turnout
        self.pin = pin
        self.cohesive_turnout_position = cohesive_turnout_state

    def encode(self) -> list[int]:
        data = [self.pin.module_id + self.pin.interface_type << 4,
                self.pin.address,
                self.pin.pin_no,
                self.cohesive_turnout_position + (self.requested_turnout << 1)]
        return data


class WriteI2CPortMessage(OutboundMessage):
    i2c_value_storage: {int: {int: int}} = {}

    def __init__(self, output_pin: "I2CPin", output_value: bool):
        super().__init__(10)
        self.output_port = output_pin
        self.output_value = output_value

    def encode(self) -> list[int]:
        module_id = self.output_port.module_id
        output_type = self.output_port.interface_type
        output_address = self.output_port.address

        # check if module_id already exists
        if module_id not in WriteI2CPortMessage.i2c_value_storage:
            WriteI2CPortMessage.i2c_value_storage[module_id] = {}
        # get current output value
        old_value = WriteI2CPortMessage.i2c_value_storage.get(module_id, {}).get(output_address, 0)
        new_value = bit_write(old_value,
                              self.output_port.pin_no,
                              self.output_value)
        # write new value to storage
        WriteI2CPortMessage.i2c_value_storage[module_id].update({output_address: new_value})

        data = [module_id + output_type << 4, output_address, new_value]
        return data
