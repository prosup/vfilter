#!/usr/bin/env python3
import sqlite3
#import csv
import os.path
import os
import base64

#validate server from database
#we need multiple thread access server port,to determine the server is alive
class SERVER:

    def __init__(self,raw):
        self.raw=raw
        

    def rawData(self):
        return self.raw
    
    def solvConfig(self):
        self.config=base64.b64decode(self.raw)
        
#write tmp.ovpn for grep & awk
        dpath="/tmp/vfilter/"
        mode = 0o777
        try :
            os.mkdir(dpath,mode)
        except Exception as e :
            print(e)
        fpath=dpath+"tmp.ovpn"
        try:
            cfile=open(fpath,"wb+")
            cfile.write(self.config)
        except Exception as e:
            print(e)
        self.solvePort()
        self.solveAddr()
        self.solveProtocol()
        os.rename(fpath,dpath+self.addr+".ovpn")
    
    def solveProtocol(self):
        cmd="cat /tmp/vfilter/tmp.ovpn | grep ^proto | awk '{print $2}'"
        self.protocol=os.popen(cmd).readline().split("\n")[0]
        return 

    def solvePort(self):
        cmd="cat /tmp/vfilter/tmp.ovpn | grep ^remote | awk '{print $3}'"
        self.port=os.popen(cmd).readline().split("\n")[0]
        return 

    def solveAddr(self):
        cmd="cat /tmp/vfilter/tmp.ovpn | grep ^remote | awk '{print $2}'"
        self.addr=os.popen(cmd).readline().split("\n")[0]
        return 

    def validate(self):

        return

## manage server database
class SERVER_DB:
    con = sqlite3.connect("vfilter.db")
    cur = con.cursor()

    create_table='''CREATE TABLE server(
        HostName,IP,
        Score,Ping,Speed,CountryLong,
        CountryShort,NumVpnSessions,Uptime,TotalUsers,
        TotalTraffic,LogType,Operator,Message,OpenVPN_ConfigData_Base64,
        usable);
        '''    
    ip_exist ="SELECT rowid FROM \"server\" WHERE IP="

    insert_records = '''
        INSERT INTO server (
        HostName,IP,
        Score,Ping,Speed,CountryLong,
        CountryShort,NumVpnSessions,Uptime,TotalUsers,
        TotalTraffic,LogType,Operator,Message,OpenVPN_ConfigData_Base64) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        '''
    select_all = "SELECT * FROM server" 
    delete_rowid = "delete from server where rowid="
    update_rowid = "update server set update=\'True\' where rowid="
    remove_dup = '''delete from server  
        where IP in (select IP from server group by IP having count(IP) > 1) 
        and rowid not in (select min(rowid) from server group by IP having count(IP) > 1 )'''

    def validateServer(self,row):
        sv=SERVER(row)
        sv.solvConfig()

        return

    def validateDatabase(self):#if the datebase is avalible
        if not os.path.isfile("vfilter.db"):
            return False
        try:
            lists=self.cur.execute(self.select_all).fetchall() 
        except Exception as e:
            print(e)
            return False
        return lists
    
    def validateRow(self,row):#if the row data is avaible
        if "#" in row[0]:
            return False
        if "*" in row[0]:
            return False
        try:
            sql=self.ip_exist+"\""+row[1]+"\""
            iprow=self.cur.execute(sql).fetchall()
            if ( len(iprow) == 0 ):#didn't find same ip address ,the row is valid
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return True
    
    def createDatabase(self):
        if not self.validateDatabase(): 
            try:
                self.cur.execute(self.create_table)
            except Exception as e:
                print(e)
        return
    #delete server by it's index
    def delServer(self,id):#delete one line of server,if the server is deprecated
        self.cur.execute(self.delete_rowid+id) 
        self.con.commit()
        return
    def updateServer(self):#new server data has been verified,modified the "col" to "good"
        self.cur.execute(self.update_rowid+id) 
        self.con.commit()
        return

    def addServer(self,s):
        row=s.split(",")
        if self.validateRow(row):
            self.validateServer(row[14])
            self.cur.execute(self.insert_records,row)
        return 

    def updateDatabase(self,server="www.vpngate.net"):
        self.createDatabase()
        list=os.popen("curl http://"+server+"/api/iphone/").readlines()

        for line in list:
            try:
#                self.cur.execute()
#                self.validateServer(line)
                self.addServer(line)
            except Exception as e:
                print(e)
#                print(line.split(","))

        self.con.commit()
    # closing the database connection
#        self.con.close() 
        return
    def removeDup(self):
        self.cur.execute(self.remove_dup)
        self.con.commit()
        return 
    
    def configCache(self):

        return
    def itor(self):

        return

def main():

    sdb=SERVER_DB()
    sdb.updateDatabase("222.255.11.117:54621")
#    sdb.delServer("1")
#    sdb.removeDup()

if __name__ == '__main__': 
    main()