import socket
from time import sleep
from enum import Enum,auto
import sys
import threading

from client.queues import EventQueue
from packets.packets import PType, sockWrapper
from client.helpers import startSocket, getSaved,serverHistory,getIpFromStr
import client.threads as threads
import client.config as cfg
from client.gui import Gui

class Client:
    def __init__(self):
        self.running = True
        self.gui = Gui(self.textSubmitted,self.close)
        

        #sorted by id number
        self.clientsDict = {}
        self.dictLock = threading.Lock()

        self.servers=serverHistory()

        self.threadJobs=["recieve","transmit"]
        self.threads={}

        self.eventQueue = EventQueue()

        try:
            self.dict = getSaved(self.gui)
        except:
            self.running = False
            
        if self.running:
            #server panel must be updated on seperate thread to avoid hanging
            self.gui.updateSidePanel(["Pinging Servers..."],[cfg.subTextColor])
            threads.nonDaemon(self.gui.updateServerPanel,(self.servers,self.eventQueue))
            self.connect()


    def reset(self):
        try:# catch for reset before connection
            self.disconnect()
        except:
            pass
        
        #waits for all threads to stop running
        self.running = False
        for job in self.threadJobs:
            if job in self.threads.keys():
                self.threads[job].join()

        self.clientsDict.clear()
        self.gui.updateClientsPanel(self.clientsDict,self.dictLock)
        self.threads.clear()
        self.eventQueue.clear()
        self.sock.clear()

        self.running = True
        
        threads.nonDaemon(self.gui.updateServerPanel,(self.servers,self.eventQueue))
        self.connect()


    def connect(self):
        while self.running:
            inStr = self.gui.prompt("What IP Would You Like to Connect to? ",self.eventQueue)
            ip = getIpFromStr(self.servers.dict,inStr)
            if not self.running:
                break
            try:

                self.gui.addText("Attempting to Connect...")
                self.gui.tkRoot.update()
                sock = startSocket(ip)
                self.sock = sockWrapper(sock,cfg.bufferSize)
            except:
                self.gui.addText("Failed To Connect To That IP")
                continue

            #sends clientData
            try:
                self.sock.addClientData(self.dict)
                self.sock.send()
            except:
                self.sock.close()
                self.gui.addText("Connected But With No Response")
                continue

            threads.startThreads(self)
            #allows server to overwrite id and username for runtime
            _,self.dict = self.sock.get(True)

           

            #gets number of users in chatroom
            _,numUsers = self.sock.get(True)
            for _ in range(0,numUsers):
                #gets other users in chatroom
                pType,data = self.sock.get(True)
                self.packetSwitch(pType,data)

            #gets server name
            pType,data = self.sock.get(True)

            #gets actual ip incase user typed localhost
            ip = self.sock.sock.getpeername()[0]
            self.servers.add(ip,data[1])

            break
    
    def disconnect(self):
        text="Disconnecting from Server"
        self.eventQueue.addEvent(self.gui.addText,(text,))
        
        self.sock.addEot()

        #waits for server to see leave message
        sleep(1)

        self.sock.close()
    
    def close(self):
        try:# catch for closure before connection
            self.disconnect()
        except:
            pass
        
        #waits for all threads to stop running

        self.running = False
        for job in self.threadJobs:
            if job in self.threads.keys():
                self.threads[job].join()

        #sys.exit()

    def packetSwitch(self,pType,data):
        if pType == PType.eot:
            self.eventQueue.addEvent(self.serverDisconnected,())

        elif pType == PType.message:
            userId,message=data
            if userId !=-1:

                self.dictLock.acquire()
                clientDict=self.clientsDict[userId]
                self.dictLock.release()

                self.eventQueue.addEvent(self.gui.addMessage,(message,clientDict))
            else:
                self.eventQueue.addEvent(self.gui.addText,(message,))

        elif pType == PType.clientData:
            self.dictLock.acquire()
            self.clientsDict[data["id"]] = data
            self.dictLock.release()

            self.eventQueue.addEvent(self.gui.updateClientsPanel,(self.clientsDict,self.dictLock))

        elif pType == PType.clientDisconnect:

            self.dictLock.acquire()
            username = self.clientsDict[data]["username"]
            self.clientsDict.pop(data,None)
            self.dictLock.release()

            text = f"> {username} Disconnected"
            self.eventQueue.addEvent(self.gui.addText, (text,))
            self.eventQueue.addEvent(self.gui.updateClientsPanel,(self.clientsDict,self.dictLock))

        
        elif pType == PType.ping:
            pass
        
        else:
            print("Recieved Invalid Packet Type")


    def serverDisconnected(self):
        text="Server Disconnected"
        self.eventQueue.addEvent(self.gui.addText,(text,))
        self.eventQueue.addEvent(self.reset,())


    #callback when enter is hit in text field
    def textSubmitted(self,text):
        self.sock.addMessage(text,self.dict["id"])

    #run by transmit thread
    def transmit(self):
        while self.running:
            while not self.sock.outEmpty():
                try:
                    self.sock.send()
                except:
                    if self.running:
                        self.serverDisconnected()
            #lowers resource usage
            sleep(cfg.sleepTime)
        
    #run by thread
    def recievingLoop(self):
        while self.running:
            try:
                self.sock.listen()
            except:
                pass
            #lowers resource usage
            sleep(cfg.sleepTime)

    #run by main thread
    def mainLoop(self):
        while self.running:
            try:
                while not self.eventQueue.empty():
                    self.eventQueue.triggerEvent()

                while self.running and not self.sock.inQueue.empty():
                    pType,data = self.sock.get()
                    self.packetSwitch(pType,data)

                self.gui.tkRoot.update()
            except:
                break
            #lowers resource usage
            sleep(cfg.sleepTime)
        self.close()
