
from inspect import signature,getargspec
import sys


class Operation:
    def __init__(self,funct):
        #Callback function which exacutes the operation
        self.funct = funct

        numParams =  len(signature(funct).parameters)
        numDefaults = getargspec(funct).defaults

        if numDefaults == None:
            numDefaults = 0
        else:
            numDefaults = len(numDefaults)

        #number of arguments function takes (range accounts for defaults)
        self.minArgs = numParams - numDefaults
        self.maxArgs = numParams

        self.argRange = range(self.minArgs,self.maxArgs+1)
    
    def argsErrorPrint(self,cmdName):
        if self.minArgs == self.maxArgs:
            numArgs =self.minArgs
        else:
            numArgs = f"Between {self.minArgs} and {self.maxArgs}"

        print(f"Invalid Number of Arguments, {cmdName} Requires {numArgs} Arguments\n")




def printHelp():
    message ='''
Commands:
    help                    -Show Help Message
    exit                    -Close Application

    start                   -Launch Server
    close                   -Close Server
    info                    -Show Server Name and Network Details

    clients                 -Show Connected Clients Data

    msgs [n]                -Show Most Recent n Messages (n defaults to 50)
    numMsgs                 -Shows How Many Messages are in the Database
    rmMsgs [n]              -Delete the Oldest n Messages
    clrMsgs                 -Delete all Messages

    conns [n]               -Show Most Recent n Connections Made (n defaults to 50)
    numConns                -Shows How Many Connections Logs are in the Database
    rmConns [n]             -Delete the Oldest n Connection Logs
    clrConns                -Delete all Connection Logs

    ban [ip] [reason]       -Kick and Ban ip Address (Reason is Optional, and for Internal Reference)
    bans                    -Lists all Active Bans
    rmBan                   -Remove IP Ban by BanID (use bans command to see ID)
    clrBans                 -clear all bans
    '''
    print(message)

def exitWrapper():
    print("Closing App")
    sys.exit()
    
def loadCommands(server):

    commandsDict = {
        "help": Operation(printHelp),
        "exit": Operation(exitWrapper),

        "start": Operation(server.start),
        "close": Operation(server.close),
        "info": Operation(lambda: print(server)),

        "clients": Operation(lambda: print("\n".join(str(client) for client in server.clients),"\n") ),

        "msgs": Operation(lambda n=50: print("\n".join(server.db.msgTable.getN(n))+"\n")),
        "numMsgs": Operation(lambda : print(server.db.msgTable.num(),"\n") ),
        "rmMsgs": Operation(server.db.msgTable.delOldestN),
        "clrMsgs": Operation(server.db.msgTable.clear),

        "conns": Operation(lambda n=50: print("\n".join(server.db.connTable.getN(n))+"\n")),
        "numConns": Operation(lambda : print(server.db.connTable.num(),"\n") ),
        "rmConns": Operation(server.db.connTable.delOldestN),
        "clrConns": Operation(server.db.connTable.clear),

        "ban": Operation(server.banIP),
        "bans": Operation(lambda : print("\n".join(server.db.banTable.getAll())+"\n")),
        "rmBan": Operation(server.removeBan),
        "clrBans": Operation(server.db.banTable.clear),
    }

    return commandsDict