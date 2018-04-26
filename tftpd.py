import socket
import struct
import os
from utility import send_error_message
from Reader import Reader
from Writer import Writer

HOST = '127.0.0.1'
PORT = 12345

if __name__ == '__main__':
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))

    while True:
        msg, addr = server.recvfrom(4096)

        print(msg)
        op = struct.unpack('>H', msg[:2])[0]
        msg = msg[2:]

        if op != 1 and op != 2:
            send_error_message(0, "Unsupported request type: " + str(op), addr, server)
            continue

        file_name = ""
        mode = ""
        window_size = 1

        for i in range(0, msg.__len__()):
            if msg[i] == 0:
                file_name = msg[:i]
                msg = msg[i+1:]
                break

        for i in range(0, msg.__len__()):
            if msg[i] == 0:
                mode = msg[:i]
                msg = msg[i+1:]
                break

        options = list()
        #process options
        while msg:
            #option name
            name = ""
            for i in range(0, msg.__len__()):
                if msg[i] == 0:
                    name = msg[:i]
                    msg = msg[i + 1:]
                    break
            value = ""
            for i in range(0, msg.__len__()):
                if msg[i] == 0:
                    value = msg[:i]
                    msg = msg[i + 1:]
                    break
            value = int(value)
            options.append((name, value))

            for name, value in options:
                if name == b'windowsize':
                    window_size = min(4, value)
                    if window_size < 1:
                        window_size = 1
                    break


        if mode != b'octet':
            send_error_message(0, "Unsupported mode: " + str(mode) +
                               ". This server supports only octet mode currently.", addr, server)
            continue

        if op == 1:
            Reader(addr, file_name, mode, HOST, window_size).start()
        elif op == 2:
            Writer(addr, file_name, mode, HOST, window_size).start()

