

import sys
from colorama import Fore, Style
from includes import *
import tkinter as tk
from tkinter import ttk


class MyApplication(tk.Tk):
    """Hello World Main Application"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Find best pricing for AWS")
        self.iconbitmap('favicon.icns')
        self.resizable(width=False, height=False)
        self.fr = FirstFrame(self, bg="White")
        self.fr.grid(padx=10, pady=10, sticky=tk.E + tk.W + tk.N + tk.S)
        self.columnconfigure(0, weight=1)

        menubar = MyMenu(self)
        self.config(menu=menubar)


class MyMenu(tk.Menu):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        filemenu = tk.Menu(self, tearoff=0)
        filemenu.add_command(label="Exit", command=self.exit_app)
        self.add_cascade(label="File", menu=filemenu)

        helpmenu = tk.Menu(self, tearoff=0)
        helpmenu.add_command(label="Fiilter conditions", command=self.conditions)
        helpmenu.add_command(label="About...", command=self.about)
        self.add_cascade(label="Help", menu=helpmenu)


    def conditions(self):
        from tkinter import messagebox
        messagebox.showinfo(title="About", message=help_text)

    def about(self):
        from tkinter import messagebox
        messagebox.showinfo(title="About", message="Developed by Fuat Ulugay")

    def exit_app(self):
        self.quit()


class FirstFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.regions = list_regions
        self.os = list_os
        # create the theme and styles
        self.black_white = 'F2.TLabel'
        self.white_black = 'F1.TLabel'
        self.white_green = 'F3.TLabel'
        self.white_red = 'F4.TLabel'
        self.white_black_btn = 'F1.TButton'
        self.white_black_input = 'F1.TEntry'
        self.white_black_spin = 'F1.TSpinbox'
        style = ttk.Style(self)
        style.theme_use('classic')
        style.configure(self.white_black, background='white',
                        font="Lato 12", padding="5", width="8",
                        borderwidth="2", bordercolor="black", relief="groove")
        style.configure(self.black_white, background='black', foreground="white",
                        font="Lato 12 bold", padding="5", width="8",
                        borderwidth="2", bordercolor="white", relief="groove")
        style.configure(self.white_green, background='white', foreground="green",
                        font="Lato 12", padding="5", width="8",
                        borderwidth="2", bordercolor="black", relief="groove")
        style.configure(self.white_red, background='white', foreground="red",
                        font="Lato 12", padding="5", width="8",
                        borderwidth="2", bordercolor="black", relief="groove")
        style.configure(self.white_black_btn, background='white',font="Lato 12 bold")
        style.configure(self.white_black_input, foreground = "black", font="Lato 12 bold")
        style.configure(self.white_black_spin, foreground="black", background="white",font="Lato 12 bold")
        self.input_ram = tk.DoubleVar()
        self.input_cpu = tk.DoubleVar()
        self.input_region = tk.StringVar()
        self.input_os = tk.StringVar()
        self.results = tk.Text(self, height=7, width=100, relief="groove", borderwidth=2)

        self.ec2_details()

    def ec2_details(self):
        # CPU
        lbl_cpu = ttk.Label(self, text="CPU", style=self.black_white)
        lbl_cpu.grid(padx=5, row=0, column=0, sticky=tk.W)
        in_cpu = ttk.Spinbox(self, style=self.white_black_spin, textvariable=self.input_cpu,
                             from_=0.5, to=256.0, increment=.5, justify=tk.CENTER, width=3)
        in_cpu.grid(row=0, column=1, sticky=tk.W)
        # RAM
        lbl_ram = ttk.Label(self, text="RAM", style=self.black_white)
        lbl_ram.grid(padx=5,row=1, column=0, sticky=tk.W)

        in_ram = ttk.Spinbox(self, style=self.white_black_spin, textvariable=self.input_ram,
                             from_=1, to=256.0, increment=1, justify=tk.CENTER, width=3)
        in_ram.grid(row=1, column=1, sticky=tk.W)
        # Region
        lbl_region = ttk.Label(self, text="Region", style=self.black_white)
        lbl_region.grid(padx=5, row=2, column=0, sticky=tk.W)
        drpdwn_region = ttk.OptionMenu(self, self.input_region, *self.regions)
        drpdwn_region.grid(row=2, column=1, sticky=tk.W)
        # Os
        lbl_os = ttk.Label(self, text="OS", style=self.black_white)
        lbl_os.grid(padx=5, row=3, column=0, sticky=tk.W)
        drpdwn_os = ttk.OptionMenu(self, self.input_os, *self.os)
        drpdwn_os.grid(row=3, column=1, sticky=tk.W)

        find = ttk.Button(self, text="Find EC2", style=self.white_black_btn, command=self.find_ec2s)
        find.grid(padx=5, row=3, column=2, sticky=tk.W)
        self.results.grid(row=4, column=0, sticky=tk.W, columnspan=4)


    def find_ec2s(self):
        limit=6
        cpu = self.input_cpu.get()
        ram = self.input_ram.get()
        os = self.input_os.get()
        region = self.input_region.get()
        result = find_ec2(cpu=cpu, ram=ram, os=os, region=region, limit=limit)
        for i in range(limit):
            self.results.delete(str(i + 1) + ".0", tk.END)
        for rr in result:
            self.results.insert(tk.END,
                                "{0: <15} vCPU {1:<6.2f}  RAM {2:<6.2f} OS {3: <10} PriceH {4:.5f}  PriceM {5:.5f}\n"
                                .format(rr[1], rr[2], rr[3], rr[4], rr[5], rr[5] * 24 * 30))



def create_db():
    con = sqlite3.connect('awsprices.db')
    cObj = con.cursor()
    # create table if does not exist
    sql_query =  "CREATE TABLE IF NOT EXISTS " \
                 "ec2(id INTEGER PRIMARY KEY, instanceType TEXT, vcpu REAL, memory REAL, " \
                 "os TEXT, price REAL, region TEXT, add_date DATE)"
    cObj.execute(sql_query)
    con.commit()
    cObj.close()
    con.close()



def print_services():
    pricing = pricing_boto()
    print("All Services")
    print("============")
    response = pricing.describe_services()
    for service in response['Services']:
        print(service['ServiceCode'] + ": " + ", ".join(service['AttributeNames']))
    print()

def EC2_attributes():
    pricing = pricing_boto()
    print("Selected EC2 Attributes & Values")
    print("================================")
    response = pricing.describe_services(ServiceCode='AmazonEC2')
    attrs = response['Services'][0]['AttributeNames']

    for attr in attrs:
        response = pricing.get_attribute_values(ServiceCode='AmazonEC2', AttributeName=attr)

        values = []
        for attr_value in response['AttributeValues']:
            values.append(attr_value['Value'])

        print("  " + attr + ": " + ", ".join(values))





def print_prices_from_db():
    con = sqlite3.connect('awsprices.db')
    cObj = con.cursor()
    sql_query = "SELECT * FROM ec2"
    cObj.execute(sql_query)
    result = cObj.fetchall()
    cObj.close()
    con.close()
    if result == []:
        print("No records")
    print("Selected EC2 Products")
    print("=====================")
    for rr in result:
        print("{0: <4} Instance Type: {1: <14} \tvCPU: {2: <4} \tmemory: {3: <5} \tos: {4: <8} \tprice {5}".format(
            rr[0], rr[1], rr[2], rr[3], rr[4], rr[5]))


if len(sys.argv) > 1:
    if sys.argv[1] == '-t':
        text_only=True
    if sys.argv[1] == '-h':
        print_help()
else:
    text_only = False

if len(sys.argv) > 2:
    pvcpu = float(sys.argv[2])

if len(sys.argv) > 3:
    pram = float(sys.argv[3])

if len(sys.argv) > 4:
    pos = sys.argv[4]

if len(sys.argv) > 5:
    pregion = sys.argv[5]


if text_only:
    limit = 6
    result = find_ec2(cpu=pvcpu, ram=pram, os=pos, region=pregion, limit=6)
    txt_message = Style.RESET_ALL + "--------------------------\n" + \
                  Fore.GREEN + " vCPU: {0:.2f}\n RAM: {1:.2f}\n OS: {2}\n Region: {3}\n" + \
                  Style.RESET_ALL + "--------------------------\n"
    print(Fore.GREEN + txt_message.format(pvcpu, pram, pos, pregion))
    for rr in result:
        print(Fore.GREEN + "{0: <15} vCPU {1:<6.2f}  RAM {2:<6.2f} OS {3: <10} PriceH {4:.5f}  PriceM {5:.5f}"
                            .format(rr[1], rr[2], rr[3], rr[4], rr[5], rr[5] * 24 * 30))
    print(Style.RESET_ALL)
else:
    myapp = MyApplication()
    myapp.mainloop()


