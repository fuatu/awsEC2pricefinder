# awsEC2pricefinder

## Install
tested with Python 3.7

#### Install requirements
To install requirements, run command:
```
$ pip3 install -r requirements.txt
```
#### AWS credentials
Copy credentails.yaml.example to credentails.yaml
Edit it and fill aws key+secret details. 
Your AWS user needs to have IAM rights to read pricing.

## graphical interface
run without parameters
```
$ python awsEC2pricing.py
```

![alt text](https://i.ibb.co/G0vdH9Y/image.png)

## example output from terminal
```
$ python awsEC2pricing.py -t 8 32
Records are up-to-date
--------------------------
 vCPU: 8.00
 RAM: 32.00
 OS: Linux
 Region: US East (N. Virginia)
--------------------------
Instance        vCPU   RAM    OS         PriceH   PriceM      SpotH    SpotM      KillRate
t3a.2xlarge     8.00   32.00  Linux      0.30080  216.57600   0.10610  76.39200   <5%
m6g.2xlarge     8.00   32.00  Linux      0.30800  221.76000   0.00000  0.00000       
t3.2xlarge      8.00   32.00  Linux      0.33280  239.61600   0.16100  115.92000  <5%
m5a.2xlarge     8.00   32.00  Linux      0.34400  247.68000   0.20950  150.84000  15-20%
t2.2xlarge      8.00   32.00  Linux      0.37120  267.26400   0.11850  85.32000   >20%
m5.2xlarge      8.00   32.00  Linux      0.38400  276.48000   0.19390  139.60800  5-10%
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
## Predefined filter conditions 

- preInstalledSw: NA 
- storage: EBS only 
- productFamily: Compute Instance
- termType: OnDemand
- licenseModel: No License 
- requiredcapacitystatus: Used