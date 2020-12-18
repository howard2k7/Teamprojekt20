from tkinter import *
import threading
import verbindungsTest
import time
import Gamepad as gp
import re

class mainGui:
    def __init__(self, master):
        self.master = master
        master.geometry("1500x700")
        master.config(bg="white")
        master.title("Main Interface")
        master.resizable(False, False)

        #building frame grid
        self.frameTop = Frame(master, padx=50, pady=50)
        self.frameTop.grid(row=0, column=0)
        self.frameTopRight = Frame(master, padx=50, pady=50)
        self.frameTopRight.grid(row=0, column=1)
        self.frameBot = Frame(master, padx=50, pady=50)
        self.frameBot.grid(row=1, column=0)
        self.frameBotRight = Frame(master, padx=50, pady=50)
        self.frameBotRight.grid(row=1, column=1)

        # frame for terminal
        self.frameTerminal = Frame(self.frameBotRight)
        self.frameTerminal.grid(row=2, column=3)
        self.frameTerminal.configure(background='black')

        # frame for terminal2
        self.frameTerminal2 = Frame(self.frameBot)
        self.frameTerminal2.grid(row=0, column=0)
        self.frameTerminal2.configure(background='black')

        # create scrollbar
        self.scrollbar = Scrollbar(self.frameTerminal)
        self.scrollbar.pack(side=RIGHT, fill="y")

        # create scrollbar2
        self.scrollbar2 = Scrollbar(self.frameTerminal2)
        self.scrollbar2.pack(side=RIGHT, fill="y")

        # create output
        self.output = Listbox(self.frameTerminal, yscrollcommand=self.scrollbar.set , width=50, height=15, background='black', fg='white')
        self.output.pack(side=LEFT)
        self.scrollbar.config(command=self.output.yview)

        # create output
        self.output2 = Listbox(self.frameTerminal2, yscrollcommand=self.scrollbar2.set, width=50, height=15,
                              background='black', fg='white')
        self.output2.pack(side=LEFT)
        self.scrollbar2.config(command=self.output2.yview)

        # initial set for variables
        self.selectedHeight = StringVar(main)
        self.selectedHeight.set("Höhe 1")
        self.selectedPace = StringVar(main)
        self.selectedPace.set("Geschwindigkeit 1")

        # creating drop menus
        self.dropPace = OptionMenu(self.frameTop, self.selectedPace, "Geschwindigkeit 1", "Geschwindigkeit 2", "Geschwindigkeit 3")
        self.dropPace.grid(row=1, column=2)
        self.dropPace.config(padx=20)
        self.dropHeight = OptionMenu(self.frameTop, self.selectedHeight, "Höhe 1", "Höhe 2", "Höhe 3")
        self.dropHeight.grid(row=1, column=1)

        # creating Buttons
        self.heightSelectedButton = Button(self.frameTop, text="Höhe übernehmen", pady=20, padx=20, command=lambda: threading.Thread(target=self.heightSelect).start())
        self.heightSelectedButton.grid(row=2, column=1)
        self.paceSelectedButton = Button(self.frameTop, text="Geschwindigkeit übernehmen", pady=20, padx=20, command=lambda: threading.Thread(target=self.paceSelect).start())
        self.paceSelectedButton.grid(row=2, column=2)

        # initial terminal message
        self.write("Betriebsbereit !")
        self.write2("Betriebsbereit !")


        # create labels
        self.descriptionLabel = Label(self.frameTopRight, text="Gebe die IP-Adresse des Servers ein !")
        self.testLabel2 = Label(self.frameTopRight, text="IP Adresse:")
        self.conLabel = Label(self.frameTopRight, text="Verbindung nicht aufgebaut !", bg="red")


        # arrange labels
        self.testLabel2.grid(row=2, column=0)
        self.descriptionLabel.grid(row=0, column=0)
        self.conLabel.grid(row=0, column=2)


        # create input field
        self.ipField = Entry(self.frameTopRight)
        self.ipField.config(width=25)

        # arrange input field
        self.ipField.grid(row=2, column=1)

        # create button
        self.connectButton = Button(self.frameTopRight, text="Verbinden", pady=20, padx=20,
                                    command=lambda: threading.Thread(target=self.connectionClick).start())

        # arrange button
        self.connectButton.grid(row=2, column=2)

    def connectionClick(self):
        self.conLabel.config(bg="yellow", text="Verbindung wird aufgebaut")
        self.master.update()

        ipaddress = ""
        text = self.ipField.get()
        ipaddressOK = re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$",text)
        
        if ipaddressOK:
            ipaddress = ipaddressOK.string

        if ipaddress:

            # call connection method
            myGamepad = gp.Gamepad(ipaddress, self)
            myGamepad.checkConnection()
            time.sleep(2)

            # checking the answer
            if (myGamepad.getConnectionStatus()):
                self.write("Connected....")
                self.connectionIsPositive(myGamepad)
            else:
                print("Verbindungs TimeOut")
                self.conLabel.config(text="Verbindung nicht aufgebaut !", bg="red")
            # myGamepad.getControlSignals()
        else:
            print("Fehler nichts eigegeben!")
            self.conLabel.config(bg="red", text="Verbindung fehlgeschlagen")
        # del myGamepad

    def connectionIsPositive(self, myGamepad):
        self.conLabel.config(bg="green", text="Verbindung erfolgreich!")
        myGamepad.getControlSignals()
        return

    def convertString(self, string):
        helpStr = ""
        for i in range(len(string)):
            if string[i] != "'" and string[i] != "(" and string[i] != ")" and string[i] != ",":
                helpStr = helpStr + string[i]
        return helpStr


    def heightSelect(self):
        height = 0
        self.write("Befehl: " + self.selectedHeight.get())
        if self.selectedHeight.get() == "Höhe 1":
            height = 1
        elif self.selectedHeight.get() == "Höhe 2":
            height = 2
        elif self.selectedHeight.get() == "Höhe 3":
            height = 3
            # call heightSelect method with height
        help = verbindungsTest.hoeheStufe(height)
        self.write(str(help))


    def paceSelect(self):
        pace = 0
        self.write("Befehl: " + self.selectedPace.get())
        if self.selectedPace.get() == "Geschwindigkeit 1":
            pace = 1
        elif self.selectedPace.get() == "Geschwindigkeit 2":
            pace = 2
        elif self.selectedPace.get() == "Geschwindigkeit 3":
            pace = 3
        # call paceSelect method with pace
        help = verbindungsTest.geschwStufe(pace)
        self.write(str(help))

    def write(self, txt):
        self.output.insert(END, str(self.convertString(txt) + "\n"))
        self.output.see("end")

    def write2(self, txt):
        self.output2.insert(END, str(txt + "\n"))
        self.output2.see("end")


if __name__ == "__main__":
    main = Tk()
    my_maingui = mainGui(main)
    main.mainloop()

