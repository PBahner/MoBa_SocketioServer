class IOPort:  # contains all required information/addresses to access an PCF8574 input or output
    def __init__(self,
                 module_id: int,
                 interface_type: int,
                 address: int):
        self.module_id = module_id
        self.interface_type = interface_type
        self.address = address

    def compare(self, module_id, interface_type, address):
        return (module_id == self.module_id and
                interface_type == self.interface_type and
                address == self.address)


class I2CPin(IOPort):  # contains all required information/addresses to access an PCF8574 input or output
    def __init__(self,
                 module_id: int,
                 interface_type: int,
                 address: int,
                 pin_no: int):
        super().__init__(module_id, interface_type, address)
        self.pin_no = pin_no
