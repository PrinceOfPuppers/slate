import sqlite3
import os
from queue import Queue
from time import time
from datetime import datetime

import server.config as cfg

class DbWrapper:
    def __init__(self):
        self.opsQueue = Queue()
        self.generateChatLogStr ='''
            CREATE TABLE IF NOT EXISTS chatLog (
            messageID integer PRIMARY KEY, 
            time integer NOT NULL, 
            username text NOT NULL, 
            clientID integer NOT NULL, 
            message text NOT NULL
            );'''
        self.generateConnLogStr ='''
            CREATE TABLE IF NOT EXISTS connLog (
            connID integer PRIMARY KEY, 
            time integer NOT NULL, 
            ip text NOT NULL,
            successful INTEGER NOT NULL,
            username text, 
            clientID integer
            );'''
        self.generateBansStr ='''
            CREATE TABLE IF NOT EXISTS bans (
            banID integer PRIMARY KEY, 
            time integer NOT NULL, 
            ip text NOT NULL,
            reason text NOT NULL
            );'''
        
        self.generate()

        self.msgTable = MessageTable(self.db,self.conn)
        self.connTable = connectionsTable(self.db,self.conn)
        self.banTable = BansTable(self.db,self.conn)
        
    def generate(self):
        self.conn = sqlite3.connect(cfg.dbPath)
        db = self.conn.cursor()

        db.execute(self.generateChatLogStr)
        db.execute(self.generateConnLogStr)
        db.execute(self.generateBansStr)
        self.db = db

        #used as an interface for threads trying to add to the queue
    def addToQueue(self,operation,args):
        self.opsQueue.put((operation,args))

    def pushQueue(self):
        while not self.opsQueue.empty():
            operation, args = self.opsQueue.get()
            operation(*args)

    def clearQueue(self):
        while not self.opsQueue.empty():
            self.opsQueue.get()
    

class BansTable:
    def __init__(self,db,conn):
        self.db = db
        self.conn = conn
        self.putStr = '''
            INSERT INTO bans
            (time,ip,reason)
            VALUES(?,?,?);'''
        
        self.getAllStr='''
            SELECT * FROM bans 
            ORDER BY time DESC; '''
        
        self.getIPsStr='''
            SELECT ip FROM bans 
            ORDER BY banID DESC; '''

        self.getIPStr='''
            SELECT ip FROM bans 
            WHERE banID = ?; '''
        
        self.delIDStr='''
            DELETE FROM bans
            WHERE banID = ?; '''
        
        self.delAllRows="DELETE FROM bans"

    def clear(self):
        with self.conn:
            self.db.execute(self.delAllRows)

    def popBanID(self,banID):
        with self.conn:
            self.db.execute(self.getIPStr,(str(banID),))

            fetchList = self.db.fetchall()

            #checks if fetchList isnt empty
            if fetchList:
                ip = fetchList[0][0]
            else:
                print("No Ban With That ID")
                ip = ""
            self.db.execute(self.delIDStr,(str(banID),))
        
        return ip

    def put(self,ip,reason):
        currentTime = round(time())
        with self.conn:
            self.db.execute(self.putStr,(currentTime,ip,reason))
        print(f"{ip} Banned\n")

    def getAll(self):
        self.db.execute(self.getAllStr)
        bans = self.db.fetchall()

        for i,ban in enumerate(bans):

            dateTime=datetime.fromtimestamp(ban[1])

            bans[i] = f"banID: {ban[0]}, {dateTime}, IP: {ban[2]}, Reason: {ban[3]}"
        
        bans.reverse()
        return bans

    def getIPs(self):
        self.db.execute(self.getIPsStr)
        bannedIPs = self.db.fetchall()
        
        #unpacks tups 
        for i,ip in enumerate(bannedIPs):
            bannedIPs[i]=ip[0]

        return bannedIPs


