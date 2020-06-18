import socket
from time import sleep,time
from datetime import timedelta

from packets.packets import PType,sockWrapper
from server.helpers import startServer, getRoomName,ensureUniqueUsername
from server.structures import ClientData
import server.threads as threads
from server.dbWrapper import DbWrapper
import server.config as cfg


class Server:
    def __init__(self):
        self.running = False
        self.roomName = getRoomName()
        #unix time when server was last started
        self.startTime=0

        self.db = DbWrapper()
        self.bannedIPs = self.db.banTable.getIPs()

        self.clients = []
        self.threads=[]

    def __str__(self):
        servStr = f"Server is Called {self.roomName} "
        if self.running:
            servStr += f"and has {len(self.clients) } Clients Connected\n"
            servStr += f"it Has Been Running For {timedelta(seconds = round(time() - self.startTime)) }\n"
            servStr += f"External IP: {self.ip}, Internal IP {self.localIp}, Port: {cfg.port}\n"
            
        else:
            servStr +="Currently Not Running"
        
        return servStr

    def start(self):
        self.running = True
        self.startTime = round(time())
        self.nextClientID = 0
        self.s,self.ip,self.localIp = startServer()
        threads.startThreads(self)

    def getClientById(self,clientId):
        for client in self.clients:
            if client.dict["id"]==clientId:
                return client
        
        return None

    def banIP(self,ip,reason="None Given"):
        ip=ip.strip()
        self.bannedIPs.append(ip)
        self.db.addToQueue(self.db.banTable.put,(ip,reason))

        for client in self.clients:
            if client.ip == ip:
                self.dropClient(client)
    
    #must be run on main thread 
    def removeBan(self,banID):
        ip = self.db.banTable.popBanID(banID)
        if ip in self.bannedIPs:
            self.bannedIPs.remove(ip)

    #run on thread
    def awaitConnections(self):
        while self.running:
            sleep(cfg.sleepTime)
            try:
                clientSocket, addr = self.s.accept()
                ip = addr[0]
                #checks if client is banned
                if ip in self.bannedIPs:
                    clientSocket.close()
                    continue
            except:
                continue
            
            sockWrap = sockWrapper(clientSocket,cfg.bufferSize)

            #gets userdata
            try:
                sockWrap.listen()
                _,clientDataDict = sockWrap.get()

                clientUsername = clientDataDict["username"]
                clientUsername=ensureUniqueUsername(clientUsername,self.roomName,self.clients)

                #updates client data dict with proper user id
                clientID = self.nextClientID
                clientDataDict["id"]= clientID
                clientDataDict["username"]=clientUsername

                sockWrap.addClientData(clientDataDict)
                sockWrap.send()

                sockWrap.addIterations(len(self.clients))
                sockWrap.send()
            except:
                #connection failed in inital setup (likley didnt connect using client)
                self.db.addToQueue(self.db.connTable.put,(ip,))
                continue

            #sends active users
            for client in self.clients:
                sockWrap.addClientData(client.dict)
                sockWrap.send()
            
            #sends server name
            sockWrap.addMessage(self.roomName)
            
            newClient = ClientData(sockWrap,ip,clientDataDict)

            self.clients.append(newClient)
            message = f"> {clientUsername} Joined {self.roomName}"

            #logs message and client connection
            self.db.addToQueue(self.db.msgTable.put,("Server",-1,message))
            self.db.addToQueue(self.db.connTable.put,(ip,True,clientUsername,clientID))

            for client in self.clients:
                client.sock.addClientData(newClient.dict)
                client.sock.addMessage(message)
                
            client.sock.sock.settimeout(cfg.waitTime)
            self.nextClientID+=1
            

    #client index is for eot transmission so this method knows who disconnected
    def packetSwitch(self,pType,data,client=None):
        if pType == PType.eot:
            self.dropClient(client)

        elif pType == PType.message:
            messangerID, message = data
            username = client.dict["username"]
            self.db.addToQueue(self.db.msgTable.put,(username,messangerID,message))
            for client in self.clients:
                client.sock.addMessage(message, messangerID,username)
                

        elif pType == PType.clientData:
            print("ClientData Recieved Unexpectedly")

        elif pType == PType.clientDisconnect:
            print("ClientDisconnect Packet Intended for Server to Client Only")
        
        elif pType == PType.ping:
            pass
        
        else:
            print("Recieved Invalid Packet Type")

    #run on thread
    def recieving(self):
        while self.running:
            sleep(cfg.sleepTime)
            for client in self.clients:
                try:
                    client.sock.listen()
                    pType,data = client.sock.get()
                    self.packetSwitch(pType,data,client)
                except:
                    continue

    #run on thread
    def relay(self):
        while self.running:
            sleep(cfg.sleepTime)
            for client in self.clients:
                while not client.sock.outEmpty() and client in self.clients:
                    try:
                        client.lock.acquire()
                        client.sock.send()
                        client.lock.release()

                    #client not recieving packets
                    except:
                        client.lock.release()
                        self.dropClient(client)


    def dropClient(self,client):
        username=client.dict["username"]
        self.db.addToQueue(self.db.msgTable.put,("Server",-1,f"{username} Disconnected"))

        clientId = client.dict["id"]
        client.sock.close()
        self.clients.remove(client)
        for otherClients in self.clients:
            otherClients.sock.addClientDisconnect(clientId,username)
    
    def close(self):
        if not self.running:
            print("Server Not Started\n")
            return
        

        print("Closing...")
        self.db.addToQueue(self.db.msgTable.put,("Server",-1,f"Closing"))

        #sends client eot
        for client in self.clients:
            client.lock.acquire()
            client.sock.addEot()
            while not client.sock.outEmpty():
                try:
                    client.sock.send()
                except:
                    break
            client.lock.release()

        #closes socket and removes client
        for client in self.clients:
            self.dropClient(client)

        self.running = False

        self.threads.clear()
        self.clients.clear()
        self.s.close()
        print("Server Closed\n")
        