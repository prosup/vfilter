#!/usr/bin/env python3
import sqlite3
#import csv
import os.path
import os
import base64
import socket


dpath="/tmp/vfilter/"
mode = 0o777
try :
    os.mkdir(dpath,mode)
    logfd=open("/tmp/vfilter/op.log","a")
except Exception as e :
    print(e)

#validate server from database
#we need multiple thread access server port,to determine the server is alive
class SERVER:

    def __init__(self,raw):
        self.raw=raw
        #init the tmp directory once


    def rawData(self):
        return self.raw
    
    def solvConfig(self):
        self.config=base64.b64decode(self.raw)
        
#write tmp.ovpn for grep & awk
        dpath="/tmp/vfilter/"
        fpath=dpath+"tmp.ovpn"
        try:
            cfile=open(fpath,"wb+")
            cfile.write(self.config)
        except Exception as e:
            print(e,file=logfd)
        self.solvePort()
        self.solveAddr()
        self.solveProtocol()
        self.config=dpath+self.addr+".ovpn"
        os.rename(fpath,self.config)
    
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
        if (self.protocol == "tcp"):
            socket_type=socket.SOCK_STREAM
        else:
            socket_type=socket.SOCK_DGRAM
        sk=socket.socket(socket.AF_INET,socket_type)
        sk.settimeout(0.5)
        try:
            ret=sk.connect_ex((self.addr,int(self.port)))
            if(0==ret):
                print(self.addr+":"+self.port)
                return 0
            else:
                return -1

        except Exception as e:
            print(e)
        sk.close()

        return -1

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
    ip_exist ="SELECT * FROM \"server\" WHERE IP="
    config_data ="SELECT OpenVPN_ConfigData_Base64 FROM \"server\" "

    insert_records = '''
        INSERT INTO server (
        HostName,IP,
        Score,Ping,Speed,CountryLong,
        CountryShort,NumVpnSessions,Uptime,TotalUsers,
        TotalTraffic,LogType,Operator,Message,OpenVPN_ConfigData_Base64) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        '''
    select_all = "SELECT * FROM server" 
    search_rowid_by_config = "SELECT rowid FROM server where OpenVPN_ConfigData_Base64=" 
    delete_rowid = "delete from server where rowid="
    update_rowid = "update server set update=\'True\' where rowid="
    remove_dup = '''delete from server  
        where IP in (select IP from server group by IP having count(IP) > 1) 
        and rowid not in (select min(rowid) from server group by IP having count(IP) > 1 )'''

    def validateServer(self,row):
        sv=SERVER(row)
        sv.solvConfig()
        if 0 == sv.validate():
            return (sv,0)
        else:
            return (sv,-1)

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
        if "#" in row[0]:#the 1st row
            return False
        if "*" in row[0]:#the header row
            return False
        try:
            sql=self.ip_exist+"\""+row[1]+"\""
            ret=self.cur.execute(sql)
            iprow=ret.fetchall() 
#            print(iprow)
#            config=iprow[0][14]
#            print(type(config))

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
#            self.validateServer(row[14])
            self.cur.execute(self.insert_records,row)
        return 

    def updateDatabase(self,server="www.vpngate.net"):
        self.createDatabase()
#        list=os.popen("curl http://"+server+"/api/iphone/").readlines()
#use local file to accelerate debuging process
        list=os.popen("cat vpn.csv").readlines()

        for line in list:
            try:
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
        ret=self.cur.execute(self.config_data)
        #itor all server in database ,check it's connectivity
        #flag the good server
        for row in ret.fetchall():
            (sv,result)=self.validateServer(row[0]) 
#            print(sv.config) 
            if result == -1:
                os.remove(sv.config)
        return
    def getRowid(self,row):
        ret=self.cur.execute(self.search_rowid_by_config+row)
        rowid=ret.fetchone()
        if len(rowid)==0 :
            return -1
        else:
            return rowid[0]
def main():
    sdb=SERVER_DB()
#    sdb.updateDatabase("222.255.11.117:54621")
    sdb.updateDatabase("103.201.129.226:14684")
#    sdb.updateDatabase("109.111.243.206:17579")
#    sdb.updateDatabase("78.142.193.246:33304")
#    sdb.updateDatabase("126.11.252.230:56912")
#    sdb.updateDatabase("122.208.194.111:54239")
    sdb.itor()
#    sdb.delServer("1")
#    sdb.removeDup()

if __name__ == '__main__': 
    main()
