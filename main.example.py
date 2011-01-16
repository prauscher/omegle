#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ircsession import IRCSession

irc = IRCSession('irc.example.org', 6667, 'Stranger', 'omegle', 'Der fabulöse OmegleBot', None)
irc.join('#omegle')
