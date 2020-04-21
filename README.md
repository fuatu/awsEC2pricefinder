# awsEC2pricefinder

## Install
tested with Python 3.7

To install requirements, run command:
```
$ pip3 install -r requirements.txt
```

## graphical interface
run without parameters
```
$ python awsEC2pricing.py
```

![alt text](https://i.ibb.co/71wK6Dm/image.png)

## example output from terminal
```
$ python awsEC2pricing.py -t 4 8 Windows 'EU (Ireland)'
Records are up-to-date
--------------------------
 vCPU: 4.00
 RAM: 8.00
 OS: Windows
 Region: EU (Ireland)
--------------------------

t3a.xlarge      vCPU 4.00    RAM 16.00  OS Windows    PriceH 0.23680  PriceM 170.49600
t2.xlarge       vCPU 4.00    RAM 16.00  OS Windows    PriceH 0.24260  PriceM 174.67200
t3.xlarge       vCPU 4.00    RAM 16.00  OS Windows    PriceH 0.25600  PriceM 184.32000
m5a.xlarge      vCPU 4.00    RAM 16.00  OS Windows    PriceH 0.37600  PriceM 270.72000
c5.xlarge       vCPU 4.00    RAM 8.00   OS Windows    PriceH 0.37600  PriceM 270.72000
m5.xlarge       vCPU 4.00    RAM 16.00  OS Windows    PriceH 0.39800  PriceM 286.56000
```

## help output:
```
$ python awsEC2pricing.py -h
----------------------------------
Sample command:
$ python awsEC2pricing.py -t 1 16 Windows 'US East (N. Virginia)'
----------------------------------
 -t                      --> run in terminal
 1                       --> vCPU
 16                      --> RAM
 Windows                 --> OS
 'US East (N. Virginia)' --> Region
----------------------------------
 rename credentials.yaml.example to credentials.yaml and fill your aws key and secret
 your user in AWS needs rights for reading price

----------------------------------
Regions:
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
    US West (Oregon)
----------------------------------
```
