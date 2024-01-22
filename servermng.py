#!/usr/bin/env python3
from dbapi import DatabaseManager
from vserver import SERVER
from concurrent.futures import ThreadPoolExecutor,as_completed
import os
import requests

class ServerManager:
    def __init__(self, db_manager: DatabaseManager):
        self.create_table='''CREATE TABLE server(
        HostName,IP,
        Score,Ping,Speed,CountryLong,
        CountryShort,NumVpnSessions,Uptime,TotalUsers,
        TotalTraffic,LogType,Operator,Message,OpenVPN_ConfigData_Base64,
        usable);
        '''    
        self.insert_records_query = '''
            INSERT INTO server (
                HostName, IP, Score, Ping, Speed, CountryLong, CountryShort,
                NumVpnSessions, Uptime, TotalUsers, TotalTraffic, LogType,
                Operator, Message, OpenVPN_ConfigData_Base64 
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        self.db_manager = db_manager 
        if not self.db_manager.validate_table("server"):
            self.db_manager.create_table(self.create_table)

    def validate_server(self, row):
        # Assuming SERVER class is defined elsewhere
        sv = SERVER(row,self.db_manager)
        sv.solvConfig()
        if 0 == sv.validate():
            return sv, 0
        else:
            return sv, -1

    def validate_row(self, row):
        # Your existing validateRow method
        if "#" in row[0]:#the 1st row
            return False
        if "*" in row[0]:#the header row
            return False
        
        try:
            iprow = self.db_manager.execute_query(f"SELECT * FROM \"server\" WHERE IP=\"{row[1]}\"")

            if ( len(iprow) == 0 ):#didn't find same ip address ,the row is valid
                return True
            else:
                return False


        except Exception as e:
            print(f"Error validating row: {e}\n")
            return False
        

    def del_server(self, rowid):
        self.db_manager.execute_non_query(f"DELETE FROM server WHERE rowid={rowid}")

    def update_server(self, rowid):
        self.db_manager.execute_non_query(f"UPDATE server SET update='True' WHERE rowid={rowid}")

    def add_server(self, row):
        # Assuming addServer method is defined elsewhere
        server_data=row.split(",")
        if self.validate_row(server_data):
#            self.validateServer(row[14])
#            self.db_manager.cur.execute(self.insert_records,row)
            self.db_manager.execute_non_query(self.insert_records_query,server_data)
        return 

    def create_database(self):
        if not os.path.isfile("vfilter.db"):
            try:
                create_table_query='''CREATE TABLE server(
                HostName,IP,
                Score,Ping,Speed,CountryLong,
                CountryShort,NumVpnSessions,Uptime,TotalUsers,
                TotalTraffic,LogType,Operator,Message,OpenVPN_ConfigData_Base64,
                usable);
                '''    
                self.db_manager.execute_query(create_table_query)
            except Exception as e:
                print(f"Error creating table: {e}\n")
    def fetch_data(self,server):
        url = f"http://{server}/api/iphone/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(url ,headers=headers)

        if response.status_code == 200:
        # 读取响应内容，按行拆分
            data_lines = response.text.split('\n')
            return data_lines
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            return []

    def update_database(self, server):
        self.create_database()
        try:
#            with open("vpn.csv", "r") as file:
#                list_data = file.readlines()
            list_data=self.fetch_data(server)
        except Exception as e:
            print(f"Error reading vpn.csv: {e}\n")
            return

        for line in list_data:
            try:
#                new_server = SERVER(line, self.db_manager)
#                new_server.solvConfig()//do not solve config ,do it later
                self.add_server(line)
            except Exception as e:
                print(f"Error adding server: {e}\n")

        self.remove_duplicates()
#        self.db_manager.commit()

    def remove_duplicates(self):
        remove_dup = '''delete from server  
        where IP in (select IP from server group by IP having count(IP) > 1) 
        and rowid not in (select min(rowid) from server group by IP having count(IP) > 1 )'''
        self.db_manager.execute_non_query(remove_dup)

    def itor(self):
        try:
            config_list = self.db_manager.execute_query("SELECT OpenVPN_ConfigData_Base64 FROM \"server\" ")
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(self.validate_server, row[0]) for row in config_list]

            for future in as_completed(futures):
                (sv, result) = future.result()
                if result == -1:
                    os.remove(sv.config)

        except Exception as e:
            print(f"Error during iteration: {e}\n")