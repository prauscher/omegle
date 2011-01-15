#!/usr/bin/env python

class OmegleIRCConnector(object):
	def __init__(self, irc, chan, omegle):
		self.irc = irc
		self.chan = chan
		self.omegle = omegle
		self.omegle.setHandlers(self.handle_connect, self.handle_post, self.handle_typing, self.handle_disconnect)
		self.omegle.waitForConnected()
	
	def handle_connect(self):
		if self.chan.startswith('#'):
			self.irc.join(self.chan)
		else:
			self.irc.post(self.chan, "*** Connection established")
	
	def handle_post(self, msg):
		self.irc.post(self.chan, msg)
	
	def handle_typing(self):
		pass
	
	def handle_disconnect(self):
		if self.chan.startswith('#'):
			self.irc.leave(self.chan, "Stranger hung up")
		else:
			self.irc.post(self.chan, "*** Connection lost")
	
	def omegle_isConnected(self):
		return self.omegle.isConnected()
	
	def omegle_post(self, msg):
		self.omegle.post(msg)
	
	def omegle_disconnect(self):
		self.omegle.disconnect()
