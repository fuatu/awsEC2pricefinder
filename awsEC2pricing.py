"""
AWS EC2 Price Finder - A tool to find and compare EC2 instance prices including spot instances.
Provides both on-demand and spot pricing information along with interruption rates.
"""

import sys
import argparse
from typing import Tuple, List, Optional, Union, Dict, Any
from colorama import Fore, Style
from includes import (
    list_regions, list_os, find_ec2, get_ec2_spot_price,
    get_ec2_spot_interruption, print_help, region_map,
    P_VCPU, P_RAM, P_OS, P_REGION, REGION_NVIRGINIA,
    get_region_code, get_os_description
)

# Constants
MAX_EC2_RESULTS = 10
HOURS_PER_DAY = 24
DAYS_PER_MONTH = 30
MONTHLY_HOURS = HOURS_PER_DAY * DAYS_PER_MONTH

# Output format templates
HEADER_FORMAT = "{:<15} {:<6} {:<6} {:<10} {:<8} {:<11} {:<8} {:<10} {:<8} {:<10}"
INSTANCE_FORMAT = "{:<15} {:<6.2f} {:<6.2f} {:<10} {:.5f}  {:<10.5f}  {:.5f}  {:<10.5f} {:<8} {:<10}"
SUMMARY_FORMAT = (
    Style.RESET_ALL + "--------------------------\n" +
    Fore.GREEN + " vCPU: {0:.2f}\n RAM: {1:.2f}\n OS: {2}\n Region: {3}\n" +
    Style.RESET_ALL + "--------------------------"
)

# Burstable instance pattern and baseline percentages
# Based on AWS documentation: t3.nano has 5% baseline, t3.micro 10%, etc.
BURSTABLE_INSTANCES = {
    't2.nano': '5%',
    't2.micro': '10%',
    't2.small': '20%',
    't2.medium': '40%',
    't2.large': '60%',
    't2.xlarge': '90%',
    't2.2xlarge': '90%',
    't3.nano': '5%',
    't3.micro': '10%',
    't3.small': '20%',
    't3.medium': '20%',
    't3.large': '30%',
    't3.xlarge': '40%',
    't3.2xlarge': '40%',
    't3a.nano': '5%',
    't3a.micro': '10%',
    't3a.small': '20%',
    't3a.medium': '20%',
    't3a.large': '30%',
    't3a.xlarge': '40%',
    't3a.2xlarge': '40%',
    't4g.nano': '5%',
    't4g.micro': '10%',
    't4g.small': '20%',
    't4g.medium': '20%',
    't4g.large': '30%',
    't4g.xlarge': '40%',
    't4g.2xlarge': '40%',
}

def get_burstable_info(instance_name: str) -> str:
    """
    Returns burstable baseline percentage for given instance if it's a burstable instance.
    
    Args:
        instance_name: The name of the EC2 instance
        
    Returns:
        Baseline percentage as string or empty string if not burstable
    """
    return BURSTABLE_INSTANCES.get(instance_name, "")


def parse_args(testing: bool = False, argv: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Parse command line arguments using argparse for secure handling.
    
    Args:
        testing: Boolean indicating if in test mode
        argv: Optional list of arguments to parse (for testing)
    
    Returns:
        Dictionary containing parsed arguments
    """
    if testing:
        # Return predefined arguments for testing mode
        return {
            'text_only': True, 
            'vcpu': 8.0, 
            'ram': 16.0,
            'os': 'Linux',
            'region': REGION_NVIRGINIA
        }
    
    parser = argparse.ArgumentParser(
        description='AWS EC2 Price Finder - Find and compare EC2 instance prices including spot instances',
        add_help=False  # We'll handle the help manually to keep existing format
    )
    
    # Add arguments
    parser.add_argument('-t', action='store_true', dest='text_only',
                        help='Run in terminal mode')
    parser.add_argument('-h', action='store_true', dest='show_help',
                        help='Show help information')
    parser.add_argument('vcpu', nargs='?', type=float, default=P_VCPU, 
                        help='Number of virtual CPUs')
    parser.add_argument('ram', nargs='?', type=float, default=P_RAM,
                        help='Amount of RAM in GB')
    parser.add_argument('os', nargs='?', default=P_OS, choices=list_os,
                        help='Operating system')
    parser.add_argument('region', nargs='?', default=P_REGION, choices=list_regions,
                        help='AWS region')
    
    # Use provided argv or sys.argv
    args_list = argv if argv is not None else sys.argv[1:]

    if not args_list:
        print('no parameters. Check help with -h')
        sys.exit(1)
        
    if '-h' in args_list:
        print_help()
        sys.exit(0)
        
    args = parser.parse_args(args_list)
    
    # Validate numeric arguments
    if args.vcpu <= 0 or args.vcpu > 128:
        print('vCPU must be a positive number between 1 and 128')
        sys.exit(1)
        
    if args.ram <= 0 or args.ram > 1024:
        print('RAM must be a positive number between 1 and 1024')
        sys.exit(1)
    
    return vars(args)

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
    burstable_info = get_burstable_info(instance)

    print(Fore.GREEN + INSTANCE_FORMAT.format(
        instance, vcpu, ram, os_type, price, price_monthly,
        spot_price, spot_price_monthly, kill_rate, burstable_info
    ))

def main(testing: bool = False) -> Optional[bool]:
    """
    Main function to process EC2 instance pricing information.

    Args:
        testing: Boolean flag for test mode

    Returns:
        Boolean indicating success in test mode, None otherwise
    """
    args = parse_args(testing)
    
    if args['text_only']:
        result = find_ec2(
            cpu=args['vcpu'], 
            ram=args['ram'], 
            os=args['os'], 
            region=args['region'], 
            limit=MAX_EC2_RESULTS
        )
        
        print(Fore.GREEN + SUMMARY_FORMAT.format(
            args['vcpu'], args['ram'], args['os'], args['region']
        ))
        
        print(Fore.LIGHTGREEN_EX + HEADER_FORMAT.format(
            "Instance", "vCPU", "RAM", "OS", "PriceH", "PriceM", "SpotH", "SpotM", "KillRate", "Burstable"
        ))

        instances = [r[1] for r in result]
        spot_prices = get_ec2_spot_price(instances=instances, os=args['os'], region=args['region'])
        spot_interrupt_rates = get_ec2_spot_interruption(
            instances=instances,
            os=args['os'],
            region=get_region_code(args['region'])
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
