def send_error_message(code, message, addr, sock):
    sock.sendto(b'\x00\x05' + code.to_bytes(2, 'big') + bytes(message, 'utf8') + b'\x00', addr)


def send_ack(block_nr, addr, sock):
    sock.sendto(b'\x00\x04' + block_nr.to_bytes(2, 'big') + b'\x00', addr)


def send_oack(option_name, value, addr, sock):
    sock.sendto(b'\x00\x06' + bytes(option_name, 'utf8') + b'\x00' + bytes(str(value), 'utf8') + b'\x00', addr)


def send_data(block_nr, data, addr, sock):
    sock.sendto(b'\x00\x03' + block_nr.to_bytes(2, 'big') + data, addr)
