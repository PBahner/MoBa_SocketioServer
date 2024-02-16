from railway.io_port import I2CPort
from railway.turnout import Turnout


class TrackInterruption:
    def __init__(self,
                 global_number: int,
                 section: int,
                 output_reference: I2CPort,
                 required_turnout: Turnout = None,
                 required_turnout_pos: str = None):
        self.global_number = global_number
        self.section = section
        self.output_reference = output_reference
        self.required_turnout = required_turnout
        self.required_turnout_pos = required_turnout_pos
