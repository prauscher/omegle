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
		self.admins = ['lutoma','prauscher']
		
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
			source = line.split(' ', 2)[0].lstrip(':').split('!')[0].lower()
			line = ' '.join(line.split(' ', 2)[1:])
		if line.upper().startswith('PRIVMSG'):
			(cmd, chan) = line.split(' ')[0:2]
			if not chan.startswith('#'):
				chan = source
			body = ' '.join(line.split(' ')[2:])
			if body.startswith(':'): body = body[1:]
			
			if body.startswith('!'):
				self.parseAdminCommand(source, chan, body[1:])
			#elif self.hasOmegleSession(chan):
			elif self.hasOmegleSession(chan) and chan.startswith('#') and body.startswith(self.nickname):
				self.getOmegleSession(chan).omegle_post(body[len(self.nickname)+1:].lstrip())
			elif chan.startswith('#') and body.startswith(self.nickname):
				self.post(chan, "No Stranger available! Use !omegle to search for Strangers.")
			elif not chan.startswith('#'):
				self.post(chan, "Hello! Use !omegle to start a new conversation")
			else:
				pass
				#self.post(chan, 'U are talking strange things!')
		elif line.upper().startswith('PING'):
			self.send('PONG ' + line[5:])
	
	def parseAdminCommand(self, sender, chan, admin):
		args = admin.rstrip().split(' ')
		cmd = args.pop(0).strip()
		if cmd.upper() == 'HELP':
			if len(args) > 0:
				subcmd = args.pop(0).upper()
				if subcmd == 'DISCONNECT':
					self.post(chan, " !disconnect   Disconnects the Omegleuser")
				elif subcmd == 'OMEGLE':
					self.post(chan, " !omegle       Start a new game, disconnecting the current user if any")
				elif subcmd == 'SIGNIN':
					self.post(chan, " !signin       Add yourself to the Playerlist. Do not forget to !signout when you are away!")
				elif subcmd == 'SIGNOUT':
					self.post(chan, " !signout      Remove yourself from the Playerlist.")
				elif subcmd == 'PLAYERS':
					self.post(chan, " !players      Show the playerlist in the current channel.")
				elif subcmd == 'JOIN':
					self.post(chan, " !join <c>     Joins channel c. Admin-Privileges required.")
				elif subcmd == 'PART':
					self.post(chan, " !part [c]     Leave channel c, defaulting to current. Admin-Privileges required.")
				elif subcmd == 'QUIT':
					self.post(chan, " !quit         Stop the Bot. Admin-Privileges required.")
				else:
					self.post(chan, "Help for " + subcmd + " not found")
			else:
				self.post(chan, "Available commands: !disconnect, !omegle, !join, !part, !signin, !signout, !players, !quit")
		elif cmd.upper() == 'DISCONNECT':
			if sender in self.admins and len(args) > 0:
				chan = args.pop(0)
			if self.hasOmegleSession(chan):
				self.getOmegleSession(chan).omegle_disconnect()
				self.delOmegleSession(chan)
		elif cmd.upper() == 'OMEGLE':
			if sender in self.admins and len(args) > 0:
				chan = args.pop(0)
			if self.hasOmegleSession(chan) and self.getOmegleSession(chan).omegle_isConnected():
				self.getOmegleSession(chan).omegle_disconnect()
				self.delOmegleSession(chan)
			self.generateOmegleSession(chan)
		elif cmd.upper() == 'JOIN':
			if sender in self.admins and len(args) >= 1:
				self.join(args.pop(0))
		elif cmd.upper() == 'PART':
			if sender in self.admins and len(args) >= 1:
				self.leave(args.pop(0), "Admin forces!")
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
		elif cmd.upper() == 'PLAYERS':
			if not self.hasPlayer(chan):
				self.post(chan, "Keine Spieler Registriert. Freier Chatmodus!")
			else:
				self.post(chan, "Eingetragene Spieler: " + ', '.join(self.player[chan]))
		elif cmd.upper() == 'QUIT':
			if not sender in self.admins:
				self.post(chan, "Troll.")
			else:
				for c in self.omegle:
					self.getOmegleSession(c).omegle_disconnect()
					self.delOmegleSession(c)
				self.send("QUIT")
				sys.exit()
		elif cmd.upper() == '':
			pass
		else:
			self.post(chan, "Command {0} not known!".format(cmd))
