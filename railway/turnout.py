from .io_port import I2CPin


class Turnout:
    __pos: {int: str} = {
        "+": False,
        "-": True,
        "": 2,
    }

    def __init__(self, turnout_id: int,
                 servo_module: int,
                 servo_number: int,
                 input_reference_plus: I2CPin = None,
                 input_reference_minus: I2CPin = None):
        self.__input_pin_minus = None
        self.__input_pin_plus = None
        self.__locked = 0
        self.current_pos = self.__pos[""]
        self.target_pos = self.__pos[""]
        self.id = turnout_id
        self.servo_module = servo_module
        self.servo_number = servo_number
        self.input_reference_plus = input_reference_plus
        self.input_reference_minus = input_reference_minus

    def set_input_pin_minus(self, input_pin_minus: int):
        self.__input_pin_minus = input_pin_minus
        self.__update_current_pos()

    def set_input_pin_plus(self, input_pin_plus: int):
        self.__input_pin_plus = input_pin_plus
        self.__update_current_pos()

    def __update_current_pos(self):
        if self.__input_pin_minus == True and self.__input_pin_plus == False:
            self.current_pos = self.__pos["-"]
        elif self.__input_pin_minus == False and self.__input_pin_plus == True:
            self.current_pos = self.__pos["+"]
        else:
            self.current_pos = self.__pos[""]

        # set target pos as soon current pos is fetched
        if self.target_pos == self.__pos[""]:
            self.target_pos = self.current_pos

    def change_target_pos(self):
        if not self.__locked:
            self.target_pos = not self.current_pos

    def get_current_pos_friendly(self) -> str:
        return next((key for key, value in self.__pos.items() if value == self.current_pos), None)

    def lock(self):
        self.__locked += 1

    def unlock(self):
        self.__locked -= 1 if self.__locked else 0
