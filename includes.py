import json
import sqlite3
from datetime import date

pvcpu = 2
pram = 4
pregion = 'US East (N. Virginia)'
pos = 'Linux'
db_name = 'awsprices.db'

txt_regions = \
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
            'US East (N. Virginia)',
            'US East (N. Virginia)',
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
    print(txt_regions)
    print(Style.RESET_ALL + "----------------------------------")
    exit()


def read_yaml(filename=None):
    import yaml

    stream = open(filename, 'r')
    try:
        file_details = yaml.safe_load(stream)
    except yaml.YAMLError:
        print("Not yaml file...")
        return None
    return file_details


def pricing_boto():
    import boto3
    filename = 'credentials.yaml'
    file_details = read_yaml(filename=filename)

    session = boto3.Session(
        aws_access_key_id=file_details['credentials']['access_key'],
        aws_secret_access_key=file_details['credentials']['secret_key'],
        region_name=file_details['credentials']['default_region'],
    )
    return session.client('pricing')


def find_ec2(cpu=pvcpu, ram=pram, os='Linux', region=pregion, limit=6):
    get_ec2_pricing(region=region)
    con = sqlite3.connect(db_name)
    cobj = con.cursor()
    sql_query = "SELECT * FROM ec2 WHERE vcpu>=? AND memory>=? AND region=? AND os=? ORDER BY price LIMIT " + str(limit)
    cobj.execute(sql_query, (cpu, ram, region, os))
    result = cobj.fetchall()
    cobj.close()
    con.close()
    return result


def get_ec2_pricing(region=pregion):
    if are_records_old(region=region):
        print("Getting price updates for EC2s")
        delete_records(region)
    else:
        print("Records are up-to-date")
        # print_prices_from_db()
        return
    pricing = pricing_boto()
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
            # MaxResults=100
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


def are_records_old(region=pregion):
    con = sqlite3.connect(db_name)
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
    con = sqlite3.connect(db_name)
    cobj = con.cursor()
    cobj.execute("DELETE FROM ec2 WHERE region=?", (region,))
    con.commit()
    cobj.close()
    con.close()


def insert_records(rc: []):
    con = sqlite3.connect(db_name)
    cobj = con.cursor()
    for rr in rc:
        cobj.execute(
            "INSERT into ec2(instanceType, vcpu, memory, os, price, region, add_date) VALUES(?, ?, ?, ?, ?, ?, ?)", rr)
    con.commit()
    cobj.close()
    con.close()
