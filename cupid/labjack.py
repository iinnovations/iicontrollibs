#!/usr/bin/python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2016, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"


def readU6(registers):

    import u6
    from utilities.utility import gettimestring
    device = u6.U6()

    resultslist = []
    for register in registers:
        try:
            value = device.readRegister(register)
            status = 0
        except:
            value = NaN
            status = 1

        resultslist.append({'register':register, 'value':value, 'status':status, 'time': gettimestring()})

    return resultslist


def readU6Analog(positiveChannel, resolutionIndex=0, gainIndex=0, settlingFactor=0, differential=False):

    """
    Name: U6.getAIN(positiveChannel, resolutionIndex = 0, gainIndex = 0,
                    settlingFactor = 0, differential = False)
    Args: positiveChannel, the positive channel to read from
          resolutionIndex, the resolution index.  0 = default, 1-8 = high-speed
                           ADC, 9-12 = high-res ADC (U6-Pro only).
          gainIndex, the gain index.  0=x1, 1=x10, 2=x100, 3=x1000,
                     15=autorange.
          settlingFactor, the settling factor.  0=Auto, 1=20us, 2=50us,
                          3=100us, 4=200us, 5=500us, 6=1ms, 7=2ms, 8=5ms,
                          9=10ms.
          differential, set to True for differential reading.  Negative
                        channel is positiveChannel+1.
    Desc: Reads an AIN and applies the calibration constants to it.

    >>> myU6.getAIN(14)
    299.87723471224308

    strRanges = ["+/- 10", "+/- 1", "+/- 0.1", "+/- 0.01"]

    """
    from utilities.utility import gettimestring
    import u6
    result = {}
    device = u6.U6()
    result['readtime'] = gettimestring()
    try:
        device.getCalibrationData()
        result['value'] = device.getAIN(positiveChannel, resolutionIndex, gainIndex, settlingFactor, differential)
    except:
        #handle stuff ...
        pass
    device.close()

    return result


def readU6Counter(counternumber=0):

    """
    We need to see what state the counter IO is in. If it's already a counter, we just read it.
    If it is not yet a counter, we instantiate it and return count of 0

    Also, this is not safe when other timer and counter inputs are used. For now, this is just one singular counter
    """

    import u6
    from utilities.utility import gettimestring
    device = u6.U6()

    result = {'readtime':gettimestring()}

    # When passed no argument, just reads.
    currentconfig = device.configIO()
    try:
        if not currentconfig['Counter0Enabled']:
            device.configIO(EnableCounter0=True)
            reset = True
        else:
            reset = False

        result['value'] = device.getFeedback(u6.Counter(counter=0, Reset=reset))[0]

    except:
        pass
        # Error handling ....

    device.close()

    return result

if __name__ == "__main__":
    readU6()