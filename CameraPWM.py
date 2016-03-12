#######################################################################################################
###IMPORTS
#######################################################################################################
import time
import datetime
import picamera
import threading
import io
from PIL import Image,ImageFont,ImageDraw
import RPi.GPIO as GPIO 
from time import sleep
from random import randint

import pyscope
import mpsizes
import sys
import subprocess
import os, os.path
import re

#######################################################################################################
### VARIABLES
#######################################################################################################

#file = open('/var/www/data.txt', 'r')
#pictureCounter = int(file.read())
#file.close()

simulation = False
takingPicture = False
processPicture = False
img = None
scope = pyscope.pyscope()
 

#######################################################################################################
###CALLBACK FUNCTIONS
#######################################################################################################

def trigger(channel):
  print "-Trigger"
  updateSleepMode()
  global processPicture
  global takingPicture
  global img
  global camera
  if not processPicture:
    takingPicture = True 
    camera.rotation = 0
    camera.vflip = True
    camera.hvlip = True
    camera.resolution = (mpsizes.VGA[0],mpsizes.VGA[1])
    GPIO.output(flashOutPin, True)
    camera.capture('/var/www/imageTemp.jpg',resize=(mpsizes.MPX2[0],mpsizes.MPX2[1]))
    GPIO.output(flashOutPin, False)
    takingPicture = False
    stopPreview()
    sleep(0.01)
    #font = ImageFont.truetype("/var/www/fonts/Amble-Bold.ttf", 20)
    #img = Image.open('/var/www/imageTemp.jpg')
    #draw = ImageDraw.Draw(img)
    #draw.text((10, (mpsizes.MPX2[1]-40)),"J&J Prototypes",(205,133,63),font=font)
    #img.save('/var/www/imageTemp.jpg',"JPEG")
    img = pyscope.pygame.image.load('/var/www/imageTemp.jpg')
    scope.screen.blit(pyscope.pygame.transform.scale(pyscope.pygame.transform.rotate(img,180),(640,480)),(0,0))
    pyscope.pygame.display.update()
    processPicture = True
  else:
    processPicture = False
    startPreview()
  
def flash(channel):
  if(not GPIO.input(channel)):
    print "-Flash"    
  global takingPicture
  if not takingPicture:
     GPIO.output(flashOutPin, not GPIO.input(channel))
def laser(channel):
  if(not GPIO.input(channel)):
    print "-Laser"
  GPIO.output(laserOutPin, not GPIO.input(channel))

def submit(channel):
  print "-Submit"
  updateSleepMode()
  global processPicture
  global img
  if (img == None):
    return
  if processPicture:
    pictureCounter = getCount() + 1
    sleep(0.2)
    filename = '/var/www/pictures/'+ str(pictureCounter) +'.jpg'
    pyscope.pygame.image.save(img, filename)
    file = open('/var/www/data.txt', 'w')
    file.truncate()
    file.write(str(pictureCounter))
    file.close()
    processPicture = False
    startPreview()


#######################################################################################################
###PIN DEFINE
#######################################################################################################
triggerPin = 7
flashPin = 15
laserPin = 23
submitPin = 14

flashOutPin = 4
laserOutPin = 17

redPin = 2
greenPin = 22
bluePin = 3

#######################################################################################################
###SIMULATION VARIABLES
#######################################################################################################


