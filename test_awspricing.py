from includes import print_help
from includes import read_yaml

def test_print_help():
    assert print_help()

def test_read_yaml():
    # positive test
    filename = 'credentials.yaml'
    assert not read_yaml(filename) is None
    # negative test
    filename = 'credentialsx.yaml'
    assert read_yaml(filename) is None

