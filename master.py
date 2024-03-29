#!/usr/bin/python
import tkinter as tk
from tkinter import filedialog
import subprocess
import pandas as pd
import os


class MainApplication(tk.Frame):


    def __init__(self, parent):
        self.parent = parent
        self.create_GUI(parent)

    def create_GUI(self, parent):
        tk.Frame.__init__(self, parent)
        parent.geo = parent.geometry("800x600")
        parent.title("3DQI DICOM Editor")
        self.headFrame = tk.Frame(parent)
        self.headFrame.grid(row=1)
        self.centFrame = tk.Frame(parent, width=800, height=450)
        self.centFrame.grid(row=2, sticky="ew")
        self.header = tk.Label(self.headFrame, text="3DQI DICOM tagger", font=("Helvetica", 24), padx=100)
        self.header.grid(row=1, sticky="nw")
        self.directoryButton = tk.Button(self.headFrame, text="Find DCM Directory", command=self.browse_button, padx=50)
        self.directoryButton.grid(row=2, sticky="e")

        self.RFfileButton = tk.Button(self.headFrame, text="Enter Texture File (CSV)", command=self.getRFfile, padx=50)
        self.RFfileButton.grid(row=2, sticky="w", pady=10)

        self.allParamLabel = tk.Label(self.centFrame, text="Header Available Options", pady = 10)
        self.allParamLabel.grid(row=1, column=1, sticky="n", pady=20)
        self.allParams = tk.Listbox(self.centFrame, height = 20)
        self.allParamVals = self.getTAGRefVals()
        index = 0
        for param in self.allParamVals:
            self.allParams.insert(index, param)

        self.allParams.grid(row=2, column=1, padx=10)
        self.paramButton = tk.Button(self.centFrame, text = ">", command = self.moveParams ,padx= 5)
        self.paramButton.grid(row = 2, column = 2, padx = 5)
        self.wantedPLabal = tk.Label(self.centFrame, text="Copy desired DICOM Values from left box to the box below")
        self.wantedPLabal.grid(row=1, column = 3)
        self.wantedParams = tk.Text(self.centFrame, height = 20, width = 70)
        self.wantedParams.grid(row=2, column=3, sticky = "n")
        self.findDCM = tk.Button(self.centFrame, text="Search", command=self.begin, state="disabled", padx = 100)
        self.findDCM.grid(column=3, row=3, pady = 10, sticky = "w")
        self.openFile = tk.Button(self.centFrame, text="ViewFile", command = self.openResult, state = "disabled", padx = 100)
        self.openFile.grid(column = 3, row = 3, pady = 10, sticky = "e")

        self.statusLabel = tk.Label(self.centFrame, text="Status: Enter Texture File From 3DQI")
        self.statusLabel.grid(column = 3, row = 4)

    def moveParams(self):
        values = [self.allParams.get(idx) for idx in self.allParams.curselection()]
        for value in values:
            self.wantedParams.insert('1.0', str(value) + '\n')

    def browse_button(self):
        global rootdir
        rootdir = filedialog.askdirectory()
        self.statusLabel['text'] = "Status: Enter desired headers into box above and start search..."

    def getRFfile(self):
        global RFname;
        RFname = filedialog.askopenfilename()
        self.findDCM['state'] = "normal"
        self.statusLabel['text'] = "Status: Enter Working Directory (same as 3DQI)"

    def begin(self):
        # make method to get root dir, RF file, and tag preferences
        self.statusLabel['text'] = "Status: Searching..."
        global filename
        RFfile = pd.read_csv(RFname)
        params = self.wantedParams.get(1.0, "end-1c")
        params = params.split()

        IDs = RFfile["Patient_id"].astype(str).values.tolist()
        tags, tagSt = self.getTagVals(params)
        print(tagSt)
        tagList = self.retrieveDCMH(rootDir=rootdir, IDs=IDs, tags=tags, tagSt=tagSt)
        retFrame = self.matchData(RFfile=RFfile, tagList=tagList, headVals=tagSt)
        filename = rootdir + r"\outDCMHfile.csv"
        retFrame.to_csv(filename,index = False)
        self.openFile['state'] = "normal"

    def retrieveDCMH(self, rootDir, IDs, tags, tagSt):

        IDtag = " +P 0010,0020 "
        IDleft = IDs
        dcmDMP = 'dcmdump.exe'
        retList = []
        for subdir, dirs, files in os.walk(rootDir):
            for file in files:
                curFile = os.path.join(subdir, file)
                if ".dcm" in curFile:
                    print(curFile)
                    filt = dcmDMP + IDtag +'"' + curFile + '"'
                    process = subprocess.Popen(filt, shell=True, stdout=subprocess.PIPE)
                    IDval, err = process.communicate()
                    IDval = IDval.decode("utf-8")
                    try:
                        IDval = IDval[str.index(IDval, "[")+1: str.index(IDval, "]")]
                    except:
                        print(IDval + "ID values not found !")
                        self.statusLabel['text'] = "Status: ID values not found " + str(err)
                    if IDval in IDleft:

                        IDleft.remove(IDval)
                        for tag in tags:
                            concatLen = None
                            index = tags.index(tag)
                            curParam = tagSt[index]
                            tag = tag.strip()
                            if '-' in tag:
                                concatLen = tag[str.index(tag, '-'):]
                                tag = tag[:str.index(tag, '-')]
                            arg = dcmDMP + " " + tag + " " + '"' + curFile + '"'
                            process = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
                            value, err = process.communicate()
                            print(value)
                            if concatLen is not None:
                                retList.append(IDval + "," + curParam + "*" + value.decode("utf-8") + concatLen)
                            else:
                                retList.append(IDval + "," + curParam + "*" + value.decode("utf-8"))
                    break

        return retList

    def getTAGRefVals(self):
        param = []
        tag = open("TAG_REF.txt", "r")
        for line in tag:
            line = str(line)
            param.append(line[0:str.index(line, ",")])

        tag.close()

        return param

    def getTagVals(self, params):
        fileList = []
        code = []
        ourParams = []
        tag = open("TAG_REF.txt", "r")
        for line in tag:
            line = str(line)
            line = line.strip()
            fileList.append(line)


        for param in params:
            if param == "Effective_Dose":
                ourParams.append("Effective_Dose")
                if "Exposure_Time" not in ourParams:
                    ourParams.append("Exposure_Time")
                    code.append(" +P 0018,1150 ")
                if "Current" not in ourParams:
                    ourParams.append("Current")
                    code.append(" +P 0018,1151 ")
            else:
                for s in fileList:
                    if param in s:
                        if param not in ourParams:
                            codeVal = s[str.index(s, ":") + 1:]
                            code.append(" +P " + codeVal + " ")
                            ourParams.append(s[:str.index(s, ",")])
        tag.close()
        return code, ourParams


    def matchData(self, RFfile, headVals, tagList):

        for val in headVals:
            RFfile.insert(loc = 6, column=val, value = "")
            if "Effective_Dose" in val:
                EffCheck = True

        for tag in tagList :
            tag = str(tag)
            print(tag)
            if "[" not in tag:
                ourVal = tag[str.index(tag, "D") + 1:str.index(tag, "#")]
                ourVal = ourVal.strip()
            else:
                ourVal = tag[str.index(tag, "[")+1:str.index(tag, "]")]
                ourVal = ourVal.strip()
            if '-' in tag:
                concatLen = tag[str.index(tag, "-")+1:]
                concatLen = int(concatLen)
                ourVal = ourVal[:-concatLen]

            ID = tag[:str.index(tag, ",")]
            ourRow = RFfile.index[RFfile['Patient_id'] == int(ID)]
            ourCol = tag[str.index(tag, ",")+1: str.index(tag, "*")]
            RFfile.at[ourRow, ourCol] = ourVal

        return RFfile

    def checkDose(self, RFfile, headVals):
        for headVal in headVals:

            if "Effective_Dose" in headVal:
                for ID in RFfile["Patient_id"]:
                    ID = str(ID)
                    print(ID)
                    ourRow = RFfile.index[RFfile['Patient_id'] == int(ID)]
                    ourRow = int(ourRow[0])
                    print(ourRow)
                    current = RFfile.loc[RFfile.index(ourRow), "Current"]
                    print(current)
                    exposure = RFfile.loc[RFfile.index(ourRow), "Exposure_Time"]
                    print(exposure)
                    ourVa = float(current) * float(exposure)

                    RFfile.at[ourRow, "Effective_Dose"] = ourVa

    def openResult(self):
        print(filename)
        os.startfile(filename)




if __name__ == '__main__':
    root = tk.Tk()
    MainApplication(root)
    root.mainloop()