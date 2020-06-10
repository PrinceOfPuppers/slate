import tkinter as tk
import tkinter.scrolledtext as scrolledtext
import config as cfg

class Gui:
    def __init__(self,enterCallback):
        self.tkRoot = tk.Tk()
        self.generateTkinterObjs(enterCallback)
        self.makeLayout()
        print("asdf")

    def generateTkinterObjs(self,enterCallback):
        self.tkRoot.geometry(cfg.tkinterWinSize)
        self.tkRoot.option_add( "*font", cfg.tkinterFont)
        window=tk.Frame(self.tkRoot)
        window.pack(fill='both',expand=True)
        window.configure(background= cfg.darkGrey)


        #root note selection
        messages=scrolledtext.ScrolledText(window)
        messages.configure(background= cfg.darkGrey,foreground="white",borderwidth=0,padx=10,pady=5)

        textVar=tk.StringVar(window)
        textInput=tk.Entry(window,textvariable=textVar)
        textInput.configure(background= cfg.grey,foreground="white",highlightthickness=0,borderwidth=cfg.textInputPad,relief=tk.FLAT)
        #binds return key to sumbit text
        textInput.bind("<Return>", lambda event: enterCallback(textVar) )

        #to become submit button
        #generateButton=tk.Button(window,text="Generate",command=lambda: eventHand.generateButton(app,cfg,plotter,getTuningList(tuningStrVar),root.get(),scale.get()))
        #generateButton.configure(background= 'red',activebackground='#404040')

    
        self.window=window
        self.messages=messages
        self.textInput = textInput
    
    def makeLayout(self):

        self.messages.grid(row=0,sticky = tk.NSEW)

        self.textInput.grid(row=1,sticky = 'sew')


        self.window.rowconfigure(0,weight=2)
        self.window.rowconfigure(0,weight=1)
        self.window.columnconfigure(0,weight=1)
    
    def addText(self,text):
        self.messages.insert(tk.END,"\n"+text)

        self.messages.see(tk.END)