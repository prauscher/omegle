#!/usr/bin/env python

from threading import Thread, Lock
import socket
import random
import time
import sys
from omegleircconnector import OmegleIRCConnector
from omeglesession import OmegleSession

class IRCSession(object):
	def __init__(self, server, port, nickname, username, realname, password):
		self.s = socket.socket()
		self.s.connect((server,port))
		self.rbuf = self.s.makefile("rb")
		
		self.omegle = {}
		self.player = {}
		self.nickname = nickname
		
		if password:
			self.send("PASS {0}".format(password))
		self.send("NICK {0}".format(nickname))
		self.send("USER {0} 127.0.0.1 {1} :{2}".format(username, server, realname))
		Thread(target=self.readloop).start()
		# Wait until MOTD etc gets done
		time.sleep(3)
	
	def debug(self, msg):
		#print(msg)
		pass
	
	def send(self, data):
		self.debug(' > ' + data)
		self.s.send(data.encode('utf-8') + b'\n')
	
	def readloop(self):
		while True:
			try:
				line = self.rbuf.readline().strip().decode('utf-8')
				self.debug(' < ' + line)
				self.parseCommand(line)
			except UnicodeDecodeError:
				pass
	
	def generateOmegleSession(self, chan):
		omegle = OmegleIRCConnector(self, chan, OmegleSession('bajor.omegle.com'))
		self.omegle[chan] = omegle
	
	def hasOmegleSession(self, chan):
		return chan in self.omegle

	def delOmegleSession(self, chan):
		del self.omegle[chan]

	def getOmegleSession(self, chan):
		return self.omegle[chan]
	
	def join(self, chan):
		self.send('JOIN {0}'.format(chan))

	def leave(self, chan, reason):
		self.send('PART {0} :{1}'.format(chan, reason))
	
	def post(self, chan, msg):
		for line in msg.split('\n'):
			self.send('PRIVMSG {0} :{1}'.format(chan, line.rstrip()))
	
	def startGame(self, chan):
		if self.hasPlayer(chan) and chan.startswith('#'):
			self.choosePlayer(chan)
	
	def endGame(self, chan):
		if self.hasPlayer(chan) and chan.startswith('#'):
			self.send('MODE {0} -v {1}'.format(chan, self.getActivePlayer(chan)))
	
	def hasPlayer(self, chan):
		return chan in self.player and len(self.player[chan]) > 0
	
	def getActivePlayer(self, chan):
		return self.player[chan][0]
	
	def choosePlayer(self, chan):
		random.shuffle(self.player[chan])
		player = self.getActivePlayer(chan)
		self.post(chan, "Spieler " + player + " ist dran")
		self.send('MODE {0} +v {1}'.format(chan, player))
	
	def parseCommand(self, line):
		if line == '' or line == None:
			return
		if line.startswith(':'):
			source = line.split(' ', 2)[0].lstrip(':').split('!')[0]
			line = ' '.join(line.split(' ', 2)[1:])
		if line.upper().startswith('PRIVMSG'):
			(cmd, chan) = line.split(' ')[0:2]
			if not chan.startswith('#'):
				chan = sourcenick
			body = ' '.join(line.split(' ')[2:])
			if body.startswith(':'): body = body[1:]
			
			if body.startswith('!'):
				self.parseAdminCommand(source, chan, body[1:])
			#elif self.hasOmegleSession(chan):
			elif self.hasOmegleSession(chan) and body.startswith(self.nickname):
				self.getOmegleSession(chan).omegle_post(body[len(self.nickname)+1:].lstrip())
			elif body.startswith(self.nickname):
				self.post(chan, "No Stranger available! Use !omegle to search for Strangers.")
			else:
				pass
				#self.post(chan, 'U are talking strange things!')
		elif line.upper().startswith('PING'):
			self.send('PONG ' + line[5:])
	
	def parseAdminCommand(self, sender, chan, admin):
		args = admin.rstrip().split(' ')
		cmd = args.pop(0).strip()
		if cmd.upper() == 'DISCONNECT':
			self.getOmegleSession(chan).omegle_disconnect()
			self.delOmegleSession(chan)
		elif cmd.upper() == 'OMEGLE':
			if len(args) > 0:
				chan = args.pop()
			if self.hasOmegleSession(chan) and self.getOmegleSession(chan).omegle_isConnected():
				self.getOmegleSession(chan).omegle_disconnect()
				self.delOmegleSession(chan)
			self.generateOmegleSession(chan)
		elif cmd.upper() == 'SIGNIN':
			if not chan in self.player:
				self.player[chan] = []
			if sender in self.player[chan]:
				self.post(chan, "Spieler " + sender + " bereits eingetragen")
			else:
				self.player[chan].append(sender)
				self.post(chan, "Spieler " + sender + " eingetragen")
		elif cmd.upper() == 'SIGNOUT':
			if not chan in self.player:
				self.player[chan] = []
			if not sender in self.player[chan]:
				self.post(chan, "Spieler " + sender + " nicht eingetragen")
			else:
				self.player[chan].remove(sender)
				self.post(chan, "Spieler " + sender + " ausgetragen")
		elif cmd.upper() == 'QUIT':
			if sender == 'prauscher':
				sys.exit()
			else:
				self.post(chan, "Troll.")
		elif cmd.upper() == '':
			pass
		else:
			self.post(chan, "Command {0} not known!".format(cmd))