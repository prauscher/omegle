#!/usr/bin/env python

import time

class OmegleIRCConnector(object):
	def __init__(self, irc, chan, omegle):
		self.irc = irc
		self.chan = chan
		self.omegle = omegle
		self.omegle.setHandlers(self.handle_connect, self.handle_post, self.handle_typing, self.handle_disconnect)
		self.omegle.waitForConnected()
	
	def debug(self, msg):
		print(time.ctime() + " | " + self.chan + msg)
	
	def handle_connect(self):
		self.debug(" * Connected")
		self.omegle.setTyping(True)
		if self.chan.startswith('#'):
			self.irc.startGame(self.chan)
			self.irc.join(self.chan)
			self.irc.post(self.chan, "*** You're now chatting with a random stranger. Say hi!")
			self.irc.post(self.chan, "*** Answer using " + self.irc.nickname + ": <text>, To change partner use !omegle")
		else:
			self.irc.post(self.chan, "*** Connection established")
	
	def handle_post(self, msg):
		self.debug(" < " + msg)
		if self.irc.hasPlayer(self.chan):
			msg = self.irc.getActivePlayer(self.chan) + ": " + msg
		self.irc.post(self.chan, msg)
		self.omegle.setTyping(True)
	
	def handle_typing(self, typing):
		pass
	
	def handle_disconnect(self):
		self.debug(" * Hung up")
		if self.chan.startswith('#'):
			self.irc.post(self.chan, "*** Your conversational partner has disconnected.")
			self.irc.endGame(self.chan)
			#self.irc.leave(self.chan, "Stranger hung up")
		else:
			self.irc.post(self.chan, "*** Connection lost")
	
	def omegle_isConnected(self):
		return self.omegle.isConnected()
	
	def omegle_post(self, msg):
		self.debug(" > " + msg)
		self.omegle.setTyping(False)
		self.omegle.post(msg)
	
	def omegle_disconnect(self):
		self.debug(" * Disconnect")
		self.irc.post(self.chan, "*** You quit the game.")
		self.irc.endGame(self.chan)
		self.omegle.disconnect()
