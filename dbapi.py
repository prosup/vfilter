#!/usr/bin/env python3
import sqlite3
import os,os.path

class DatabaseManager:
    def __init__(self, db_name):
        self.db_name=db_name
        if not self.validate_database():
            self.create_database()

        self.con = sqlite3.connect(db_name)
        self.cur = self.con.cursor()

    def validate_database(self):
        if not os.path.isfile(self.db_name):
            return False
        return True

    def create_database(self):
        try:
            self.cur.execute(self.create_table)
        except Exception as e:
            print(e)
        return
    
    def validate_table(self,table_name):
        try:
            self.cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
        except Exception as e:
            print(e)
    
    def create_table(self, create_table_query):
        try:
            self.cur.execute(create_table_query)
            self.con.commit()
        except Exception as e:
            print(e)

    def execute_query(self, query):
        try:
            return self.cur.execute(query).fetchall()
        except Exception as e:
            print(e)
            return None

    def execute_non_query(self, query,data=None):
        try:
            if data is not None:
                self.cur.execute(query,data)
            else:
                self.cur.execute(query)
            self.con.commit()
        except Exception as e:
            print(e)

