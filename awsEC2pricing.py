"""
AWS EC2 Price Finder - A tool to find and compare EC2 instance prices including spot instances.
Provides both on-demand and spot pricing information along with interruption rates.
"""

import sys
from typing import Tuple, List, Optional, Union
from colorama import Fore, Style
from includes import (
    list_regions, list_os, find_ec2, get_ec2_spot_price,
    get_ec2_spot_interruption, print_help, region_map,
    P_VCPU, P_RAM, P_OS, P_REGION, REGION_NVIRGINIA
)

# Constants
MAX_EC2_RESULTS = 10
HOURS_PER_DAY = 24
DAYS_PER_MONTH = 30
MONTHLY_HOURS = HOURS_PER_DAY * DAYS_PER_MONTH

# Output format templates
HEADER_FORMAT = "{:<15} {:<6} {:<6} {:<10} {:<8} {:<11} {:<8} {:<10} {:<8}"
INSTANCE_FORMAT = "{:<15} {:<6.2f} {:<6.2f} {:<10} {:.5f}  {:<10.5f}  {:.5f}  {:<10.5f} {:<3}"
SUMMARY_FORMAT = (
    Style.RESET_ALL + "--------------------------\n" +
    Fore.GREEN + " vCPU: {0:.2f}\n RAM: {1:.2f}\n OS: {2}\n Region: {3}\n" +
    Style.RESET_ALL + "--------------------------"
)


def get_sanitized_args(testing: bool) -> List[str]:
    """
    Get and sanitize command line arguments.
    
    Args:
        testing: Boolean indicating if in test mode
    
    Returns:
        List of sanitized command line arguments
    """
    if testing:
        return ['', '-t', '8', '16', 'Linux', REGION_NVIRGINIA]
    
    # Create a copy of sys.argv to avoid modifying the original
    args = sys.argv.copy()
    
    # Sanitize and validate each argument
    sanitized_args = []
    for arg in args:
        # Remove any potentially dangerous characters
        cleaned_arg = ''.join(c for c in str(arg) if c.isalnum() or c in '.-_')
        sanitized_args.append(cleaned_arg)
    
    return sanitized_args

def get_sys_argv(pp_args: List[str]) -> Tuple[bool, bool, float, float, str, str]:
    """
    Parse and validate command line arguments.

    Args:
        pp_args: List of command line arguments

    Returns:
        Tuple containing:
        - success: Boolean indicating if parsing was successful
        - text_only: Boolean for text-only output
        - vcpu: Number of virtual CPUs
        - ram: Amount of RAM in GB
        - os: Operating system
        - region: AWS region

    Raises:
        ValueError: If numeric arguments cannot be parsed
    """
    if len(pp_args) == 1:
        print('no parameters. Check help with -h')
        return False, False, 0, 0, '', ''

    if pp_args[1] == '-h':
        print_help()
        return False, False, 0, 0, '', ''

    text_only = pp_args[1] == '-t'
    if not text_only and pp_args[1] != '-h':
        print('incorrect parameter check help with -h')
        return False, False, 0, 0, '', ''

    # Default values
    vcpu, ram = P_VCPU, P_RAM
    os_type, region = P_OS, P_REGION

    # Parse vCPU
    if len(pp_args) > 2:
        try:
            vcpu = float(pp_args[2])
        except ValueError:
            print('Please use an integer or floating number for vCPU')
            return False, False, 0, 0, '', ''

    # Parse RAM
    if len(pp_args) > 3:
        try:
            ram = float(pp_args[3])
        except ValueError:
            print('Please use an integer or floating number for RAM')
            return False, False, 0, 0, '', ''

    # Parse OS
    if len(pp_args) > 4:
        os_type = pp_args[4]
        if os_type not in list_os:
            print("Enter one of the values for os:", list_os)
            return False, False, 0, 0, '', ''

    # Parse Region
    if len(pp_args) > 5:
        region = pp_args[5]
        if region not in list_regions:
            print("Enter one of the values for regions. Check help with -h")
            return False, False, 0, 0, '', ''

    return True, text_only, vcpu, ram, os_type, region

def print_instance_details(
    result_row: tuple,
    spot_price: float,
    kill_rate: str
) -> None:
    """
    Print formatted instance details including pricing information.

    Args:
        result_row: Tuple containing instance information from find_ec2
        spot_price: Hourly spot price
        kill_rate: Instance interruption rate
    """
    instance = result_row[1]  # Instance name is at index 1
    vcpu = result_row[2]      # vCPU is at index 2
    ram = result_row[3]       # RAM is at index 3
    os_type = result_row[4]   # OS is at index 4
    price = result_row[5]     # Price is at index 5

    spot_price_monthly = spot_price * MONTHLY_HOURS
    price_monthly = price * MONTHLY_HOURS

    print(Fore.GREEN + INSTANCE_FORMAT.format(
        instance, vcpu, ram, os_type, price, price_monthly,
        spot_price, spot_price_monthly, kill_rate
    ))

def main(testing: bool = False) -> Optional[bool]:
    """
    Main function to process EC2 instance pricing information.

    Args:
        testing: Boolean flag for test mode

    Returns:
        Boolean indicating success in test mode, None otherwise
    """
    pp_args = get_sanitized_args(testing)
    success, text_only, vcpu, ram, os_type, region = get_sys_argv(pp_args)

    if not success:
        sys.exit()

    if text_only:
        result = find_ec2(cpu=vcpu, ram=ram, os=os_type, region=region, limit=MAX_EC2_RESULTS)
        print(Fore.GREEN + SUMMARY_FORMAT.format(vcpu, ram, os_type, region))
        
        print(Fore.LIGHTGREEN_EX + HEADER_FORMAT.format(
            "Instance", "vCPU", "RAM", "OS", "PriceH", "PriceM", "SpotH", "SpotM", "KillRate"
        ))

        instances = [r[1] for r in result]
        spot_prices = get_ec2_spot_price(instances=instances, os=os_type, region=region)
        spot_interrupt_rates = get_ec2_spot_interruption(
            instances=instances,
            os=os_type,
            region=region_map[region]
        )

        for row in result:
            print_instance_details(
                row,
                spot_prices[row[1]],
                spot_interrupt_rates[row[1]]
            )

        print(Style.RESET_ALL)
        if testing:
            return True

if __name__ == '__main__':
    main()
