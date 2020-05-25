import json
import sqlite3
from datetime import date
from collections import defaultdict

PAR_VCPU = 2
P_RAM = 4
REGION_NVIRGINIA = 'US East (N. Virginia)'
P_REGION = REGION_NVIRGINIA
P_OS = 'Linux'
DB_NAME = 'awsprices.db'

AVAILABILITY_ZONE = ""
REGIONS = \
    '''
        US East (N. Virginia)
        EU (Ireland)
        Asia Pacific (Hong Kong)
        Asia Pacific (Mumbai)
        Asia Pacific (Osaka - Local)
        Asia Pacific (Seoul)
        Asia Pacific (Singapore)
        Asia Pacific (Sydney)
        Asia Pacific (Tokyo)
        Canada(Central)
        EU (Frankfurt)
        EU (London)
        EU (Paris)
        EU (Stockholm)
        Middle East (Bahrain)
        South America (Sao Paulo)
        US East (Ohio)
        US West (Los Angeles)
        US West (N. California)
        US West (Oregon)'''

help_text = "Here are the default filter conditions:\n\n" + \
            "preInstalledSw: NA\n" + \
            "storage: EBS only\n" + \
            "productFamily: Compute Instance\n" + \
            "termType: OnDemand\n" + \
            "licenseModel: No License required" + \
            "capacitystatus: Used"

list_regions = [
            REGION_NVIRGINIA,
            REGION_NVIRGINIA,
            'EU (Ireland)',
            'Asia Pacific (Hong Kong)',
            'Asia Pacific (Mumbai)',
            'Asia Pacific (Osaka - Local)',
            'Asia Pacific (Seoul)',
            'Asia Pacific (Singapore)',
            'Asia Pacific (Sydney)',
            'Asia Pacific (Tokyo)',
            'Canada(Central)',
            'EU (Frankfurt)',
            'EU (London)',
            'EU (Paris)',
            'EU (Stockholm)',
            'Middle East (Bahrain)',
            'South America (Sao Paulo)',
            'US East (Ohio)',
            'US West (Los Angeles)',
            'US West (N. California)',
            'US West (Oregon)'
        ]

list_os = [
            'Linux',
            'Linux',
            'RHEL',
            'SUSE',
            'Windows',
        ]

os_map = {
    'Linux': 'Linux/UNIX (Amazon VPC)',
    'SUSE': 'SUSE Linux (Amazon VPC)',
    'Windows': 'Windows (Amazon VPC)',
    'RHEL': 'Red Hat Enterprise Linux'
}

region_map = {
    'US East (Ohio)': 'us-east-2',
    'US East (N. Virginia)': 'us-east-1',
    'US West (N. California)': 'us-west-1',
    'US West (Oregon)': 'us-west-2',
    'Asia Pacific (Hong Kong)': 'ap-east-1',
    'Asia Pacific (Mumbai)': 'ap-south-1',
    'Asia Pacific (Osaka-Local)': 'ap-northeast-3',
    'Asia Pacific (Seoul)': 'ap-northeast-2',
    'Asia Pacific (Singapore)': 'ap-southeast-1',
    'Asia Pacific (Sydney)': 'ap-southeast-2',
    'Asia Pacific (Tokyo)': 'ap-northeast-1',
    'Canada (Central)': 'ca-central-1',
    'China (Beijing)': 'cn-north-1',
    'China (Ningxia)': 'cn-northwest-1',
    'Europe (Frankfurt)': 'eu-central-1',
    'EU (Ireland)': 'eu-west-1',
    'Europe (London)': 'eu-west-2',
    'Europe (Paris)': 'eu-west-3',
    'Europe (Stockholm)': 'eu-north-1',
    'Middle East (Bahrain)': 'me-south-1',
    'South America (Sao Paulo)': 'sa-east-1'
}

