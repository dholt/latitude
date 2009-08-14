#!/usr/bin/env python 

import urllib2, urllib, json, cookielib, sys

# needed to get by special cookie attributes
class ForgivingCookieJar(cookielib.CookieJar):
	
	def _cookie_from_cookie_tuple(self, tup, request):
		name, value, standard, rest = tup
		version = standard.get("version", None)
		if version is not None:
			# Some servers add " around the version number, this module expects a pure int.
			standard["version"] = version.strip('"')
			return cookielib.CookieJar._cookie_from_cookie_tuple(self, tup,request)

class GoogleScraper():

	def __init__(self, email, password, lat, lon):
		self.location = {}
		# handlers
		self.proc = urllib2.HTTPCookieProcessor(ForgivingCookieJar())
		self.opener = urllib2.build_opener(self.proc)
		urllib2.install_opener(self.opener)
	
		# login form values
		self.body = urllib.urlencode({'Email': email,
					 'Passwd': password,
					 'service': 'ig',
					 'continue': 'http://www.google.com/ig',
					 'followup': 'http://www.google.com/ig',
					 'submit': 'Sign in',})
		self.lat = lat
		self.lon = lon
	
	def update(self):
		try:
			# log in
			self.opener.open('https://www.google.com/accounts/ServiceLoginAuth',  self.body)
		except urllib2.HTTPError,msg:
			print "Error: ", msg
			exit(1)
	
		try:
			# get device (only one for now)
			data = self.opener.open('https://www.google.com/ig?gl=us').read()
			start = int(data.find("Google Latitude"))
			st = int(data.find("core:core.io:core.iglegacy#", start))
			end = int(data.find("\\x26", st))
			start = int(data.find("st=", st))
			token = data[start:end][3:]
		
			post = urllib.urlencode({
				'OAUTH_SERVICE_NAME': 'google',
				'authz': 'oauth',
				'httpMethod': 'GET',
				'url': 'http://www.google.com/glm/mmap/ig?t=ul&lat=%s&lng=%s&accuracy=10' % (self.lat, self.lon),})
				
			# get location
			post = '%s&st=%s' % (post, token)
			data = self.opener.open('http://lfkq9vbe9u4sg98ip8rfvf00l7atcn3d.ig.ig.gmodules.com/gadgets/makeRequest', post)
		except urllib2.HTTPError,msg:
			print "Error: ", msg
			exit(1)

class MobileMeScraper():

	def __init__(self, email, password):
		self.location = {}
		# handlers
		self.proc = urllib2.HTTPCookieProcessor(ForgivingCookieJar())
		self.opener = urllib2.build_opener(self.proc)
		urllib2.install_opener(self.opener)
	
		# login form values
		self.body = urllib.urlencode({'username': email,
					 'password': password,
					 'returnURL': "aHR0cHM6Ly9zZWN1cmUubWUuY29tL3dvL1dlYk9iamVjdHMvRG9ja1N0YXR1cy53b2Evd2EvdHJhbXBvbGluZT9kZXN0aW5hdGlvblVybD0vYWNjb3VudA%3D%3D",
					 'service': 'DockStatus',
					 'realm': 'primary-me',
					 'cancelURL': 'http://www.me.com/mail',
					 'formID': 'loginForm',
					 'reauthorize': 'Y',
					 'destinationUrl': '/account'})
	
	def locate(self):
		try:
			# log in
			self.opener.open('https://auth.apple.com/authenticate',  self.body)
		except urllib2.HTTPError,msg:
			print "Error: ", msg
			exit(1)
	
		# get secure cookie value
		secureCookie = ''
		for i in self.proc.cookiejar:
			if i.name == 'isc-secure.me.com':
				secureCookie = i.value
	
		# build headers
		headers = [ ("Content-Type", "application/json"),
			    ("Accept","text/javascript, text/html, application/xml, text/xml, */*"),
			    ("X-Requested-With", "XMLHttpRequest"),
			    ("X-Prototype-Version", "1.6.0.3"),
			    ("X-Mobileme-Version", "1.0"),
			    ("X-Mobileme-Isc", secureCookie) ]
		self.opener.addheaders = headers
		
		try:
			# get device (only one for now)
			data = self.opener.open('https://secure.me.com/wo/WebObjects/DeviceMgmt.woa/?lang=en').read()
			start = int(data.find("DeviceMgmt.deviceIdMap"))
			start = int(data.find('=',start))+2
			end = int(data.find(';',start))
			deviceId = data[start:end].strip("'")
		
			# configure post data
			post = "postBody=%s" % json.dumps( {
			'deviceId': deviceId,
			'deviceOsVersion': "7A341",
			} )
		
			# get location
			data = self.opener.open('https://secure.me.com/wo/WebObjects/DeviceMgmt.woa/wa/LocateAction/locateStatus', post)
			self.location = json.load(data)
			return self.location
		except urllib2.HTTPError,msg:
			print "Error: ", msg
			exit(1)

if __name__ == '__main__':
	from config import *
	s = MobileMeScraper(musername, mpassword)
	location = s.locate()

	if 'noLocation' in location and location['noLocation']:
		exit(1)

	g = GoogleScraper(gusername, gpassword, location['latitude'], location['longitude'])
	g.update()

	exit(0)
