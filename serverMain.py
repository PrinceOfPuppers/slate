from time import sleep
import ast
import threading
from queue import Queue
from server.server import Server
from server.serverShell import loadCommands
import server.config as cfg
from server.helpers import sanitizeInput

#run by shell thread
def pollInputs(inputQueue):
    print("Welcome To Slate Shell! Type 'help' to See all Commands\n")
    while True:
        inStr = input("")
        inputQueue.put(inStr)



def parseInput(commandDict,inStr):
    inList = sanitizeInput(inStr)
    #checks if valid command
    command = inList[0]
    if not command in commandDict:
        print("Unknown Command\n")
        return
    
    #checks if valid numbe of arguments
    command = commandDict[command]
    args = inList[1:]

    if len(args) not in command.argRange:

        command.argsErrorPrint(inList[0])
        return
    
    command.funct(*args)


if __name__ == "__main__":
    serv=Server()
    commandDict = loadCommands(serv)
    inputQueue = Queue()
    #used as a bool but with reference type so the thread knows when to stop

    shellThread = threading.Thread(target =lambda: pollInputs(inputQueue))

    shellThread.daemon = True
    shellThread.start()
    
    while True:
        #database queries can only be excecuted on main thread
        #hence why theyre done here
        while not serv.db.opsQueue.empty():
            serv.db.pushQueue()

        while not inputQueue.empty():
            inStr = inputQueue.get()
            parseInput(commandDict,inStr)
        
        sleep(cfg.sleepTime)

        


        