def print_help():
    from colorama import Fore, Style
    print("----------------------------------")
    print(Fore.GREEN + "Sample command:\n$ python awsEC2pricing.py -t 1 16 Windows 'US East (N. Virginia)'")
    print(Style.RESET_ALL + "----------------------------------")
    print(Fore.GREEN + " -t                      --> run in terminal")
    print(" 1                       --> vCPU")
    print(" 16                      --> RAM")
    print(" Windows                 --> OS")
    print(" 'US East (N. Virginia)' --> Region")
    print(Style.RESET_ALL + "----------------------------------")
    print(Fore.GREEN + " rename credentials.yaml.example to credentials.yaml and fill your aws key and secret")
    print(" your user in AWS needs rights for reading price")
    print(Style.RESET_ALL)
    print("----------------------------------")
    print(Fore.GREEN + "Regions:")
    print(REGIONS)
    print(Style.RESET_ALL + "----------------------------------")
    return True


def read_yaml(filename=None):
    import yaml

    stream = open(filename, 'r')
    try:
        file_details = yaml.safe_load(stream)
    except yaml.YAMLError:
        print("Not yaml file...")
        return None
    return file_details


def pricing_boto(region=None):
    import boto3
    filename = 'credentials.yaml'
    file_details = read_yaml(filename=filename)
    if region is None:
        l_region = file_details['credentials']['default_region']
    else:
        l_region = region_map[region]
    session = boto3.Session(
        aws_access_key_id=file_details['credentials']['access_key'],
        aws_secret_access_key=file_details['credentials']['secret_key'],
        region_name=l_region,
    )
    return session.client('pricing'), session.client('ec2')


def find_ec2(cpu=PAR_VCPU, ram=P_RAM, os='Linux', region=P_REGION, limit=6):
    get_ec2_pricing(region=region)
    con = sqlite3.connect(DB_NAME)
    cobj = con.cursor()
    sql_query = "SELECT * FROM ec2 WHERE vcpu>=? AND memory>=? AND region=? AND os=? ORDER BY price LIMIT " + str(limit)
    cobj.execute(sql_query, (cpu, ram, region, os))
    result = cobj.fetchall()
    cobj.close()
    con.close()
    return result


