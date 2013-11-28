#!/usr/bin/python

def setrawspilights(enabledlist1, enabledlist2):

    import spidev
    import time

    spi = spidev.SpiDev()
    spi.open(0,1)   # Port 0, CS1

    #enabledlist1 = [0,0,0,0,0,0,0,0]
    #enabledlist2 = [0,0,0,0,0,0,0,0]

    # Notes:
    # Low is on. Cathodes are open drain.
    # This unforunately means we need to initialize
    # to off on start-up. not a huge deal

    # Color LED assignments:
    # list 1:
    # 1 : RGB 2 Green 
    # 2 : RGB 1 Blue 
    # 3 : RGB 1 Red 
    # 4 : RGB 1 Green 
    # 5 : Yellow single color 
    # 6 : Blue single color 
    # 7 : Green single color 
    # 8 : Red single color 

    # list 2:

    # 1 : RGB 4 Blue 
    # 2 : RGB 4 Red 
    # 3 : RGB 4 Green 
    # 4 : RGB 3 Blue 
    # 5 : RGB 3 Red 
    # 6 : RGB 3 Green 
    # 7 : RGB 2 Blue 
    # 8 : RGB 2 Red 

    wordsum1=0
    for index,bit in enumerate(enabledlist1):
        wordsum1+=bit*(bit*2)**index
    print('wordsum1: ' + str(wordsum1))
    wordsum2=0
    for index,bit in enumerate(enabledlist2):
        wordsum2+=bit*(bit*2)**index
    print('wordsum2: ' + str(wordsum2)) 

    spiassign1=255-wordsum1
    spiassign2=255-wordsum2
    #spiassign1=0
    #spiassign2=0

     # Transfer one byte
    resp = spi.xfer2([spiassign1,spiassign2])
    print(resp[0])

def setspilights(lightsettingsarray):
    # RGB1, RGB2, RGB3, RGB4, singlered, singlegreen, singleblue, singleyellow
    RGB1=lightsettingsarray[0]
    print('RGB1')
    print(RGB1)
    RGB2=lightsettingsarray[1]
    RGB3=lightsettingsarray[2]
    RGB4=lightsettingsarray[3]
    singlered=lightsettingsarray[4]
    singlegreen=lightsettingsarray[5]
    singleblue=lightsettingsarray[6]
    singleyellow=lightsettingsarray[7]
   
    enabledlist1=[RGB2[1],RGB1[2],RGB1[0],RGB1[1],singleyellow,singleblue,singlegreen,singlered]
    enabledlist2=[RGB4[2],RGB4[0],RGB4[1],RGB3[2],RGB3[0],RGB3[1],RGB2[2],RGB2[0]]
    setrawspilights(enabledlist1,enabledlist2)

def setspilightsoff():
   setrawspilights([0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0])   

def twitterspilights(delay):
   import time
   settingsarray=[]
   settingsarray.append([[1,0,0],[0,0,0],[0,0,0],[0,0,0],0,0,0,0])
   settingsarray.append([[0,1,0],[0,0,0],[0,0,0],[0,0,0],0,0,0,0])
   settingsarray.append([[0,0,1],[0,0,0],[0,0,0],[0,0,0],0,0,0,0])
   settingsarray.append([[0,0,0],[1,0,0],[0,0,0],[0,0,0],0,0,0,0])
   settingsarray.append([[0,0,0],[0,1,0],[0,0,0],[0,0,0],0,0,0,0])
   settingsarray.append([[0,0,0],[0,0,1],[0,0,0],[0,0,0],0,0,0,0])
   settingsarray.append([[0,0,0],[0,0,0],[1,0,0],[0,0,0],0,0,0,0])
   settingsarray.append([[0,0,0],[0,0,0],[0,1,0],[0,0,0],0,0,0,0])
   settingsarray.append([[0,0,0],[0,0,0],[0,0,1],[0,0,0],0,0,0,0])
   settingsarray.append([[0,0,0],[0,0,0],[0,0,0],[1,0,0],0,0,0,0])
   settingsarray.append([[0,0,0],[0,0,0],[0,0,0],[0,1,0],0,0,0,0])
   settingsarray.append([[0,0,0],[0,0,0],[0,0,0],[0,0,1],0,0,0,0])
   settingsarray.append([[0,0,0],[0,0,0],[0,0,0],[0,0,0],1,0,0,0])
   settingsarray.append([[0,0,0],[0,0,0],[0,0,0],[0,0,0],0,1,0,0])
   settingsarray.append([[0,0,0],[0,0,0],[0,0,0],[0,0,0],0,0,1,0])
   settingsarray.append([[0,0,0],[0,0,0],[0,0,0],[0,0,0],0,0,0,1])
   run=True 
   index=0
   while run==True:
      setspilights(settingsarray[index])
      print('sending')
      print(settingsarray[index])
      time.sleep(delay)
      index+=1
      if index>=len(settingsarray):
          index=0 
if __name__ == '__main__':
   setspilightsoff()
