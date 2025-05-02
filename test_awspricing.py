"""
Test suite for AWS EC2 Price Finder
"""

import pytest
import sys
from unittest.mock import patch, MagicMock
from datetime import date
import sqlite3

from includes import (
    DatabaseManager, AWSPricing, print_help,
    REGION_NVIRGINIA, region_map, P_OS,
    find_ec2, get_ec2_spot_price, get_ec2_spot_interruption
)
from awsEC2pricing import (
    main, parse_args, get_burstable_info, 
    print_instance_details, BURSTABLE_INSTANCES,
    MONTHLY_HOURS, INSTANCE_FORMAT
)

# Test data
TEST_INSTANCES = ['t3.medium', 't2.medium', 't3.large', 'm6g.large']
TEST_DB = 'test_awsprices.db'

@pytest.fixture
def db_manager():
    """Fixture for database manager with test database."""
    manager = DatabaseManager(TEST_DB)
    yield manager
    # Cleanup
    import os
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

@pytest.fixture
def aws_pricing():
    """Fixture for AWS pricing with mocked credentials."""
    with patch('includes.yaml.safe_load') as mock_yaml:
        mock_yaml.return_value = {
            'credentials': {
                'access_key': 'test_key',
                'secret_key': 'test_secret',
                'default_region': 'us-east-1'
            }
        }
        yield AWSPricing()

def test_print_help():
    """Test help text printing."""
    assert print_help() is None

def test_database_creation(db_manager):
    """Test database creation and structure."""
    with sqlite3.connect(TEST_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='ec2'
        """)
        assert cursor.fetchone() is not None

def test_database_operations(db_manager):
    """Test database CRUD operations."""
    test_record = ('t3.medium', 2, 4, 'Linux', 0.0416, REGION_NVIRGINIA, date.today())
    db_manager.insert_records([test_record])
    results = db_manager.find_ec2(1, 2, 'Linux', REGION_NVIRGINIA, 1)
    assert len(results) == 1
    assert results[0][1] == 't3.medium'
    db_manager.delete_records(REGION_NVIRGINIA)
    results = db_manager.find_ec2(1, 2, 'Linux', REGION_NVIRGINIA, 1)
    assert len(results) == 0

def test_records_expiry(db_manager):
    """Test record expiry checking."""
    assert db_manager.are_records_old(REGION_NVIRGINIA) is True
    test_record = ('t3.medium', 2, 4, 'Linux', 0.0416, REGION_NVIRGINIA, date.today())
    db_manager.insert_records([test_record])
    assert db_manager.are_records_old(REGION_NVIRGINIA) is False

@patch('includes.boto3.Session')
def test_aws_pricing_initialization(mock_session, aws_pricing):
    """Test AWS pricing initialization."""
    assert aws_pricing.credentials['access_key'] == 'test_key'
    assert aws_pricing.credentials['secret_key'] == 'test_secret'

@patch('includes.requests.get')
def test_spot_interruption_rates(mock_get):
    """Test spot interruption rates retrieval."""
    mock_response = MagicMock()
    mock_response.text = '''{
        "spot_advisor": {
            "us-east-1": {
                "Linux": {
                    "t3.medium": {"r": 0}
                }
            }
        }
    }'''
    mock_get.return_value = mock_response
    rates = get_ec2_spot_interruption(
        instances=['t3.medium'],
        os='Linux',
        region=region_map[REGION_NVIRGINIA]
    )
    assert len(rates) == 1
    assert rates['t3.medium'] == '<5%'

@patch('includes.boto3.Session')
def test_spot_prices(mock_session):
    """Test spot prices retrieval."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_spot_price_history.return_value = {
        'SpotPriceHistory': [{'SpotPrice': '0.0416'}]
    }
    mock_session.return_value.client.return_value = mock_ec2
    prices = get_ec2_spot_price(
        instances=['t3.medium'],
        os=P_OS,
        region=REGION_NVIRGINIA
    )
    assert len(prices) == 1
    assert prices['t3.medium'] == 0.0416

@patch('awsEC2pricing.find_ec2')
@patch('awsEC2pricing.get_ec2_spot_price')
@patch('awsEC2pricing.get_ec2_spot_interruption')
def test_main(mock_interrupt, mock_spot, mock_find):
    """Test main function execution."""
    mock_find.return_value = [
        (1, 't3.medium', 2, 4, 'Linux', 0.0416, REGION_NVIRGINIA, date.today())
    ]
    mock_spot.return_value = {'t3.medium': 0.0416}
    mock_interrupt.return_value = {'t3.medium': '<5%'}
    assert main(testing=True) is True

def test_get_burstable_info():
    """Test the get_burstable_info function for burstable and non-burstable instances."""
    assert get_burstable_info('m5.large') == ""
    for instance, expected in BURSTABLE_INSTANCES.items():
        assert get_burstable_info(instance) == expected

def test_instance_and_header_format():
    """Test HEADER_FORMAT and INSTANCE_FORMAT for correct formatting and columns."""
    from awsEC2pricing import HEADER_FORMAT, INSTANCE_FORMAT
    header = HEADER_FORMAT.format("Instance", "vCPU", "RAM", "OS", "OnDemand", "Monthly", "Spot", "SpotMonthly", "Interruption", "Burst")
    assert "Instance" in header
    assert "Burst" in header
    instance = INSTANCE_FORMAT.format("t3.micro", 2, 4, "Linux", 0.0116, 8.395, 0.0035, 2.555, "<5%", "10%")
    assert "t3.micro" in instance
    assert "10%" in instance
    assert "<5%" in instance