def get_ec2_pricing(region=P_REGION):
    if are_records_old(region=region):
        print("Getting price updates for EC2s")
        delete_records(region)
    else:
        print("Records are up-to-date")
        # print_prices_from_db()
        return
    pricing, ec2s = pricing_boto(region=P_REGION)
    dt_today = date.today()
    next_token = ''
    while next_token is not None:
        response = pricing.get_products(
            ServiceCode='AmazonEC2',
            Filters=[
                {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
                {'Type': 'TERM_MATCH', 'Field': 'storage', 'Value': 'EBS only'},
                {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Compute Instance'},
                {'Type': 'TERM_MATCH', 'Field': 'termType', 'Value': 'OnDemand'},
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region},
                {'Type': 'TERM_MATCH', 'Field': 'licenseModel', 'Value': 'No License required'},
                {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'}
            ],
            NextToken=next_token
            # use MaxResults=100 for limiting the results if needed
        )
        try:
            next_token = response['NextToken']
        except KeyError:
            next_token = None
        records = []
        for price in response['PriceList']:
            details = json.loads(price)
            pricedimensions = next(iter(details['terms']['OnDemand'].values()))['priceDimensions']
            pricing_details = next(iter(pricedimensions.values()))
            instance_price = float(pricing_details['pricePerUnit']['USD'])
            if instance_price <= 0:
                continue
            instance_type = details['product']['attributes']['instanceType']
            vcpu = details['product']['attributes']['vcpu']
            memory = details['product']['attributes']['memory'].split(" ")[0]
            os = json.loads(price)['product']['attributes']['operatingSystem']
            line = (instance_type, vcpu, memory, os, instance_price, region, dt_today)
            records.append(line)
        insert_records(rc=records)


def are_records_old(region=P_REGION):
    create_db()
    con = sqlite3.connect(DB_NAME)
    cobj = con.cursor()
    sql_query = "SELECT add_date FROM ec2 WHERE region=? LIMIT 1"
    cobj.execute(sql_query, (region,))
    result = cobj.fetchall()
    cobj.close()
    con.close()
    if not result:
        return True
    year = int(result[0][0].split("-")[0])
    month = int(result[0][0].split("-")[1])
    day = int(result[0][0].split("-")[2])
    rec_date = date(year, month, day)
    difference = date.today() - rec_date
    if int(difference.days) >= 7:
        return True
    return False


def delete_records(region: str):
    con = sqlite3.connect(DB_NAME)
    cobj = con.cursor()
    cobj.execute("DELETE FROM ec2 WHERE region=?", (region,))
    con.commit()
    cobj.close()
    con.close()


def insert_records(rc: []):
    con = sqlite3.connect(DB_NAME)
    cobj = con.cursor()
    for rr in rc:
        cobj.execute(
            "INSERT into ec2(instanceType, vcpu, memory, os, price, region, add_date) VALUES(?, ?, ?, ?, ?, ?, ?)", rr)
    con.commit()
    cobj.close()
    con.close()

def print_services():
    pricing, ec2s = pricing_boto()
    print("All Services")
    print("============")
    response = pricing.describe_services()
    for service in response['Services']:
        print(service['ServiceCode'] + ": " + ", ".join(service['AttributeNames']))
    print()

def ec2_attributes():
    pricing, ec2s = pricing_boto()
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
    con = sqlite3.connect(DB_NAME)
    c_obj = con.cursor()
    sql_query = "SELECT * FROM ec2"
    c_obj.execute(sql_query)
    result = c_obj.fetchall()
    c_obj.close()
    con.close()
    if result == []:
        print("No records")
    print("Selected EC2 Products")
    print("=====================")
    for rr in result:
        print("{0: <4} Instance Type: {1: <14} \tvCPU: {2: <4} \tmemory: {3: <5} \tos: {4: <8} \tprice {5}".format(
            rr[0], rr[1], rr[2], rr[3], rr[4], rr[5]))

def get_ec2_ondemand_price(instances=[], os=None, region="None") -> defaultdict(None):
    pricing, ec2s = pricing_boto(region=region)
    results = defaultdict(None)
    for ii in instances:
        try:
            spot = ec2s.describe_spot_price_history(InstanceTypes=[ii, ], MaxResults=1,
                                                    ProductDescriptions=[os_map[os]])
            results[ii] = float(spot['SpotPriceHistory'][0]['SpotPrice'])
        except (IndexError,KeyError) as _:
            results[ii] = 0
    return results

def get_ec2_spot_price(instances=[], os=None, region="None") -> defaultdict(None):
    pricing, ec2s = pricing_boto(region=region)
    results = defaultdict(None)
    for ii in instances:
        try:
            spot = ec2s.describe_spot_price_history(InstanceTypes=[ii, ], MaxResults=1,
                                                    ProductDescriptions=[os_map[os]])
            results[ii] = float(spot['SpotPriceHistory'][0]['SpotPrice'])
        except (IndexError,KeyError) as _:
            results[ii] = 0
    return results


def get_ec2_spot_interruption(instances=[], os=None, region=None) -> defaultdict(None):
    import requests
    import json
    results = defaultdict(None)
    url_interruptions = "https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json"
    try:
        response = requests.get(url=url_interruptions)
        spot_advisor = json.loads(response.text)['spot_advisor']
    except requests.exceptions.ConnectionError:
        return
    rates = {
        0: "<5%",
        1: "5-10%",
        2: "10-15%",
        3: "15-20%",
        4: ">20%"
    }
    for ii in instances:
        try:
            rate = spot_advisor[region][os][ii]['r']
            results[ii] = rates[rate]
        except (IndexError,KeyError):
            results[ii] = ""
    return results

def create_db():
    con = sqlite3.connect(DB_NAME)
    c_obj = con.cursor()
    # create table if does not exist
    sql_query =  "CREATE TABLE IF NOT EXISTS " \
                 "ec2(id INTEGER PRIMARY KEY, instanceType TEXT, vcpu REAL, memory REAL, " \
                 "os TEXT, price REAL, region TEXT, add_date DATE)"
    c_obj.execute(sql_query)
    con.commit()
    c_obj.close()
    con.close()