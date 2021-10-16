import sys
from colorama import Fore, Style
from includes import list_regions, list_os, find_ec2, get_ec2_spot_price
from includes import get_ec2_spot_interruption, print_help, region_map, P_VCPU
from includes import P_RAM, P_OS, P_REGION, REGION_NVIRGINIA
ec2_limit = 10


def get_sys_argv(pp_args=[]):
    """ function for collecting terminal args """
    p_args = pp_args
    text_only = False
    pvcpu = P_VCPU
    pram = P_RAM
    pos = P_OS
    pregion = P_REGION
    if len(p_args) == 1:
        print('no parameters. Check help with -h')
        return False, '', '', '', '', ''
    elif len(p_args) > 1 and p_args[1] == '-t':
        text_only = True
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
        if pos not in list_os:
            print("Enter one of the values for os:", list_os)
            return False, '', '', '', '', ''

    if len(p_args) > 5:
        pregion = p_args[5]
        if pregion not in list_regions:
            print("Enter one of the values for regions. Check help with -h")
            return False, '', '', '', '', ''

    return True, text_only, pvcpu, pram, pos, pregion


def main(testing=False):
    """ main function """
    if testing:
        pp_args = ['', '-t', '8', '16', 'Linux', REGION_NVIRGINIA]
    else:
        pp_args = sys.argv
    success, text_only, pvcpu, pram, pos, pregion = get_sys_argv(pp_args)
    if not success:
        sys.exit()
    if text_only:
        result = find_ec2(cpu=pvcpu, ram=pram, os=pos, region=pregion, limit=ec2_limit)
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
                                .format(rr[1], rr[2], rr[3], rr[4], rr[5], rr[5] * 24 * 30,
                                spotprice_hourly, spotprice_monthly, kill_rate))
        print(Style.RESET_ALL)
        if testing:
            return True


if __name__ == '__main__':
    main()
