import requests
import tkinter as tk
import tkinter.font as tkFont
from tkinter import filedialog as fd
from tkinter import scrolledtext
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

proxy = ""
combos = ""
configLines = ""
config_file = ""
config_file_parts = ""
combo_file = ""
combo_file_parts = ""
running = False
requestParsing = False
responseParsing = False
threads = []
headers = [{}]
content = [{}]
params = [{}]
urls = []
methods = []
configResponseCookies = []
configRequestCookies = []
requestCount = 0
responseCount = 0
requestIndex = 0
threadcount = 0

chrome_versions = ["120.0.0.0","119.0.0.0","118.0.0.0","117.0.0.0","116.0.0.0","115.0.0.0","114.0.0.0","113.0.0.0","112.0.0.0","111.0.0.0"]

class App:
    def __init__(self, root):
        global startStopButton
        # setting title
        root.title("Newton")
        # setting window size
        width = 1200  # Adjusted width
        height = 800
        screenwidth = root.winfo_screenwidth()
        screenheight = root.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        root.geometry(alignstr)
        root.resizable(width=False, height=False)

        # Create a frame to hold the console output
        console_frame = tk.Frame(root, bg="black")  # Set background color to black
        console_frame.place(x=400, y=0, width=800, height=800)

        # Create a Text widget for console output
        self.console_text = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, width=60, height=20, bg="black", fg="white")
        self.console_text.pack(expand=True, fill="both")

        # Redirect stdout to the Text widget
        sys.stdout = self.ConsoleRedirector(self.console_text)

        proxyButton=tk.Button(root)
        proxyButton["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=10)
        proxyButton["font"] = ft
        proxyButton["fg"] = "#000000"
        proxyButton["justify"] = "center"
        proxyButton["text"] = "Proxy File"
        proxyButton.place(x=0,y=25,width=250,height=150)
        proxyButton["command"] = self.proxyButton_command

        comboButton=tk.Button(root)
        comboButton["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=10)
        comboButton["font"] = ft
        comboButton["fg"] = "#000000"
        comboButton["justify"] = "center"
        comboButton["text"] = "Combo File"
        comboButton.place(x=0,y=225,width=250,height=150)
        comboButton["command"] = self.comboButton_command

        configButton=tk.Button(root)
        configButton["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=10)
        configButton["font"] = ft
        configButton["fg"] = "#000000"
        configButton["justify"] = "center"
        configButton["text"] = "Config File"
        configButton.place(x=0,y=425,width=250,height=150)
        configButton["command"] = self.configButton_command

        startStopButton=tk.Button(root)
        startStopButton["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times',size=10)
        startStopButton["font"] = ft
        startStopButton["fg"] = "#000000"
        startStopButton["justify"] = "center"
        startStopButton["text"] = "Start"
        startStopButton.place(x=0,y=625,width=250,height=150)
        startStopButton["command"] = self.startStopButton_command

    def proxyButton_command(self):
        global proxy
        proxy_file = fd.askopenfilename()
        if proxy_file:
            with open(proxy_file,"r") as proxyfile:
                proxyparts = proxyfile.read().split(":")
                proxyformatted = proxyparts[2]+":"+proxyparts[3]+"@"+proxyparts[0]+":"+proxyparts[1]
                proxy = {"http": f"http://{proxyformatted}"}

    def comboButton_command(self):
        global combos
        global combo_file
        combo_file = fd.askopenfilename()
        if combo_file:
            with open(combo_file, "r") as combofile:
                combos = combofile.read().splitlines()

    def configButton_command(self):
        global configLines
        global config_file
        config_file = fd.askopenfilename()
        if config_file:
            with open(config_file, "r") as combofile:
                configLines = combofile.read().splitlines()

    def startStopButton_command(self):
            global running
            global combo_file
            global proxy
            global config_file
            global requestIndex
            if running:
                running = False
                startStopButton["text"] = "Start"
                requestIndex = 0
            else:
                running = True
                startStopButton["text"] = "Stop"
                parseConfig()
            config_file_parts = config_file.split("/")
            combo_file_parts = combo_file.split("/")
            print("Running: "+str(running)+" "+"\nCombos: "+str(combo_file_parts[-1])+"\nProxy: "+str(proxy)+"\nConfig: "+str(config_file_parts[-1]))

    class ConsoleRedirector:
        def __init__(self, text_widget):
            self.text_widget = text_widget

        def write(self, message):
            self.text_widget.insert(tk.END, message)
            self.text_widget.see(tk.END)  # Auto-scroll to the end
            self.text_widget.update_idletasks()  # Force an update

def request(session,method,url,param,header,content):
    try:
        if method.upper() == "GET":
            response = session.get(url, params=param, headers=header, data=content, proxies=proxy)
        elif method.upper() == "POST":
            response = session.post(url, params=param, headers=header, data=content, proxies=proxy)
    except requests.exceptions.TooManyRedirects:
        print("ERROR: Too many redirects")
    except Exception as e:
        print("ERROR: "+str(e))
    return response

def replacementCheck(item, replacementDictionary):
    for replacement in replacementDictionary:
        if replacement[0] in item:
            return item.replace(replacement[0],replacement[1])

def createReplacementDictionary(*kwargs):
    for kwarg in kwargs:
        if kwarg[0] == "email":
            email = kwarg[1]
        elif kwarg[0] == "password":
            password = kwarg[1]
    returnThis = {
        r"{USER}":email,
        r"{PASS}":password
    }
    return returnThis

def threadFunction(combo):
    global headers
    global params
    global content
    session = requests.session()
    comboParts = combo.split(":")
    username = comboParts[0]
    password = comboParts[1]
    replacementDictionary = createReplacementDictionary(email = username, password = password)
    for header in headers:
        for key,value in header.items():
            headers[header][key] = replacementCheck(value, replacementDictionary)
    print("REPLACED HEADERS: "+headers)

def runThreads():
    global threadcount
    chunk_size = 400
    if threads:
        print("Threads: " + str(len(threads)), end="\r")
    with ThreadPoolExecutor(max_workers=400) as executor:
        # Submit initial chunk of tasks
        futures = [executor.submit(threadFunction, combo) for combo in combos[:chunk_size]]
        threadcount += chunk_size

        while threadcount < len(combos):
            # Wait for any task to complete
            for future in as_completed(futures):
                # Submit a new task with the next combo
                new_future = executor.submit(threadFunction, combos[threadcount])
                threadcount += 1

                # Replace the completed task with the new task in the futures list
                futures[futures.index(future)] = new_future

def parseConfig():
    global configLines
    global running
    global requestParsing
    global responseParsing
    global requestCount
    global responseCount
    global configResponseCookies
    global configRequestCookies
    global requestIndex
    global headers
    global methods
    global urls
    currentCookies = {}
    if configLines and proxy and combos:
        for line in configLines:
            if line == "$REQUEST":
                requestParsing = True
                requestCount += 1
            elif line == "$RESPONSE":
                responseParsing = True
                responseCount += 1
            elif line == "{":
                pass
            elif line == "}":
                if requestParsing:
                    requestParsing = False
                    currentURL = headers[requestIndex]["Host"]+urlEnd
                    urls.append(currentURL)
                    print("URL "+str(requestIndex)+": "+str(urls[requestIndex])+"\n")
                    print("HEADERS "+str(requestIndex)+": "+str(headers[requestIndex])+"\n")
                    try:
                        print("CONTENT "+str(requestIndex)+": "+str(content[requestIndex])+"\n")
                    except:
                        print("CONTENT "+str(requestIndex)+": "+"{}")
                    try:
                        print("PARAMS "+str(requestIndex)+": "+str(params[requestIndex])+"\n")
                    except:
                        print("PARAMS "+str(requestIndex)+": "+"{}")
                    requestIndex += 1
                responseParsing = False
            elif line == "":
                pass
            elif line.startswith("  "):
                if requestParsing:
                    if line.startswith("    GET /"):
                        methods.append("GET")
                        urlEnding = line[9:]
                        urlEnd = (urlEnding.split("?"))[0]
                        urlEnd = urlEnd.replace(" HTTP/1.1","")
                        if "?" in urlEnding:
                            rightHalfQst = (urlEnding.split("?"))[1]
                            urlParamPieces = rightHalfQst.split("&")
                            for piece in urlParamPieces:
                                piece = piece.replace(" HTTP/1.1","")
                                pc = piece.split("=")
                                updateThis = {pc[0]:pc[1]}
                                try:
                                    params[requestIndex].update(updateThis)
                                except:
                                    params.append(updateThis)
                    elif line.startswith("    POST /"):
                        methods.append("POST")
                        urlEnding = line[9:]
                        urlEnd = (urlEnding.split("?"))[0]
                        urlEnd = urlEnd.replace(" HTTP/1.1","")
                        if "?" in urlEnding:
                            rightHalfQst = (urlEnding.split("?"))[1]
                            urlParamPieces = rightHalfQst.split("&")
                            for piece in urlParamPieces:
                                piece = piece.replace(" HTTP/1.1","")
                                pc = piece.split("=")
                                updateThis = {pc[0]:pc[1]}
                                try:
                                    params[requestIndex].update(updateThis)
                                except:
                                    params.append(updateThis)

                    elif line.startswith("    Cookie: "):
                        cookiesString = line[12:]
                        cookieSplits = cookiesString.split("; ")
                        for splits in cookieSplits:
                            equalsSplit = splits.split("=")
                            if len(equalsSplit) > 2:
                                #print("====>2: "+str(equalsSplit))
                                lefthalf = len(equalsSplit)-2
                                appendThisKey = str(equalsSplit[0:lefthalf])
                                appendThisValue = str(equalsSplit[lefthalf:])
                                currentCookies.update({appendThisKey: appendThisValue})
                            elif len(equalsSplit) == 2:
                                #print("====2: "+str(equalsSplit))
                                currentCookies.update({equalsSplit[0]: equalsSplit[1]})
                            elif len(equalsSplit) == 1:
                                #print("====1: "+str(equalsSplit))
                                currentCookies.update({equalsSplit[0]: None})
                            else:
                                #print("====?: "+str(equalsSplit))
                                print("For some reason, the length of equalsSplit is: "+str(len(equalsSplit)))
                        configRequestCookies.append(currentCookies)
                    elif line.startswith("    {") and requestParsing:
                        try:
                            splitUps = line[5:-1].split(",")
                            print("#####splitUps: "+splitUps)
                            for sp in splitUps:
                                splitUp = dict([sp.split(":")])
                                content[requestIndex].update(splitUp)
                        except:
                            content.append({})
                            splitUps = line[5:-1].split(",")
                            for sp in splitUps:
                                splitUp = dict([sp.split(":")])
                                content[requestIndex].update(splitUp)
                    elif ":" in line:
                        try:
                            if headers[requestIndex]:
                                try:
                                    splitUp = dict([line[4:].split(": ")])
                                    headers[requestIndex].update(splitUp)
                                except Exception as e:
                                    print("ERROR: "+str(e))
                            else:
                                headers.append({})
                                splitUp = dict([line[4:].split(": ")])
                                headers[requestIndex].update(splitUp)
                        except:
                            pass
                    elif ("&" in line) and ":" not in line:
                        try:
                            splitUps = line[4:-1].split("&")
                            for sp in splitUps:
                                splitUp = dict([sp.split(":")])
                                content[requestIndex].update(splitUp)
                        except:
                            content.append({})
                            splitUps = line[4:-1].split("&")
                            for sp in splitUps:
                                splitUp = dict([sp.split("=")])
                                content[requestIndex].update(splitUp)
                    else:
                        print(f"ERROR: LINE {line} DIDN'T MATCH ANY OF THE PARSES")
                elif responseParsing:
                    if line.startswith("    Set-Cookie: "):
                        cookiesString = line[16:]
                        cookieSplits = cookiesString.split("; ")
                        for splits in cookieSplits:
                            equalsSplit = splits.split("=")
                            if len(equalsSplit) > 2:
                                #print("====>2: "+str(equalsSplit))
                                lefthalf = len(equalsSplit)-2
                                appendThisKey = str(equalsSplit[0:lefthalf])
                                appendThisValue = str(equalsSplit[lefthalf:])
                                currentCookies.update({appendThisKey: appendThisValue})
                            elif len(equalsSplit) == 2:
                                #print("====2: "+str(equalsSplit))
                                currentCookies.update({equalsSplit[0]: equalsSplit[1]})
                            elif len(equalsSplit) == 1:
                                #print("====1: "+str(equalsSplit))
                                if str(equalsSplit) != " HttpOnly":
                                    currentCookies.update({equalsSplit[0]: None})
                            else:
                                #print("====?: "+str(equalsSplit))
                                print("For some reason, the length of equalsSplit is: "+str(len(equalsSplit)))
                        configResponseCookies.append(currentCookies)
            else:
                print("CONFIG SYNTAX ERROR")
        #print("Config Request Cookies: "+str(configRequestCookies))
        #print("\n\n\n\n\n##############################################\n\n\n\n\n")
        #print("Config Response Cookies: "+str(configResponseCookies))
        #print("\n\n\n\n\n##############################################\n\n\n\n\n")
        runThreads()
    else:
        running = False
        startStopButton["text"] = "Start"

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()