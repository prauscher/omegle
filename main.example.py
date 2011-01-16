#!/usr/bin/env python

from ircsession import IRCSession

irc = IRCSession('irc.example.org', 6667, 'Stranger', 'omegle', 'Der fabulöse OmegleBot')
irc.join('#omegle')