"""
AWS EC2 Price Finder Helper Module

This module provides utility functions and constants for the AWS EC2 Price Finder tool.
It handles AWS pricing API interactions, database operations, and various helper functions
for retrieving and managing EC2 instance pricing information.
"""

import json
import sqlite3
from datetime import date
from typing import List, Dict, Tuple, Optional, Any, DefaultDict
from collections import defaultdict
import yaml
import boto3
import requests
from colorama import Fore, Style

# Default configuration values
P_VCPU = 2
P_RAM = 4
P_OS = 'Linux'
DB_NAME = 'awsprices.db'
REGION_NVIRGINIA = 'US East (N. Virginia)'
P_REGION = REGION_NVIRGINIA
DB_RECORD_EXPIRY_DAYS = 7
MAX_RESULTS = 100

# AWS specific constants
AWS_SERVICE_CODE = 'AmazonEC2'
SPOT_ADVISOR_URL = "https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json"

# EC2 filter constants
EC2_FILTERS = {
    'preInstalledSw': 'NA',
    'storage': 'EBS only',
    'productFamily': 'Compute Instance',
    'termType': 'OnDemand',
    'licenseModel': 'No License required',
    'tenancy': 'Shared',
    'capacitystatus': 'Used'
}

# Mapping dictionaries
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
    'EU (Frankfurt)': 'eu-central-1',
    'EU (Ireland)': 'eu-west-1',
    'EU (London)': 'eu-west-2',
    'EU (Paris)': 'eu-west-3',
    'EU (Stockholm)': 'eu-north-1',
    'Middle East (Bahrain)': 'me-south-1',
    'South America (Sao Paulo)': 'sa-east-1'
}

# Available regions and OS options
list_regions = list(region_map.keys())
list_os = list(os_map.keys())

def adapt_date(val: date) -> str:
    """Convert date to string format for SQLite storage."""
    return val.isoformat()

def convert_date(val: str) -> date:
    """Convert string from SQLite to date object."""
    return date.fromisoformat(val.decode())

# Register the adapters with SQLite
sqlite3.register_adapter(date, adapt_date)
sqlite3.register_converter("DATE", convert_date)

