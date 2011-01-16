#!/usr/bin/env python

class OmegleIRCConnector(object):
	def __init__(self, irc, chan, omegle):
		self.irc = irc
		self.chan = chan
		self.omegle = omegle
		self.omegle.setHandlers(self.handle_connect, self.handle_post, self.handle_typing, self.handle_disconnect)
		self.omegle.waitForConnected()
	
	def debug(self, msg):
		print(self.chan + msg)
	
	def handle_connect(self):
		self.debug(" * Connected")
		if self.chan.startswith('#'):
			self.irc.startGame(self.chan)
			self.irc.join(self.chan)
			self.irc.post(self.chan, "You're now chatting with a random stranger. Say hi!")
			self.irc.post(self.chan, "Antworten mit " + self.irc.nickname + ": <text>, Neuer Chatpartner: !omegle")
		else:
			self.irc.post(self.chan, "*** Connection established")
	
	def handle_post(self, msg):
		self.debug(" < " + msg)
		if self.irc.hasPlayer(self.chan):
			msg = self.irc.getActivePlayer(self.chan) + ": " + msg
		self.irc.post(self.chan, msg)
	
	def handle_typing(self, typing):
		pass
	
	def handle_disconnect(self):
		self.debug(" * Hung up")
		if self.chan.startswith('#'):
			self.irc.endGame(self.chan)
			#self.irc.leave(self.chan, "Stranger hung up")
			self.irc.post(self.chan, "Your conversational partner has disconnected.")
		else:
			self.irc.post(self.chan, "*** Connection lost")
	
	def omegle_isConnected(self):
		return self.omegle.isConnected()
	
	def omegle_post(self, msg):
		self.debug(" > " + msg)
		self.omegle.post(msg)
	
	def omegle_disconnect(self):
		self.debug(" * Disconnect")
		self.irc.endGame(self.chan)
		self.omegle.disconnect()
