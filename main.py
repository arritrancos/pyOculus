#!/usr/bin/python
# -*- encoding: utf-8 -*-

try:		
	from indiclient import IndiClient
except:
	print("INDiClient not installed")

import sys
from datetime import datetime, timedelta
from astropy.coordinates import EarthLocation
from astropy.time import Time
import astropy.units as u
from shutil import copyfile
import time
from astroplan import Observer, download_IERS_A

# My libs
from config import OBSERVATORY, INSTR_ID, INSTR_TAG, DATA_DIR, EXP_DAY, EXP_NIGHT, SUNDT, SHOK
import outputs
import check

if SHOK == "yes":
	from sense_hat import SenseHat
	from random import randint
	sensehat = SenseHat()
	sensehat.low_light = True
	shpos = (randint(0,7), randint(0,7))

# TODO: ponerle que si tiene internet, que baje actualizacion
# Tambien que compruebe si es antigua
#download_IERS_A()

def shscreen(value, shpos):
	if SHOK == "yes":
		if value == "ini":
			shpos = ((shpos[0]+1) % 8, (shpos[1]+1) % 8)
			sensehat.set_pixel(shpos[0],shpos[1],0,0,255)
			time.sleep(0.1)
			sensehat.clear()
		elif value == "exp":
			sensehat.set_pixel(shpos[0],shpos[1],0,0,255)
		elif value == "dld":
			sensehat.set_pixel(shpos[0],shpos[1],0,255,0)
		elif value == "day":
			sensehat.show_letter("d",text_colour=(255,255,0))
			time.sleep(5)
			sensehat.clear()
		elif value == False:
			sensehat.clear()
		else:
			sensehat.clear()
	
	return shpos
	

# Take image through INDI
def take_exposure(exptime, filename):
	# instantiate the client
	indiclient=IndiClient(exptime, filename)
	# set indi server localhost and port 7624
	indiclient.setServer("localhost",7624)
	# connect to indi server pause for 2 seconds
	if (not(indiclient.connectServer())):
		 print("No indiserver running on "+indiclient.getHost()+":"+str(indiclient.getPort())+" - Try to run")
		 return False
	time.sleep(1)
	# start endless loop, client works asynchron in background, loop stops after disconnect
	while indiclient.connected:
		time.sleep(0.3)
	indiclient.disconnectServer()
	del indiclient
	return True


# Setting time exposure
def set_exposure(observatory, currenttime):
	sunrise, sunset = rise_set(observatory, currenttime)
	#print(sunrise, sunset, currenttime)
	if observatory.is_night(currenttime):
		if abs(sunrise - currenttime ) < timedelta(seconds=600) or abs(currenttime -sunset) < timedelta(seconds=600):
			exp = EXP_DAY
		elif abs(sunrise - currenttime) < timedelta(seconds=1800) or abs(currenttime -sunset) < timedelta(seconds=1800):
			exp = EXP_NIGHT/10.
		elif abs(sunrise - currenttime) < timedelta(seconds=5400) or (abs(currenttime -sunset) < timedelta(seconds=5400)):
			exp = EXP_NIGHT/2.
		else:
			exp = EXP_NIGHT
	else:
		exp = EXP_DAY
	print("Setting exposure time to %s (%s)" % (exp, sunrise-sunset))
	del sunrise, sunset, observatory, currenttime
	return exp


# Setting Observatory
def set_location():
	lat = OBSERVATORY["lati"]
	lon = OBSERVATORY["long"]
	elev = OBSERVATORY["elev"]
	name = OBSERVATORY["name"]
	timezone = OBSERVATORY["tizo"]
	location = EarthLocation.from_geodetic(lon*u.deg+180*u.deg, lat*u.deg, elev*u.m)
	observatory = Observer(location=location, name=name, timezone=timezone)
	return observatory


# Sunset, Sunrise
def rise_set(observatory, currenttime):
	time = Time(currenttime)
	sunset_tonight = observatory.sun_set_time(time, which='nearest')
	sunrise_tonight = observatory.sun_rise_time(time, which='nearest')
	return (sunrise_tonight.datetime, sunset_tonight.datetime)


# Which night? Change on every midday
def night(currenttime):
	currenthour = float(currenttime.strftime('%H'))+float(currenttime.strftime('%M'))/60.
	if currenthour > 12:
		night8 = currenttime.strftime('%Y%m%d')
	else:
		night8 = (currenttime - timedelta(1)).strftime('%Y%m%d')
	del currenttime
	return night8


# Loop whole night
def loop(observatory, currenttime, night8):
	resp = None
	itsOk = False
	exp = set_exposure(observatory, currenttime)
	now = datetime.utcnow()
	datestamp = now.strftime("%Y%m%dT%H%M%S")
	# Taking a image
	fitsfile = check.check_dir('%s/raw/%s/%s-%s.fits' % (DATA_DIR, night8, INSTR_ID, datestamp))
	resp = take_exposure(exptime=exp, filename=fitsfile)
	# Creating other products from new fits
	if resp:
		parms = {
		'observatory': OBSERVATORY["name"],
		'night': night8,
		'exp': exp,
		'utc': now
		}
		# Make PNG files
		pngfile = check.check_dir('%s/png/%s/%s.png' % (DATA_DIR, night8, datestamp))
		latestpng = check.check_dir('%s/tonight/latest.png' % (DATA_DIR))
		outputs.make_image(parms=parms, fitsfile=fitsfile, pngfile=pngfile)
		copyfile(pngfile, latestpng)
		# Make Jasonfile
		jsonfile = check.check_dir('%s/tonight/latest.json' % (DATA_DIR))
		outputs.make_json(parms, jsonfile)
		print("Saved %s - %s" % (pngfile, datetime.utcnow().isoformat()))
		itsOk = True
	else:
		print("Error!")
		itsOk = False
	del fitsfile, jsonfile, pngfile, latestpng
	del resp
	return itsOk


# MAIN ###################################
if __name__ == '__main__':
	
	observatory = set_location()
	currenttime = datetime.utcnow()
	sunrise, sunset = rise_set(observatory, currenttime)
	night8 = night(currenttime)
	
	# Somethings to check
	test = {
	'datadir': DATA_DIR,
	'usbtag': INSTR_TAG
	}
	
	itsOk = True
	i = 0
	while itsOk == True:
		i += 1
		if i > 10:
			itsOk = False
		shpos=shscreen("ini",shpos)
		# Check prerequisities.
		itsOk, reasons = check.check_prev(test)
		if not itsOk:
			print("ERROR: %s" % " ".join(reasons))
			break
		
		# Check currenttime in range to observe
		if currenttime >= (sunset - timedelta(minutes = SUNDT)) or \
		currenttime <= (sunrise + timedelta(minutes = SUNDT)):
			shpos=shscreen("exp",shpos)
			itsOk = loop(observatory, currenttime, night8)
			shpos=shscreen("dld",shpos)
			#TODO: grabar un fichero status.
			pass
		
		elif currenttime < (sunset - timedelta(minutes = SUNDT)):
			print("Nope yet. Wait.")
			shpos=shscreen("day",shpos)
			time.sleep(60)
			pass
		
		else:
			print("Observation finished!")
			itsOk = False
				
	sys.exit()