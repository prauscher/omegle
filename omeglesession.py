#!/usr/bin/env python

from urllib.parse import urlencode
from threading import Thread, Lock
import http.client
import json
import time

class OmegleSession():
	"""Omegle session"""
	
	def __init__(self, server):
		self.server = server
		self.lock = Lock()
		self.omegleid = self.clientRequestJSON('POST', '/start?rcs=1')
		self.connected = False
		Thread(target=self.readloop).start()
	
	def setHandlers(self, handler_connect, handler_post, handler_typing, handler_disconnect):
		self.handler_connect = handler_connect
		self.handler_post = handler_post
		self.handler_typing = handler_typing
		self.handler_disconnect = handler_disconnect
	
	def clientRequestJSON(self, method, url, postdata='\r\n', server=''):
		return json.loads(self.clientRequest(method, url, postdata, server))
	
	def clientRequest(self, method, url, postdata='\r\n', server=''):
		if server == '':
			server = self.server
		self.lock.acquire()
		client = http.client.HTTPConnection(server)
		client.request(method, url, postdata, {"Content-Type": "application/x-www-form-urlencoded"});
		resp = client.getresponse()
		cont = resp.read().decode('utf-8')
		self.lock.release()
		return cont

	def readevents(self):
		return self.clientRequestJSON('POST', '/events', urlencode({'id': self.omegleid}))
	
	def readloop(self):
		while not self.isConnected():
			events = self.readevents()
			if events:
				for event in events:
					self.debug(event)
					if event[0] == 'connected':
						self.connected = True
						if self.handler_connect:
							self.handler_connect()
			time.sleep(2)
		while self.isConnected():
			events = self.readevents()
			if events:
				for event in events:
					self.debug(event)
					if event[0] == 'gotMessage' and self.handler_post:
						self.handler_post(event[1])
					elif event[0] == 'typing' and self.handler_typing:
						self.handler_typing(True)
					elif event[0] == 'stoppedTyping' and self.handler_typing:
						self.handler_typing(False)
					elif event[0] == 'strangerDisconnected':
						self.connected = False
						self.wasConnected = False
						self.disconnect()
						if self.handler_disconnect:
							self.handler_disconnect()
			time.sleep(2)
	
	def debug(self, msg):
		pass
		#print(self.omegleid + " | " + time.ctime() + " | " + str(msg))
	
	def post(self, msg):
		self.clientRequest('POST', '/send', urlencode({'id': self.omegleid, 'msg': msg}))
	
	def disconnect(self):
		self.clientRequest('POST', '/disconnect')
		self.connected = False
	
	def isConnected(self):
		return self.connected
	
	def waitForConnected(self):
		# hacky, but works!
		while not self.isConnected():
			time.sleep(1)
