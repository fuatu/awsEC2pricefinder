from includes import print_help
from includes import read_yaml
from includes import REGION_NVIRGINIA
from awsEC2pricing import get_sys_argv
from awsEC2pricing import main

def test_print_help():
    assert print_help()

def test_read_yaml():
    # positive test
    filename = 'credentials.yaml'
    assert not read_yaml(filename) is None
    # negative test
    filename = 'credentialsx.yaml'
    assert read_yaml(filename) is None

def test_get_sys_argv_positive():
    success, text_only, pvcpu, pram, pos, pregion = get_sys_argv()
    assert success
    assert not text_only is None
    assert not pvcpu is None
    assert not pram is None
    assert not pos is None
    assert not pregion is None
    # test with parameters
    success, text_only, pvcpu, pram, pos, pregion = get_sys_argv(['','-t','8','16','Linux',REGION_NVIRGINIA])
    assert success
    assert not text_only is None
    assert not pvcpu is None
    assert not pram is None
    assert not pos is None
    assert not pregion is None

def test_get_sys_argv_help():
    # test help
    success, text_only, pvcpu, pram, pos, pregion = get_sys_argv(['', '-h'])
    assert not success

def test_main():
    assert main(testing=True)