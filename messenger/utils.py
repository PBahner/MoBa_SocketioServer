def bit_write(byte: int, position: int, value: bool) -> int:
    if value:
        # Set the bit at the specified position
        return byte | (1 << position)
    else:
        # Clear the bit at the specified position
        return byte & ~(1 << position)


def bools_to_bytes(data_list: [int]) -> [int]:
    data_list = [b == 1 for b in data_list]
    output_byte = [0]
    byte_number = 0
    for i, x in enumerate(data_list):
        exponent = ((i+1) % 8)-1
        output_byte[byte_number] += int(x * 2**exponent)
        if (i+1) % 8 == 0:
            output_byte.append(0)
            byte_number += 1
    return output_byte
