#!/usr/bin/env python

from threading import Thread, Lock
import socket
import random
import time
from omegleircconnector import OmegleIRCConnector
from omeglesession import OmegleSession

class IRCSession(object):
	def __init__(self, server, port, nickname, username, realname, password):
		self.s = socket.socket()
		self.s.connect((server,port))
		self.rbuf = self.s.makefile("rb")
		
		self.omegle = {}
		
		if password:
			self.send("PASS {0}".format(password))
		self.send("NICK {0}".format(nickname))
		self.send("USER {0} 127.0.0.1 {1} :{2}".format(username, server, realname))
		Thread(target=self.readloop).start()
		# Wait until MOTD etc gets done
		time.sleep(3)
	
	def send(self, data):
		#print('> ' + data)
		self.s.send(data.encode('utf-8') + b'\n')
	
	def readloop(self):
		while True:
			line = self.rbuf.readline().strip().decode('utf-8')
			#print('< ' + line)
			self.parseCommand(line)
	
	def generateOmegleSession(self, chan):
		omegle = OmegleIRCConnector(self, chan, OmegleSession('bajor.omegle.com'))
		self.omegle[chan] = omegle
	
	def hasOmegleSession(self, chan):
		return chan in self.omegle

	def delOmegleSession(self, chan):
		del self.omegle[chan]

	def getOmegleSession(self, chan):
		if not chan in self.omegle:
			self.generateOmegleSession(chan)
		elif not self.omegle[chan].omegle_isConnected():
			self.omegle[chan].omegle_disconnect()
			self.generateOmegleSession(chan)
		return self.omegle[chan]
	
	def join(self, chan):
		self.send('JOIN {0}'.format(chan))

	def leave(self, chan, reason):
		self.send('PART {0} :{1}'.format(chan, reason))
	
	def post(self, chan, msg):
		self.send('PRIVMSG {0} :{1}'.format(chan, msg))
	
	def parseCommand(self, line):
		if line == '' or line == None:
			return
		if line.startswith(':'):
			source = line.split(' ', 2)[0].lstrip(':')
			sourcenick = source.split('!')[0]
			line = ' '.join(line.split(' ', 2)[1:])
		if line.upper().startswith('PRIVMSG'):
			(cmd, chan) = line.split(' ')[0:2]
			if not chan.startswith('#'):
				chan = sourcenick
			body = ' '.join(line.split(' ')[2:])
			if body.startswith(':'): body = body[1:]
			
			if body.startswith('!'):
				self.parseAdminCommand(chan, body[1:])
			elif self.hasOmegleSession(chan):
				self.getOmegleSession(chan).omegle_post(body)
			else:
				self.post(chan, 'U are talking strange things!')
		elif line.upper().startswith('PING'):
			self.post('PONG ' + line[5:])
	
	def parseAdminCommand(self, chan, admin):
		args = admin.rstrip().split(' ')
		cmd = args.pop(0).strip()
		if cmd.upper() == 'DISCONNECT':
			self.getOmegleSession(chan).omegle_disconnect()
			self.delOmegleSession(chan)
		elif cmd.upper() == 'OMEGLE':
			if len(args) > 0:
				chan = args.pop()
			if self.getOmegleSession(chan).omegle_isConnected():
				self.getOmegleSession(chan).omegle_disconnect()
			self.generateOmegleSession(chan)
		elif cmd.upper() == '':
			pass
		else:
			self.post(chan, "Command {0} not known!".format(cmd))


def main():
	irc = IRCSession('irc.libertirc.net', 6667, 'OmegleBot', 'omegle', 'Der fabulöse OmegleBot', None)
	irc.generateOmegleSession('#omegle')

if __name__=="__main__": 
	try:
		main()
	except KeyboardInterrupt:
		quit(0)
