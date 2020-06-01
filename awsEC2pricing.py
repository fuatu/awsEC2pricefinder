

import sys
from colorama import Fore, Style
from includes import HELP_TEXT, list_regions, list_os, find_ec2, get_ec2_spot_price
from includes import get_ec2_spot_interruption, print_help, region_map, PAR_VCPU
from includes import P_RAM, P_OS, P_REGION, REGION_NVIRGINIA
import tkinter as tk
from tkinter import ttk


class MyApplication(tk.Tk):
    """ Class for tkinter user interface """
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
    """ Class for tkinter menu interface """
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
        messagebox.showinfo(title="About", message=HELP_TEXT)

    def about(self):
        from tkinter import messagebox
        messagebox.showinfo(title="About", message="Developed by Fuat Ulugay")

    def exit_app(self):
        self.quit()


class FirstFrame(tk.Frame):
    """ Class for tkinter frame interface """
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
        lato12 = "Lato 12"
        bold = "bold"
        style = ttk.Style(self)
        style.theme_use('classic')
        style.configure(self.white_black, background='white',
                        font=lato12, padding="5", width="8",
                        borderwidth="2", bordercolor="black", relief="groove")
        style.configure(self.black_white, background='black', foreground="white",
                        font=lato12 + " " + bold, padding="5", width="8",
                        borderwidth="2", bordercolor="white", relief="groove")
        style.configure(self.white_green, background='white', foreground="green",
                        font=lato12, padding="5", width="8",
                        borderwidth="2", bordercolor="black", relief="groove")
        style.configure(self.white_red, background='white', foreground="red",
                        font=lato12, padding="5", width="8",
                        borderwidth="2", bordercolor="black", relief="groove")
        style.configure(self.white_black_btn, background='white',font=lato12 + " " + bold)
        style.configure(self.white_black_input, foreground = "black", font=lato12 + " " + bold)
        style.configure(self.white_black_spin, foreground="black", background="white",font=lato12 + " " + bold)
        self.input_ram = tk.DoubleVar()
        self.input_cpu = tk.DoubleVar()
        self.input_region = tk.StringVar()
        self.input_os = tk.StringVar()
        self.results = tk.Text(self, height=8, width=100, relief="groove", borderwidth=2)

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
        instances = [rr[1] for rr in result]
        spot_prices = get_ec2_spot_price(instances=instances, os=os, region=region)
        spot_interrupt_rates = get_ec2_spot_interruption(instances=instances, os=os, region=region_map[region])
        #self.results.tag_add("header","1.0","end")
        self.results.tag_configure("header", foreground="red")
        txt_header = "{0:<15} {1:<6} {2:<6} {3:<10} {4:<8} {5:<11} {6:<8} {7:<10} {8}" \
                  .format("Instance", "vCPU", "RAM", "OS", "PriceH", "PriceM", "SpotH", "SpotM", "KillRate")
        self.results.insert(tk.END,txt_header + "\n", "header")
        for rr in result:
            spotprice_hourly = spot_prices[rr[1]]
            spotprice_monthly = spotprice_hourly*24*30
            kill_rate = spot_interrupt_rates[rr[1]]
            self.results.insert(tk.END,
                "{0: <15} {1:<6.2f} {2:<6.2f} {3: <10} {4:.5f}  {5:<10.5f}  {6:.5f}  {7:<10.5f} {8:<3}\n" \
                .format(rr[1], rr[2], rr[3], rr[4], rr[5], rr[5] * 24 * 30, \
                spotprice_hourly, spotprice_monthly, kill_rate))


def get_sys_argv(pp_args = []):
    """ function for collecting terminal args """
    p_args = pp_args
    text_only = False
    pvcpu = PAR_VCPU
    pram = P_RAM
    pos = P_OS
    pregion =  P_REGION
    if len(p_args) > 1 and p_args[1] == '-t':
        text_only=True
    elif len(p_args) > 1 and p_args[1] == '-h':
        print_help()
        return False, '', '', '', '', ''
    elif len(p_args) > 1:
        print('incorrect parameter check help with -h')
        return False, '', '', '', '', ''

    if len(p_args) > 2:
        try:
            pvcpu = float(p_args[2])
        except ValueError:
            print('Please use an integer or floating number')
            return False, '', '', '', '', ''

    if len(p_args) > 3:
        try:
            pram = float(p_args[3])
        except ValueError:
            print('Please use an integer or floating number')
            return False, '', '', '', '', ''

    if len(p_args) > 4:
        pos = p_args[4]
        if not pos in list_os:
            print("Enter one of the values for os:", list_os )
            return False, '', '', '', '', ''

    if len(p_args) > 5:
        pregion = p_args[5]
        if not pregion in list_regions:
            print("Enter one of the values for regions. Check help with -h")
            return False, '', '', '', '', ''

    return True, text_only, pvcpu, pram, pos, pregion


def main(testing=False):
    """ main function """
    if testing:
        text_only = True
        pp_args = ['','-t','8','16','Linux',REGION_NVIRGINIA]
    else:
        pp_args = sys.argv
    success, text_only, pvcpu, pram, pos, pregion = get_sys_argv(pp_args)
    if not success:
        sys.exit()
    if text_only:
        result = find_ec2(cpu=pvcpu, ram=pram, os=pos, region=pregion, limit=6)
        txt_message = Style.RESET_ALL + "--------------------------\n" + \
                      Fore.GREEN + " vCPU: {0:.2f}\n RAM: {1:.2f}\n OS: {2}\n Region: {3}\n" + \
                      Style.RESET_ALL + "--------------------------"
        print(Fore.GREEN + txt_message.format(pvcpu, pram, pos, pregion))
        txt_header = "{0:<15} {1:<6} {2:<6} {3:<10} {4:<8} {5:<11} {6:<8} {7:<10} {8}" \
                      .format("Instance", "vCPU", "RAM", "OS", "PriceH", "PriceM", "SpotH", "SpotM", "KillRate")
        print(Fore.LIGHTGREEN_EX + txt_header)
        instances = [rr[1] for rr in result]
        spot_prices = get_ec2_spot_price(instances=instances, os=pos, region=pregion)
        spot_interrupt_rates = get_ec2_spot_interruption(instances=instances, os=pos, region=region_map[pregion])
        for rr in result:
            spotprice_hourly = spot_prices[rr[1]]
            spotprice_monthly = spotprice_hourly * 24 * 30
            kill_rate = spot_interrupt_rates[rr[1]]
            print(Fore.GREEN + "{0: <15} {1:<6.2f} {2:<6.2f} {3: <10} {4:.5f}  {5:<10.5f}  {6:.5f}  {7:<10.5f} {8:<3}"
                                .format(rr[1], rr[2], rr[3], rr[4], rr[5], rr[5] * 24 * 30, \
                                spotprice_hourly, spotprice_monthly, kill_rate))
        print(Style.RESET_ALL)
        if testing:
            return True
    else:
        myapp = MyApplication()
        myapp.mainloop()

if __name__ == '__main__':
    main()



