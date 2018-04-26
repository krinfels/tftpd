import socket
import threading
import struct

from utility import *


class Reader(threading.Thread):
    def __init__(self, dst, file_name, mode, host, window_size=1):
        super().__init__()
        self.dst = dst
        self.host = host
        self.file_name = str(file_name)[2:-1]
        self.mode = mode[2:-1]
        self.window_size = window_size

        self.conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # set timeout to 2s
        self.conn.settimeout(2)
        self.conn.bind((self.host, 0))

    def run(self):
        try:
            with open(self.file_name, 'rb') as file:
                done = False
                if self.window_size == 1:
                    data = file.read(512)
                    i = 1
                else:
                    data = bytes()
                    i = 0

                j = 0
                while j < 5:
                    if self.window_size == 1:
                        send_data(i, data, self.dst, self.conn)
                    else:
                        send_oack("windowsize", self.window_size, self.dst, self.conn)

                    try:
                        response, src = self.conn.recvfrom(4096)
                    except socket.timeout:
                        j = j+1
                        if j == 5:
                            return
                        continue

                    if len(response) < 4:
                        continue

                    op = struct.unpack('>H', response[:2])[0]
                    block_nr = struct.unpack('>H', response[2:4])[0]

                    if op == 5:
                        return
                    if op != 4:
                        continue

                    if block_nr == i:
                        break

                # Read data from file to buffer
                buffer = list()
                for k in range(0, self.window_size):
                    buffer.append((i+k+1, file.read(512)))
                    if len(buffer[len(buffer)-1][1]) < 512:
                        done = True
                        break

                while True:
                    j = 0
                    while j < 5:
                        for data in buffer:
                            send_data(data[0], data[1], self.dst, self.conn)

                        while True:
                            try:
                                response, src = self.conn.recvfrom(4096)
                            except socket.timeout:
                                j = j+1
                                if j == 5:
                                    print("Timeout")
                                    return
                                break

                            if len(response) < 4:
                                continue

                            op = struct.unpack('>H', response[:2])[0]
                            block_nr = struct.unpack('>H', response[2:4])[0]

                            if op != 4 or (block_nr < i and i - block_nr <= 2*self.window_size):
                                print("WTF")
                                continue

                            if block_nr < i:
                                amount = (1 << 16) - i + block_nr + 1
                            else:
                                amount = block_nr - i + 1

                            i = (block_nr+1) % (1 << 16)

                            buffer = buffer[amount:]

                            if done and not buffer:
                                print("DONE")
                                return

                            if not done:
                                for k in range(0, self.window_size - len(buffer)):
                                    buffer.append(((i+k) % (1 << 16), file.read(512)))
                                    if len(buffer[len(buffer)-1][1]) < 512:
                                        done = True
                                        break
                            break

        except FileNotFoundError:
            send_error_message(1, "File: " + self.file_name + " does not exist", self.dst, self.conn)
            return
        except PermissionError:
            send_error_message(2, "Permission denied for file: " + self.file_name, self.dst, self.conn)
            return
