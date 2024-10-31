"""
Test suite for AWS EC2 Price Finder
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import date
import yaml
import sqlite3

from includes import (
    DatabaseManager, AWSPricing, print_help,
    REGION_NVIRGINIA, region_map, P_OS,
    find_ec2, get_ec2_spot_price, get_ec2_spot_interruption
)
from awsEC2pricing import get_sys_argv, main

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
    
    # Test insert
    db_manager.insert_records([test_record])
    
    # Test query
    results = db_manager.find_ec2(1, 2, 'Linux', REGION_NVIRGINIA, 1)
    assert len(results) == 1
    assert results[0][1] == 't3.medium'  # Check instance type
    
    # Test delete
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

def test_get_sys_argv_positive():
    """Test command line argument parsing - positive cases."""
    success, text_only, pvcpu, pram, pos, pregion = get_sys_argv(
        ['', '-t', '8', '16', 'Linux', REGION_NVIRGINIA]
    )
    assert success
    assert text_only is True
    assert pvcpu == 8
    assert pram == 16
    assert pos == 'Linux'
    assert pregion == REGION_NVIRGINIA

def test_get_sys_argv_help():
    """Test help command line argument."""
    success, *_ = get_sys_argv(['', '-h'])
    assert not success

@pytest.mark.parametrize("args,expected", [
    (['', '-x'], False),  # incorrect parameter
    (['', '-t', 'x'], False),  # incorrect CPU
    (['', '-t', '4', 'x'], False),  # incorrect RAM
    (['', '-t', '4', '8', 'x'], False),  # incorrect OS
    (['', '-t', '4', '8', 'Linux', 'x'], False),  # incorrect region
])
def test_get_sys_argv_negative(args, expected):
    """Test command line argument parsing - negative cases."""
    success, *_ = get_sys_argv(args)
    assert success == expected

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