#######################################################################################################
###GPIO INIT
#######################################################################################################
GPIO.setmode(GPIO.BCM)
GPIO.setup(triggerPin, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(flashPin, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(laserPin, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(submitPin, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(flashOutPin, GPIO.OUT)
GPIO.setup(laserOutPin, GPIO.OUT)

GPIO.setup(redPin, GPIO.OUT)
GPIO.setup(greenPin, GPIO.OUT)
GPIO.setup(bluePin, GPIO.OUT)    
#######################################################################################################
###PWM DEFINE
#######################################################################################################
frequency = 100 #Hz
pwmRed = GPIO.PWM(redPin, frequency)
pwmGreen = GPIO.PWM(greenPin, frequency)
pwmBlue = GPIO.PWM(bluePin, frequency)
pwmRed.start(100)
pwmGreen.start(100)
pwmBlue.start(100)

redScale = 1
greenScale = 0.3
blueScale = 0.3

def setRGB(r,g,b):
  global pwmRed
  global pwmGreen
  global pwmBlue
  global redScale
  global blueScale
  global greenScale
  pwmRed.ChangeDutyCycle((100 * r/255)*redScale)
  pwmGreen.ChangeDutyCycle((100 * g/255)*greenScale)
  pwmBlue.ChangeDutyCycle((100 * b/255)*blueScale)  

#######################################################################################################
###CAMERA INIT

camera = picamera.PiCamera()
camera.led = False
camera.sharpness = 0
camera.contrast = 0
camera.brightness = 50
camera.saturation = 30
camera.ISO = 0
camera.exposure_compensation = 0
camera.exposure_mode = 'sports'
camera.meter_mode = 'average'
camera.awb_mode = 'off'
camera.awb_gains = (1.6, 1.9)
camera.video_stabilization = False
camera.image_effect = 'none'
camera.color_effects = None

#original camera
#camera.rotation = 0
#camera.vflip = True
#camera.hflip = True

#######################################################################################################
###GLOBAL FUNCTIONS
#######################################################################################################
def sendRefresh():
  pictureCounter = getCount()
  file = open('/var/www/data.txt', 'w')
  file.truncate()
  file.write(str(pictureCounter) + "_refresh")
  file.close()

def getCount():
  DIR = '/var/www/pictures/'
  return len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])

def getWifiInfo(interface,ESSID):
  # watch -n 1 iwconfig wlan0 |grep -i --color quality
  p = subprocess.Popen('iwconfig wlan0 |grep -i quality', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  out, err = p.communicate()
  outPut = re.findall(r"[\w']+", out)
  try:
    outputQuality = outPut[2]
    outputSignal = outPut[6]
    outputNoise = outPut[10]
  except IndexError:
    outputQuality = '100'
    outputSignal = '100'
    outputNoise = '100'
  
  try:
    qu = int(outputQuality)
    si = int(outputSignal)
    no = int(outputNoise)
  except ValueError:
    qu = 100
    si = 100
    no = 100
  return (qu,si,no)

def updateSleepMode():
  global sleepModeSavedTime
  sleepModeSavedTime = time.time()
  
def startPreview():
  global camera
  scope.screen.fill((0, 0, 0))
  pyscope.pygame.display.update()
  camera.rotation = 90
  camera.vflip = True
  camera.hflip = True
  camera.resolution = (480, 640)
  camera.start_preview()

def stopPreview():
  global camera
  camera.stop_preview()
  
#######################################################################################################
###MAIN PROGRAM
#######################################################################################################
sleepModeTime = 60
sleepModeSavedTime = 0
sleepMode = False
sleepModeFirst = True
tiggerTimeOut = 0
submitTimeOut = 0
laserTimeOut = 0
flashTimeOut = 0
rgbTimer = 0
bounceTime = 0.2
updateTimer = 0.2
countUp = True
counter = 0
submitButtonSendRefreshTime = 3;
submitButtonLastTimeHigh = 0;

try:
  sleepModeSavedTime = time.time()
  startPreview()
  
  while True:
    # if sleepmode
    if(sleepMode):
      #Stop as much as possible
      if(sleepModeFirst):
        stopPreview()
        GPIO.output(flashOutPin,False)
        GPIO.output(laserOutPin,False)
        sleepModeFirst = False
        pwmRed.stop()
        pwmGreen.stop()
        pwmBlue.stop()
        
      #Start every thing  
      if(GPIO.input(triggerPin) == GPIO.LOW or GPIO.input(laserPin) == GPIO.LOW or GPIO.input(submitPin) == GPIO.LOW or GPIO.input(flashPin) == GPIO.LOW ):
        startPreview()
        pwmRed.start(100)
        pwmGreen.start(100)
        pwmBlue.start(100)
        sleepModeFirst = True
        sleepMode = False
        updateSleepMode()
      #updatelast high time refresh function otherwise allways refresh after sleepmode
      submitButtonLastTimeHigh = time.time()
      
      #Delay to unload processor
      sleep(0.2)
      
    else:
      #update sleepmode
      if(time.time() - sleepModeSavedTime>sleepModeTime):
        sleepMode = True
      
      # readInputs
      laser(laserPin)
      flash(flashPin)
       
      if(GPIO.input(submitPin) == GPIO.LOW):
        if((time.time() - submitButtonLastTimeHigh) > submitButtonSendRefreshTime):
          sendRefresh()
          submitButtonLastTimeHigh = time.time()
          setRGB(255,255,255)
      else:
        submitButtonLastTimeHigh = time.time()
        
      if((GPIO.input(triggerPin) == GPIO.LOW) and ((time.time()-tiggerTimeOut)>bounceTime)):
        tiggerTimeOut = time.time()
        trigger(triggerPin)
      elif((GPIO.input(submitPin) == GPIO.LOW) and ((time.time()-submitTimeOut)>bounceTime)):
        submitTimeOut = time.time()
        submit(submitPin)
        
      # set rgb val
      if((time.time()-rgbTimer )>updateTimer):
        rgbTimer = time.time()
        quality,signal,noise = getWifiInfo("wlan0","PiWiFi")
        #print quality,signal,noise
        if(signal>50):
          rood = ((100.00-signal)/50.00)*255
          groen = 255.00
          blauw = (255.00*noise/100)
        else:
          rood = 255
          groen1 = (signal-20.00)/50.00*255.00
          if(groen1>=0):
            groen = groen1
          else:
            groen  = 0
          #print groen
          blauw = int((255.00*noise/100.00))
        #print rood,groen,blauw
        setRGB(rood*(quality/100.00),groen*(quality/100.00),blauw*(quality/100.00))
         
        
except KeyboardInterrupt:
    pass
# CLOSE CLEANLY AND EXIT
pyscope.pygame.quit()
pwmRed.stop()
pwmGreen.stop()
pwmBlue.stop()
GPIO.cleanup()