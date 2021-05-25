#!/usr/bin/env python3

import subprocess
import socket
import os
import time

HOST = '10.229.84.88'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)
BUFF_SIZE = 8192
TIMEOUT = 10        # Close connection if no data in TIMEOUT second

OUTPUT_LINE = b'\n====== OUTPUT ======\n'
RETURN_CODE_LINE = b'\n====== RETURN_CODE ======\n'
EOP = b'\n====== This is the end of the packet ======\n'

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    while True:
        print('# Wait for a new incomming connection...')
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            conn.setblocking(False)
            #time.sleep(1)
            begin_time = time.time()
            while True:
                # timeout
                if time.time() - begin_time > TIMEOUT:
                    print('# No data received in {} seconds. Close this connection...'.format(TIMEOUT))
                    break

                try:
                    data = conn.recv(BUFF_SIZE)
                except BlockingIOError:
                    continue

                # client close the connection
                if not data:
                    print('# Client colsed the connection. Exit...')
                    break

                # run command
                cmd = data.decode("utf-8")
                print('# Run command - {}'.format(cmd))

                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                o, e = process.communicate()
                return_code = process.returncode

                print('# o:\n' + o.decode('utf-8'))
                print('# return_code:\n' + str(return_code))

                # send the output back to client
                return_code = str(return_code).encode()
                data = OUTPUT_LINE + o + RETURN_CODE_LINE + return_code + EOP
                conn.sendall(data)

                begin_time = time.time()
                time.sleep(0.1)

        print(conn, addr)
