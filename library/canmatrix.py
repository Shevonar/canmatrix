#!/usr/bin/env python

#Copyright (c) 2013, Eduard Broecker 
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice, this list of conditions and the
#    following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#    following disclaimer in the documentation and/or other materials provided with the distribution.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
#WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
#PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
#DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
#OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
#DAMAGE.

import cPickle as pickle
import json

class BotschaftenListe:
	def __init__(self):
		self._liste = []

	def addSignalToLastBotschaft(self, signal):
		self._liste[len(self._liste)-1].addSignal(signal)
	def addBotschaft(self, botschaft):
		self._liste.append(botschaft)
		return self._liste[len(self._liste)-1]

	def byId(self, Id):
		for test in self._liste:
			if test._Id == int(Id):
				return test
		return 0
	def byName(self, Name):
		for test in self._liste:
			if test._name == Name:
				return test
		return None
		
class BoardUnit:
	def __init__(self,name):
		self._name = name.strip()
		self._attributes = {}
	def addAttribute(self, attribute, value):
		 self._attributes[attribute]=value

class BoardUnitListe:
	def __init__(self):
		self._liste = []
	def add(self,BU):
		self._liste.append(BU)
	def byName(self, name):
		for test in self._liste:
			if test._name == name:
				return test
		return 0

class Signal:
	def __init__(self, name, startbit, signalsize, byteorder, valuetype, factor, offset, min, max, unit, reciever, multiplex=None):
		self._name = name
		self._startbit = int(startbit)
		self._signalsize = int(signalsize)
		self._byteorder = int(byteorder)
		# byteorder: 1: Intel, 0: Motorola
		self._valuetype = valuetype
		self._factor = float(factor)
		self._offset = float(offset)
		self._min = float(min)
		self._max = float(max)
		self._reciever = reciever
		self._attributes = {}
		self._values = {}
		self._unit = unit
		self._comment = ""
		self._multiplex = multiplex
	def addComment(self, comment):
		self._comment = comment
	def addAttribute(self, attribute, value):
		self._attributes[attribute]=value
	def addValues(self, value, valueName):
		self._values[int(value)] = valueName
	def dump(self):
		return json.dumps({"name": self._name, "startbit" : self._startbit, "signalsize": self._signalsize} )		
		# if hasattr(self, '_comment'):

class Botschaft:
	def __init__(self,bid, name, size, transmitter): 
		self._Id = int(bid)
		self._name = name
		if transmitter is not None:
			self._Transmitter = [transmitter]
		else:
			self._Transmitter = []
		self._Size = int(size)
		self._signals = []
		self._attributes = {}
		self._Reciever = []
		self._extended = 0
		self._comment = ""

	def addSignal(self, signal):
		self._signals.append(signal)
		return self._signals[len(self._signals)-1]

	def addTransmitter(self, transmitter):
		if transmitter not in self._Transmitter:
			self._Transmitter.append(transmitter)
		
	def signalByName(self, name):
		for signal in self._signals:
			if signal._name == name:
				return signal
		return 0
	def addAttribute(self, attribute, value):
		self._attributes[attribute]=value
		
	def addComment(self, comment):
		self._comment = comment


class CanMatrix:
	def __init__(self):
		self.ContentLines = []
		self._attributes = {}
		self._BUs = BoardUnitListe()
		self._bl = BotschaftenListe()

	def getRawValues(self, botschaftID, botschaftData):
		botschaft = self._bl.byId(botschaftID)
		length = int(botschaft._Size)
		bv = BitVector( size = 0 )		
		dummyBv = BitVector( size = 8 )		
		for i in range(0, length):					
			bv += ( BitVector(intVal = botschaftData[i]) | dummyBv )	
		
		for signal in botschaft._signals:
			startBit = int(signal._startbit)
			endBit = int(signal._startbit)+int(signal._signalsize)			
			rawValue = int(bv[startBit:endBit])		
			physicalValue = rawValue * float(signal._factor) + float(signal._offset)
			symbolValue = ""			
			if rawValue in signal._values:
				symbolValue = signal._values[rawValue]
			print signal._name + " " + str(rawValue) + " " + str(physicalValue) + " " + symbolValue
 
	def addAttribute(self, attribute, value):
		 self._attributes[attribute]=value

def loadPkl(filename):
        pkl_file = open(filename, 'rb')
        db1 = pickle.load(pkl_file)
        pkl_file.close()
        return db1

def savePkl(db, filename):
        output = open(filename, 'wb')
        pickle.dump(db, output)
        output.close()

def putSignalValueInFrame(startbit, len, format, value, frame):
	if format == 1: # Intel
		lastbit = startbit + len
		firstbyte = startbit/8-1
		lastbyte = (lastbit-1)/8
		# im lastbyte mit dem msb anfangen
		# im firstbyte mit dem lsb aufhoeren
		for i in range(lastbyte, firstbyte, -1):
			if lastbit %8 != 0:
				nbits = lastbit % 8
			else:
				nbits = min(len, 8)
			nbits = min(len, nbits)
				
			start = lastbit-1 - int((lastbit-1)/8)*8
			end = lastbit-nbits - int((lastbit-nbits)/8)*8
			
			len -= nbits
			mask = (0xff >> 7-start) << end
			mask &= 0xff;
			frame[i] |= (((value >> len ) << end) & mask)
			lastbit = startbit + len
	else: # Motorola
		firstbyte = startbit/8
		bitsInfirstByte = startbit % 8 + 1 
		restnBits = len - bitsInfirstByte
		lastbyte = firstbyte + restnBits/8
		if restnBits %8 > 0:
			lastbyte += 1
		restLen = len
		nbits = bitsInfirstByte
		for i in range(firstbyte, lastbyte+1):
			end = 0
			if restLen < 8:
				end = 8-restLen
			mask = (0xff >> (8-nbits)) << end
			restLen -= nbits
			frame[i] |= ((value >> restLen) << end) & mask 
			nbits = min(restLen, 8)				