def test_parse_args_invalid_vcpu(monkeypatch):
    """Test parse_args with invalid vCPU argument."""
    from awsEC2pricing import parse_args
    test_argv = ['-t', '-1', '16', 'Linux', REGION_NVIRGINIA]
    monkeypatch.setattr('sys.argv', ['awsEC2pricing.py'] + test_argv)
    with pytest.raises(SystemExit):
        parse_args()

def test_parse_args_invalid_ram(monkeypatch):
    """Test parse_args with invalid RAM argument."""
    from awsEC2pricing import parse_args
    test_argv = ['-t', '8', '-1', 'Linux', REGION_NVIRGINIA]
    monkeypatch.setattr('sys.argv', ['awsEC2pricing.py'] + test_argv)
    with pytest.raises(SystemExit):
        parse_args()

def test_parse_args_help(monkeypatch):
    """Test parse_args with help argument."""
    from awsEC2pricing import parse_args
    test_argv = ['-h']
    monkeypatch.setattr('sys.argv', ['awsEC2pricing.py'] + test_argv)
    with pytest.raises(SystemExit):
        parse_args()

def test_parse_args_no_args(monkeypatch):
    """Test parse_args with no arguments."""
    from awsEC2pricing import parse_args
    test_argv = []
    monkeypatch.setattr('sys.argv', ['awsEC2pricing.py'] + test_argv)
    with pytest.raises(SystemExit):
        parse_args()

def test_adapt_date_and_convert_date():
    """Test adapt_date and convert_date functions."""
    from includes import adapt_date, convert_date
    d = date(2024, 5, 2)
    s = adapt_date(d)
    assert s == "2024-05-02"
    # convert_date expects bytes
    assert convert_date(b"2024-05-02") == d

def test_get_region_code_and_os_description():
    """Test get_region_code and get_os_description functions."""
    from includes import get_region_code, get_os_description
    assert get_region_code("US East (N. Virginia)") == "us-east-1"
    assert get_region_code("Nonexistent") == "Nonexistent"
    assert get_os_description("Linux") == "Linux/UNIX (Amazon VPC)"
    assert get_os_description("OtherOS") == "OtherOS"

def test_awsp_get_boto_clients_invalid_region(monkeypatch):
    """Test get_boto_clients with invalid region fallback."""
    from includes import AWSPricing
    # Patch credentials to avoid file access
    monkeypatch.setattr(AWSPricing, "_load_credentials", lambda self: {
        "access_key": "x", "secret_key": "y", "default_region": "us-east-1"
    })
    ap = AWSPricing()
    pricing, ec2 = ap.get_boto_clients("Nonexistent")
    assert pricing is not None
    assert ec2 is not None

def test_awsp_load_credentials_error(tmp_path, monkeypatch):
    """Test _load_credentials error handling."""
    from includes import AWSPricing
    # Patch open to FileNotFoundError
    monkeypatch.setattr("builtins.open", lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("fail")))
    ap = AWSPricing
    with pytest.raises(Exception):
        ap()._load_credentials()

def test_parse_price_list_item_invalid(monkeypatch):
    """Test _parse_price_list_item with invalid price data."""
    from includes import AWSPricing
    monkeypatch.setattr(AWSPricing, "_load_credentials", lambda self: {
        "access_key": "x", "secret_key": "y", "default_region": "us-east-1"
    })
    ap = AWSPricing()
    # Missing keys
    assert ap._parse_price_list_item("{}", "us-east-1") is None
    # Invalid price
    bad_json = '{"terms": {"OnDemand": {}}, "product": {"attributes": {}}}'
    assert ap._parse_price_list_item(bad_json, "us-east-1") is None

def test_get_spot_prices_handles_exception(monkeypatch):
    """Test get_spot_prices handles exceptions gracefully."""
    from includes import AWSPricing
    monkeypatch.setattr(AWSPricing, "_load_credentials", lambda self: {
        "access_key": "x", "secret_key": "y", "default_region": "us-east-1"
    })
    ap = AWSPricing()
    class FakeEC2:
        def describe_spot_price_history(self, **kwargs):
            raise KeyError("fail")
    monkeypatch.setattr(ap, "get_boto_clients", lambda region: (None, FakeEC2()))
    prices = ap.get_spot_prices(["t3.medium"], "Linux", "us-east-1")
    assert prices["t3.medium"] == 0.0

def test_get_spot_interruption_rates_handles_exception(monkeypatch):
    """Test get_spot_interruption_rates handles exceptions gracefully."""
    from includes import AWSPricing
    monkeypatch.setattr(AWSPricing, "_load_credentials", lambda self: {
        "access_key": "x", "secret_key": "y", "default_region": "us-east-1"
    })
    ap = AWSPricing()
    # Patch requests.get to raise exception
    import requests
    monkeypatch.setattr(requests, "get", lambda url: (_ for _ in ()).throw(requests.exceptions.RequestException("fail")))
    rates = ap.get_spot_interruption_rates(["t3.medium"], "Linux", "us-east-1")
    assert rates["t3.medium"] == ""
