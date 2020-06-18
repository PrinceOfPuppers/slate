import tkinter as tk
import tkinter.scrolledtext as scrolledtext
from time import sleep
import client.config as cfg

class Gui:
    def __init__(self,enterCallback,closeCallback):
        self.tkRoot = tk.Tk()
        self.tkRoot.iconphoto(False,tk.PhotoImage(file = cfg.windowIconPath))

        self.tkRoot.title(cfg.windowName)
        self.generateTkinterObjs()
        self.makeLayout()

        self.lastMessanger=""
        self.prompting=False
        self.promptReturn=""
        #called in textSubmitted
        self.sendToClient = enterCallback

        #used for closing the client if x is hit
        self.closeClient = closeCallback

    def generateTkinterObjs(self):
        self.tkRoot.geometry(cfg.tkinterWinSize)
        self.tkRoot.option_add( "*font", cfg.tkinterFont)
        window=tk.Frame(self.tkRoot)
        window.pack(fill='both',expand=True)
        window.configure(background= cfg.softBlack)


        #main chatbox
        messages=scrolledtext.ScrolledText(window)
        messages.configure(background= cfg.darkGrey,foreground=cfg.defaultTextColor,borderwidth=0,padx=10,state='disabled')

        textVar=tk.StringVar(window)
        textInput=tk.Entry(window,textvariable=textVar)
        textInput.configure(background= cfg.grey,foreground=cfg.defaultTextColor,borderwidth=cfg.textInputPad,relief=tk.FLAT)
        #binds return key to textEntered
        textInput.bind("<Return>", lambda event: self.textEntered(textVar) )

        #clients online panel
        sidePanel=tk.Text(window)
        sidePanel.configure(background=cfg.softBlack, foreground = cfg.defaultTextColor,borderwidth=0,padx=10,pady=5,state='disabled')

        #configure color tags
        for color in cfg.colors:
            messages.tag_config(color, foreground=color)
            sidePanel.tag_config(color, foreground=color)
    
        self.window=window
        self.window.bind()
        self.messages=messages
        self.textInput = textInput
        self.sidePanel=sidePanel
    
    def makeLayout(self):

        self.messages.grid(row=0,sticky = tk.NSEW)

        self.textInput.grid(row=1,sticky = 'sew')
        self.sidePanel.grid(row=0, column=1,sticky='nes',rowspan=2)

        self.window.rowconfigure(0,weight=2)
        #self.window.rowconfigure(1,weight=1)
        self.window.columnconfigure(0,weight=1)
        self.window.columnconfigure(1,weight=3)
    
    #formats based on whos speaking
    def addMessage(self,message,clientDict):
        username = clientDict["username"]
        color = clientDict["color"]
        clientId = clientDict["id"]

        self.messages.configure(state='normal')
        if clientId == self.lastMessanger:
            self.messages.insert(tk.END,message+"\n")
        
        else:
            self.lastMessanger = clientId
            self.messages.insert(tk.END,f"\n{username}", color)
            self.messages.insert(tk.END,f"> {message}\n")
        self.messages.configure(state='disabled')

        self.messages.see(tk.END)
        self.textInput.focus_force()


    #username is simply for api compatibility
    def addText(self,text,color=cfg.defaultTextColor):
        self.lastMessanger=-1

        self.messages.configure(state='normal')
        self.messages.insert(tk.END,f"\n{text}\n", color)
        self.messages.configure(state='disabled')

        self.messages.see(tk.END)
        self.textInput.focus_force()
        
    def updateSidePanel(self,entires,colors):
        self.sidePanel.configure(state='normal')
        self.sidePanel.delete(1.0,tk.END)
        for i,text in enumerate(entires):
            self.sidePanel.insert(tk.END,text+"\n", colors[i])
        self.sidePanel.configure(state='disabled')

    #wrappers for updateSidePanel
    def updateClientsPanel(self,clientsDict,lock):
        lock.acquire()
        entries = [client["username"] for client in clientsDict.values()]
        colors = [client["color"] for client in clientsDict.values()]
        lock.release()
        self.updateSidePanel(entries,colors)
    

    #ment to be run on thread due to long socket pinging time
    #as such it cant update gui and has to create an event
    def updateServerPanel(self,servers,eventQueue):
        ips,names,isOnline = servers.getOnline()
        
        entries = []
        colors = []
        for n,ip in enumerate(ips):
            entries.append(f"{names[n]}:\n    {ip}")
            colors.append(cfg.onlineColor if isOnline[n] else cfg.offlineColor)
        

        eventQueue.addEvent(self.updateSidePanel,(entries,colors))

    def textEntered(self,strVar):
        text=strVar.get()
        text=text.strip()
        strVar.set("")

        #puts text into prompt return and 
        #signals to prompt method that prompt was
        #submitted
        if self.prompting:
            self.promptReturn=text
            self.prompting = False

        else:
            self.sendToClient(text)


    def prompt(self,text,eventQueue=None,color=cfg.defaultTextColor):
        self.addText(text,color)
        self.prompting = True
        
        #made true if application was closed during prompt
        while self.prompting:
            #lowers resource usage
            sleep(cfg.sleepTime)
            try:
                self.tkRoot.update()

                #allows main thread to process events while waiting for prompt return
                if eventQueue:
                    while not eventQueue.empty():
                        eventQueue.triggerEvent()
            except:
                self.prompting=False
                self.closeClient()
        
        #textEntered has placed the input into self.promptReturn
        return self.promptReturn
