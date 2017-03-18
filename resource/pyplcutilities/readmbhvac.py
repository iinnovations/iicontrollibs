#!/usr/bin/env python

from iiutilities.netfun import readMBcodedaddresses

length=38
unitreadlength=24
ipadd = '10.0.1.82'
startadd='41'
statusstart='410800'
onlinestart='000001'

readstatuses = True
if readstatuses:
    # print('reading online statuses')
    # onlinestatuses = readMBcodedaddresses(ipadd,onlinestart,length)
    # print(onlinestatuses)

    print('reading read statuses')
    statuses = readMBcodedaddresses(ipadd,statusstart,length)
    print(statuses)

# print('reading units')
# units = ['15','02','03']
# for unit in units:
#     print('reading unit' + str(unit))
#     address = int(startadd + unit + '01')
#     print('reading address' + str(address))
#     results = readMBcodedaddresses(ipadd,address,unitreadlength)
#     print(results)
   
