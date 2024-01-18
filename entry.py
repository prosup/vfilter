#!/usr/bin/env python3

import subprocess
import argparse
from dbapi import DatabaseManager
from servermng import ServerManager
from hostmng import RemoteHostManager

def main():
    dbm=DatabaseManager("vdb.db")
    server_mng=ServerManager(dbm)
    parser = argparse.ArgumentParser()
    parser.add_argument("--srchost", type=str, help="Input the source host.",default="109.111.243.206:17579")
    args = parser.parse_args()
    #TODO:upstream server should be input as args
    server_mng.update_database(args.srchost)
    server_mng.itor()
     
#    sdb.delServer("1")
#    sdb.removeDup()

if __name__ == '__main__': 
    main()