class connectionsTable:
    def __init__(self,db,conn):
        self.db = db
        self.conn=conn

        self.putStr = '''
            INSERT INTO connLog
            (time,ip,successful,username,clientID)
            VALUES(?,?,?,?,?);'''
        
        self.numStr = "SELECT Count(*) FROM connLog;"
        
        self.getNStr = '''
            SELECT * FROM connLog 
            ORDER BY time DESC
            Limit ?; '''

        #deletion strings
        self.delAllRows="DELETE FROM connLog"

        self.delOldestStr = '''
            DELETE FROM connLog
            WHERE time = (SELECT min(time) FROM connLog); '''

        self.delIPStr = '''
            DELETE FROM connLog
            WHERE ip = ?; '''
        
        self.delclientIDStr = '''
            DELETE FROM connLog
            WHERE clientID = ?; '''

    def clear(self):
        with self.conn:
            self.db.execute(self.delAllRows)

        
    def put(self,ip,successful=False,username=None,clientID=None):
        currentTime = round(time())
        successful = int(successful)

        with self.conn:
            self.db.execute(self.putStr,(currentTime,ip,successful,username,clientID))
        
    
    def num(self):
        with self.conn:
            self.db.execute(self.numStr)
            n = self.db.fetchall()[0][0]
        
        return n

    def getN(self,n):
        try:
            n=int(n)

        except:
            print(f"{n} Cannont be Interpreted as an Int\n")
            return []
        

        self.db.execute(self.getNStr,(str(n),))
        connections = self.db.fetchall()

        for i,connec in enumerate(connections):

            dateTime=datetime.fromtimestamp(connec[1])
            successful = bool(connec[3])

            connections[i] = f"connID: {connec[0]}, {dateTime}, IP: {connec[2]}, "
            if successful:
                connections[i] += f"client Info: {connec[4]}(ID:{connec[5]})"
            else:
                connections[i] += f"Connection Failed!"
        
        connections.reverse()
        return connections

    def delOldestN(self,n):
        try:
            n=int(n)

        except:
            print(f"{n} Cannont be Interpreted as an Int\n")
            return 

        with self.conn:
            for _ in range(n):
                self.db.execute(self.delOldestStr)
        
    
    def delByIP(self,ip):
        with self.conn:
            self.db.execute(self.delIPStr,(str(ip),))
        
    
    def delByClientID(self,clientID):
        try:
            clientID=int(clientID)

        except:
            print(f"{clientID} Cannont be Interpreted as an Int\n")
            return 

        with self.conn:
            self.db.execute(self.delclientIDStr,str(clientID))


class MessageTable:
    def __init__(self,db,conn):
        self.db = db
        self.conn=conn

        self.putStr = '''
            INSERT INTO chatLog
            (time,username,clientID,message)
            VALUES(?,?,?,?);'''
        
        self.numStr = "SELECT Count(*) FROM chatLog;"
        
        self.getNStr = '''
            SELECT * FROM chatLog 
            ORDER BY time DESC
            Limit ?; '''

        #deletion strings
        self.delAllRows="DELETE FROM chatLog"
        self.delOldestStr = '''
            DELETE FROM chatLog
            WHERE time = (SELECT min(time) FROM chatLog); '''

        self.delUsernameStr = '''
            DELETE FROM chatLog
            WHERE username = ?; '''
        
        self.delclientIDStr = '''
            DELETE FROM chatLog
            WHERE clientID = ?; '''
        
        self.delMessageID='''
            DELETE FROM chatLog
            WHERE messageID = ?; '''

    def clear(self):
        with self.conn:
            self.db.execute(self.delAllRows)

        
    def put(self,username,clientID,message):
        currentTime = round(time())
        with self.conn:
            self.db.execute(self.putStr,(currentTime,username,clientID,message))
        
    
    def num(self):
        with self.conn:
            self.db.execute(self.numStr)
            n = self.db.fetchall()[0][0]
        
        return n

    def getN(self,n):
        try:
            n=int(n)

        except:
            print(f"{n} Cannont be Interpreted as an Int\n")
            return []
        
        self.db.execute(self.getNStr,(str(n),))
        messages = self.db.fetchall()

        for i,message in enumerate(messages):
            dateTime=datetime.fromtimestamp(message[1])
            messages[i] = f"MsgID: {message[0]}: {dateTime}: {message[2]}(ID:{message[3]})> {message[4]}"
        
        messages.reverse()
        return messages

    def delOldestN(self,n):
        try:
            n=int(n)

        except:
            print(f"{n} Cannont be Interpreted as an Int\n")
            return 

        with self.conn:
            for _ in range(n):
                self.db.execute(self.delOldestStr)
        
    
    def delByUsername(self,username):
        with self.conn:
            self.db.execute(self.delUsernameStr,(username,))
        
    
    def delByClientID(self,clientID):
        try:
            clientID=int(clientID)

        except:
            print(f"{clientID} Cannont be Interpreted as an Int\n")
            return 

        with self.conn:
            self.db.execute(self.delclientIDStr,str(clientID))