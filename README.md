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

![alt text](https://i.ibb.co/4WdgTzm/image.png)

## example output from terminal
```
$  python awsEC2pricing.py -t 2 4 
Records are up-to-date
--------------------------
 vCPU: 2.00
 RAM: 4.00
 OS: Linux
 Region: US East (N. Virginia)
--------------------------
Instance        vCPU   RAM    OS         PriceH   PriceM      SpotH    SpotH   
t3a.medium      2.00   4.00   Linux      0.03760  27.07200    0.01140  8.20800
t3.medium       2.00   4.00   Linux      0.04160  29.95200    0.01250  9.00000
t2.medium       2.00   4.00   Linux      0.04640  33.40800    0.01440  10.36800
a1.large        2.00   4.00   Linux      0.05100  36.72000    0.02340  16.84800
t3a.large       2.00   8.00   Linux      0.07520  54.14400    0.02270  16.34400
m6g.large       2.00   8.00   Linux      0.07700  55.44000    0.00000  0.00000
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
