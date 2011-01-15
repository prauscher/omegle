#!/usr/bin/env python
# coding: utf-8

from urllib.parse import urlencode
from threading import Thread, Lock
from optparse import OptionParser
import http.client
import json
import time
import random
import socket

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
	
	def readloop(self):
		while True:
			events = self.clientRequestJSON('POST', '/events', urlencode({'id': self.omegleid}))
			if events:
				for event in events:
					if event[0] == 'connected' and self.handler_connect:
								self.connected = True
								self.handler_connect()
					if event[0] == 'gotMessage' and self.handler_post:
								self.handler_post(event[1])
					if event[0] == 'typing' and self.handler_typing:
								self.handler_typing()
					if event[0] == 'strangerDisconnected' and self.handler_disconnect:
								self.connected = False
								self.handler_disconnect()
			time.sleep(2)
	
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

class IRCSession(object):
	def __init__(self, server, port, nickname, username, realname, password):
		self.s = socket.socket()
		self.s.connect((server,port))
		
		print("{0} is connected.".format(self))
		
		self.omegle = {}
		
		if password:
			self.send("PASS {0}".format(password))
		self.send("NICK {0}".format(nickname))
		self.send("USER {0} 127.0.0.1 trolo :{1}".format(username, realname))
		Thread(target=self.readloop).start()
		time.sleep(5)
	
	def send(self, data):
		self.s.send(data.encode('latin-1') + b'\n')
	
	def readloop(self):
		while True:
			buf = self.s.recv(1024).decode('latin-1')
			for line in buf.split('\n'):
				self.parseCommand(line)
	
	def parseCommand(self, line):
		if line == '' or line == None:
			return
		source = line.split(' ', 2)[0]
		msg = ' '.join(line.split(' ', 2)[1:])
		if msg.upper().startswith('PRIVMSG'):
			(cmd, chan) = msg.split(' ')[0:2]
			body = ' '.join(msg.split(' ')[2:])
			if body.startswith(':'): body = body[1:]
			if body.startswith('!'):
				self.parseAdminCommand(chan, body[1:])
			else:
				self.getOmegleSession(chan).omegle_post(body)
	
	def parseAdminCommand(self, chan, admin):
		cmd = admin.split(' ', 2)[0]
		print(cmd)
		if cmd.upper() == 'DISCONNECT':
			self.getOmegleSession(chan).omegle_disconnect()
		elif cmd.upper() == 'OMEGLE':
			if self.getOmegleSession(chan).isConnected():
				self.getOmegleSession(chan).omegle_disconnect()
			self.generateOmegleSession(chan)
		elif cmd.upper() == '':
			pass
	
	def generateOmegleSession(self, chan):
		omegle = OmegleIRCConnector(self, chan, OmegleSession('bajor.omegle.com'))
		print("New Stranger on " + chan)
		self.omegle[chan] = omegle
	
	def getOmegleSession(self, chan):
		if not chan in self.omegle:
			self.generateOmegleSession(chan)
		elif not self.omegle[chan].omegle_isConnected():
			self.generateOmegleSession(chan)
		return self.omegle[chan]
	
	def join(self, chan):
		self.send('JOIN {0}'.format(chan))
		print('{0} joined {1}'.format(self, chan))
	
	def post(self, chan, msg):
		self.send('PRIVMSG {0} :{1}'.format(chan, msg))

class OmegleIRCConnector(object):
	def __init__(self, irc, chan, omegle):
		self.irc = irc
		self.chan = chan
		self.omegle = omegle
		self.omegle.setHandlers(self.handle_connect, self.handle_post, self.handle_typing, self.handle_disconnect)
		self.omegle.waitForConnected()
	
	def handle_connect(self):
		self.irc.post(self.chan, 'Stranger on the line!')
	
	def handle_post(self, msg):
		self.irc.post(self.chan, msg)
	
	def handle_typing(self):
		pass
	
	def handle_disconnect(self):
		self.irc.post(self.chan, 'Stranger disconnected')
	
	def omegle_isConnected(self):
		return self.omegle.isConnected()
	
	def omegle_post(self, msg):
		self.omegle.post(msg)
	
	def omegle_disconnect(self):
		self.omegle.disconnect()

def main():
	irc = IRCSession('irc.libertirc.net', 6667, 'OmegleBot' + str(random.randint(10,99)), 'omegle', 'Der fabulöse OmegleBot', None)
	irc.join('#omegle')

	#for i in range(0,2):
	#	sessions[] = OmegleSession('bajor.omegle.com')
	

if __name__=="__main__": 
	try:
		main()
	except KeyboardInterrupt:
		quit(0)
