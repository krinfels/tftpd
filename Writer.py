import socket
import threading
import struct

from utility import *


class Writer(threading.Thread):
    def __init__(self, dst, file_name, mode, host, window_size=1):
        super().__init__()
        self.dst = dst
        self.file_name = str(file_name)[2:-1]
        self.mode = mode
        self.host = host
        self.window_size = window_size

        self.conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # set timeout to 2s
        self.conn.settimeout(2)
        self.conn.bind((self.host, 0))

    def run(self):
        try:
            with open(self.file_name, 'wb') as file:
                i = 0
                response = bytes()

                for j in range(0, 5):
                    if self.window_size == 1:
                        send_ack(i, self.dst, self.conn)
                    else:
                        send_oack("windowsize", self.window_size, self.dst, self.conn)

                    k = 0
                    while k < self.window_size:
                        try:
                            response, src = self.conn.recvfrom(516)
                        except socket.timeout:
                            k = k+1
                            if k == self.window_size:
                                print("Timeout")
                                return
                            continue

                        if len(response) < 4:
                            continue

                        op = struct.unpack('>H', response[:2])[0]
                        block_nr = struct.unpack('>H', response[2:4])[0]

                        if op == 5:
                            return
                        elif op != 3 or block_nr != (i+1) % (1 << 16):
                            continue

                        file.write(response[4:])

                        if len(response) < 516:
                            send_ack(1, self.dst, self.conn)
                            return

                        k = k+1
                        i = (i+1) % (1 << 16)

                    if i == self.window_size:
                        break

                while True:
                    for j in range(0, 5):
                        send_ack(i, self.dst, self.conn)

                        k = 0
                        while k < self.window_size:
                            try:
                                response, src = self.conn.recvfrom(516)
                            except socket.timeout:
                                k = k+1
                                if k == self.window_size:
                                    print("Timeout")
                                    return
                                continue

                            if len(response) < 4:
                                continue

                            op = struct.unpack('>H', response[:2])[0]
                            block_nr = struct.unpack('>H', response[2:4])[0]

                            if op == 5:
                                return
                            elif op != 3 or block_nr != (i + 1) % (1 << 16):
                                continue

                            file.write(response[4:])
                            k = k + 1
                            i = (i+1) % (1 << 16)

                            if len(response) < 516:
                                print("DONE")
                                send_ack(i, self.dst, self.conn)
                                return

        except FileNotFoundError:
            send_error_message(1, "File: " + self.file_name + " does not exist", self.dst, self.conn)
            return
        except PermissionError:
            send_error_message(2, "Permission denied for file: " + self.file_name, self.dst, self.conn)
            return