class DatabaseManager:
    """Handles all database operations for EC2 pricing data."""
    
    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name
        self.create_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a connection with proper date handling."""
        return sqlite3.connect(
            self.db_name,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )

    def create_db(self) -> None:
        """Create the database and required tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            sql_query = """
                CREATE TABLE IF NOT EXISTS ec2(
                    id INTEGER PRIMARY KEY,
                    instanceType TEXT,
                    vcpu REAL,
                    memory REAL,
                    os TEXT,
                    price REAL,
                    region TEXT,
                    add_date DATE
                )
            """
            cursor.execute(sql_query)
            conn.commit()

    def insert_records(self, records: List[Tuple]) -> None:
        """Insert multiple EC2 pricing records into the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """INSERT INTO ec2(instanceType, vcpu, memory, os, price, region, add_date)
                   VALUES(?, ?, ?, ?, ?, ?, ?)""",
                records
            )
            conn.commit()

    def delete_records(self, region: str) -> None:
        """Delete records for a specific region."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ec2 WHERE region=?", (region,))
            conn.commit()

    def are_records_old(self, region: str) -> bool:
        """Check if records for a region are older than DB_RECORD_EXPIRY_DAYS."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT add_date FROM ec2 WHERE region=? LIMIT 1", (region,))
            result = cursor.fetchone()
            
            if not result:
                return True

            record_date = result[0]  # Now returns a date object directly
            return (date.today() - record_date).days >= DB_RECORD_EXPIRY_DAYS

    def find_ec2(self, cpu: float, ram: float, os: str, region: str, limit: int) -> List[Tuple]:
        """Find EC2 instances matching the specified criteria."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            sql_query = """
                SELECT * FROM ec2
                WHERE vcpu >= ? AND memory >= ?
                AND region = ? AND os = ?
                ORDER BY price LIMIT ?
            """
            cursor.execute(sql_query, (cpu, ram, region, os, limit))
            return cursor.fetchall()

class AWSPricing:
    """Handles AWS pricing API interactions."""

    def __init__(self):
        self.db = DatabaseManager()
        self.credentials = self._load_credentials()

    def _load_credentials(self) -> Dict:
        """Load AWS credentials from yaml file."""
        try:
            with open('credentials.yaml', 'r') as stream:
                return yaml.safe_load(stream)['credentials']
        except (yaml.YAMLError, FileNotFoundError) as e:
            raise Exception("Failed to load credentials: " + str(e))

    def get_boto_clients(self, region: Optional[str] = None) -> Tuple[Any, Any]:
        """Create boto3 clients for pricing and EC2."""
        session = boto3.Session(
            aws_access_key_id=self.credentials['access_key'],
            aws_secret_access_key=self.credentials['secret_key'],
            region_name=region_map.get(region, self.credentials['default_region'])
        )
        return session.client('pricing'), session.client('ec2')

    def get_ec2_pricing(self, region: str = P_REGION) -> None:
        """Fetch and store EC2 pricing information."""
        if not self.db.are_records_old(region):
            print("Records are up-to-date")
            return

        print("Getting price updates for EC2s")
        self.db.delete_records(region)
        pricing, _ = self.get_boto_clients(region)

        filters = [
            {'Type': 'TERM_MATCH', 'Field': key, 'Value': value}
            for key, value in {**EC2_FILTERS, 'location': region}.items()
        ]

        records = []
        next_token = None
        
        while True:
            kwargs = {
                'ServiceCode': AWS_SERVICE_CODE,
                'Filters': filters
            }
            if next_token:
                kwargs['NextToken'] = next_token

            response = pricing.get_products(**kwargs)
            
            for price in response['PriceList']:
                record = self._parse_price_list_item(price, region)
                if record:
                    records.append(record)

            next_token = response.get('NextToken')
            if not next_token:
                break

        self.db.insert_records(records)

    def _parse_price_list_item(self, price: str, region: str) -> Optional[Tuple]:
        """Parse a price list item into a database record."""
        details = json.loads(price)
        try:
            pricedimensions = next(iter(details['terms']['OnDemand'].values()))['priceDimensions']
            pricing_details = next(iter(pricedimensions.values()))
            instance_price = float(pricing_details['pricePerUnit']['USD'])
            
            if instance_price <= 0:
                return None

            attributes = details['product']['attributes']
            return (
                attributes['instanceType'],
                float(attributes['vcpu']),
                float(attributes['memory'].split()[0]),
                attributes['operatingSystem'],
                instance_price,
                region,
                date.today()
            )
        except (KeyError, ValueError, StopIteration):
            return None

    def get_spot_prices(self, instances: List[str], os: str, region: str) -> DefaultDict:
        """Get spot prices for specified instances."""
        _, ec2 = self.get_boto_clients(region)
        results = defaultdict(float)

        for instance in instances:
            try:
                spot = ec2.describe_spot_price_history(
                    InstanceTypes=[instance],
                    MaxResults=1,
                    ProductDescriptions=[os_map[os]]
                )
                if spot['SpotPriceHistory']:
                    results[instance] = float(spot['SpotPriceHistory'][0]['SpotPrice'])
            except (IndexError, KeyError):
                continue

        return results

    def get_spot_interruption_rates(self, instances: List[str], os: str, region: str) -> DefaultDict:
        """Get spot interruption rates for specified instances."""
        results = defaultdict(str)
        rates = {
            0: "<5%",
            1: "5-10%",
            2: "10-15%",
            3: "15-20%",
            4: ">20%"
        }

        try:
            response = requests.get(SPOT_ADVISOR_URL)
            spot_advisor = json.loads(response.text)['spot_advisor']
            
            for instance in instances:
                try:
                    rate = spot_advisor[region][os][instance]['r']
                    results[instance] = rates[rate]
                except (KeyError, IndexError):
                    continue

        except requests.exceptions.RequestException:
            pass

        return results

def print_help() -> None:
    """Print help information to the terminal."""
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
    print(Style.RESET_ALL + "----------------------------------")
    print(Fore.GREEN + "Available Regions:")
    for region in list_regions:
        print(f"  {region}")
    print(Style.RESET_ALL + "----------------------------------")

# Convenience functions that use the classes above
def find_ec2(cpu: float = P_VCPU, ram: float = P_RAM,
             os: str = P_OS, region: str = P_REGION, limit: int = 6) -> List[Tuple]:
    """Find EC2 instances matching the specified criteria."""
    aws_pricing = AWSPricing()
    aws_pricing.get_ec2_pricing(region)
    return aws_pricing.db.find_ec2(cpu, ram, os, region, limit)

def get_ec2_spot_price(instances: List[str], os: str, region: str) -> DefaultDict:
    """Get spot prices for specified instances."""
    aws_pricing = AWSPricing()
    return aws_pricing.get_spot_prices(instances, os, region)

def get_ec2_spot_interruption(instances: List[str], os: str, region: str) -> DefaultDict:
    """Get spot interruption rates for specified instances."""
    aws_pricing = AWSPricing()
    return aws_pricing.get_spot_interruption_rates(instances, os, region)
