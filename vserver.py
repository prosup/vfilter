#!/usr/bin/env python3
import sqlite3
#import csv
import os.path
import os
import base64
import socket
from concurrent.futures import ThreadPoolExecutor,as_completed
import uuid
from pathlib import Path

class SERVER:
    TMP_DIR = "tmp"

    def __init__(self, raw ,db_manager):
        self.db_manager = db_manager
        self.dpath = Path(os.getcwd()) / self.TMP_DIR
        self.dpath.mkdir(parents=True, exist_ok=True)
        self.fpath = os.path.join(self.dpath, f"{uuid.uuid4()}.ovpn")
        self.raw = raw
        self.config = None



    def rawData(self):
        return self.raw

    def solvConfig(self):
        try:
            self.configdata = base64.b64decode(self.raw)

            with open(self.fpath, "wb+") as cfile:
                cfile.write(self.configdata)
        except Exception as e:
            print(e)  # Assuming logfd is defined somewhere

        self.solvePort()
        self.solveAddr()
        self.solveProtocol()

        # Build the final configuration file path using addr
        self.config = self.dpath / f"{self.addr}.ovpn"

        # Rename the temporary file to the final configuration file
        os.rename(self.fpath, self.config)
    
    def solveProtocol(self):
        try:
            with open(self.fpath, 'r') as config_file:
                for line in config_file:
                    if line.startswith('proto'):
                        self.protocol = line.split()[1].strip()
                        return
        except Exception as e:
            print(f"Error while solving protocol: {e}\n")

        # If 'proto' line is not found or any exception occurs, set protocol to None
        self.protocol = None

    def solvePort(self):
        try:
            with open(self.fpath, 'r',encoding="utf-8") as config_file:
                for line in config_file:
                    if line.startswith('remote'):
                        parts = line.split()
                        if len(parts) >= 3:
                            self.port = parts[2].strip()
                            return
        except Exception as e:
            print(f"Error while solving port: {e}\n")

        # If 'remote' line or the port information is not found, set port to None
        self.port = None

    def solveAddr(self):
        try:
            with open(self.fpath, 'r') as config_file:
                for line in config_file:
                    if line.startswith('remote'):
                        parts = line.split()
                        if len(parts) >= 2:
                            self.addr = parts[1].strip()
                            return
        except Exception as e:
            print(f"Error while solving address: {e}\n")

        # If 'remote' line or the address information is not found, set addr to None
        self.addr = None
    
    def validate(self):
        try:
            socket_type = socket.SOCK_STREAM if self.protocol.lower() == "tcp" else socket.SOCK_DGRAM
            address = (self.addr, int(self.port))

            with socket.create_connection(address, timeout=3) as sk:
                print(f"Connection successful: {self.addr}:{self.port}")
                return 0

        except socket.error as e:
            print(f"Connection failed: {self.addr}:{self.port}, Error: {e}")
            return -1
        except Exception as e:
            print(f"Error during validation: {e}")
            return -1
