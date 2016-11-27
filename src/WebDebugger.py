from Device import Device
from infos import *
import sys, re, types, json
import threading, time
import operator
import socket
import hashlib, base64, struct

from SIC import *

# web socket > http://lanian-windrunner.blogspot.kr/2013/08/python-websocket-server.html

class Debugger:
	dataAssign = [
		(1, 0, "mode = %s", "mode")
	]
	memoryStart = 0
	runnable = True
	key = ""
	needInput = True
	delay = 0
	breakPoint = []
	cmdList = ["c", "q", "r", "b", "t", "rb", "de", "re"]
	registers = {}
	debugLines = {}
	tracingVariables = []
	isRun = False
	port = 8765
	
	def __init__(self, cls, instance, debugLines):
		self.instance = instance
		
		for i in ["A", "PC", "SW", "L", "X"]:
			self.registers[i] = instance.registers[i]
			
		self.debugLines = debugLines
		sock = socket.socket()
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind(('', self.port))
		sock.listen(1)
		self.sock = sock
		
	def start(self):
		while True:
			print ('Waiting for connection on port ' + str(self.port) + ' ...')
			client, addr = self.sock.accept()
			print("connection from %s" % str(addr))
			threading.Thread(target = self.debugMain, args = (client, addr)).start()
	
	# TODO
	# while loof if needInput and input not in cmdList
	# run sic if receive input packet or not needInput
	# debuggerData has to be made after sic.run
	def debugMain(self, client, addr):
		print("New Debugger connected~")
		self.handShake(client)
		print("successfully")
		
		while self.runnable:
			opcode, data = self.recv(client)
			if opcode == 0x8:
				print("close frame received")
				self.runnable = False
			elif opcode == 0x1:
				if len(data) == 0:
					self.runnable = False
				msg = data.decode('utf-8', 'ignore')
				d = self.msgParser(msg)
				if not d:
					msg = "{\"event\":\"failed\"}"
				else:
					if self.isRun:
						self.instance.run(1)
					
					msg = self.makeWebsocketData()
				send(client, msg)
			else:
				print("frame not handled : opcode = %d, len(data) = %d" % (opcode, len(data)))
		
		client.close()
		exit(0)
	
	def handShake(self, client):
		request = client.recv(2048)
		m = re.search('Sec-WebSocket-Key: (.+?)\r\n', request.decode("utf-8"))
		
		key = m.group(1)+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
		response = "HTTP/1.1 101 Switching Protocols\r\n"+\
			"Upgrade: websocket\r\n"+\
			"Connection: Upgrade\r\n"+\
			"Sec-WebSocket-Accept: %s\r\n"+\
			"\r\n"
		r = response % base64.b64encode(hashlib.sha1(key.encode("utf-8")).digest()).decode("utf-8")
		client.send(r.encode("utf-8"))
		
		msg = self.makeWebsocketData(staticData = {
			"debugLines":self.debugLines
		}, startLoc = 0, length = len(self.instance.memory))
		self.send(client, msg)
	
	def send(self, client, msg):
		data = bytearray(msg.encode("utf-8"))
		if 126 < len(data) < 65535:
			data = bytearray([0x81, 126]) + bytearray(struct.pack(">H", len(data))) + data
		elif 65535 < len(data):
			data = bytearray([0x81, 127]) + bytearray(struct.pack(">Q", len(data))) + data
		else:
			data = bytearray([0x81, len(data)]) + data
		client.send(data)
		
	def recv(self, client):
		firstByte = bytearray(client.recv(1))[0]
		FIN = (0xFF & firstByte) >> 7
		opcode = (0x0F & firstByte)
		
		secondByte = bytearray(client.recv(1))[0]
		mask = (0xFF & secondByte) >> 7
		payloadLen = (0x7F & secondByte)
		
		if opcode < 3:
			if payloadLen == 126:
				payloadLen = struct.unpack_from(">H", bytearray(client.recv(2)))[0]
			elif payloadLen == 127:
				payloadLen = struct.unpack_from(">Q", bytearray(client.recv(8)))[0]
			
			if mask == 1:
				maskingKey = bytearray(client.recv(4))	
			maskedData = bytearray(client.recv(payloadLen))
			
			if mask == 1:
				data = [maskedData[i] ^ maskingKey[i%4] for i in range(len(maskedData))]
			else:
				data = maskedData
		else:
			return opcode, bytearray(b"\x00")
		
		return opcode, bytearray(data)
		
	def setTracingVariable(self, name):
		if name in self.debugLines and self.debugLines[name] not in self.tracingVariables:
			self.tracingVariables.append(self.debugLines[name])
			
			# print(self.tracingVariables)
			# time.sleep(3)
	
	def msgParser(self, key):
		self.isRun = False
		pc = self.instance.pc
		
		if pc in self.breakPoint:
			self.needInput = True

		if self.needInput:
			keyNames = (key[0], key[:2], key, key.split(" "))
			if key and 0 < len(key) and (keyNames[0] in self.cmdList or keyNames[1] in self.cmdList or keyNames[2] in self.cmdList):
				return False
			
			if keyNames[1] == "rb":
				value = int(keyNames[-1][1], 16)
				self.breakPoint.remove(value)
			elif keyNames[1] == "de":
				self.delay = int(keyNames[-1][1])
			elif keyNames[1] == "re":
				self.reset()
			elif keyNames[0] == "r":
				self.needInput = False
				self.isRun = True
			elif keyNames[0] == "q":
				self.runnable = False
			elif keyNames[0] == "b":
				value = int(keyNames[-1][1], 16)
				self.breakPoint.append(value)
			elif keyNames[0] == "c":
				self.isRun = True
			elif keyNames[0] == "t":
				keys = keyNames[-1]
				self.setTracingVariable(keys[1])
				self.isRun = False
			self.key = key
		else:
			self.isRun = True

		return True
	
	def makeWebsocketData(self, staticData = {}, startLoc=0, length=0):
		data = {
			"instruction": {
				"opcode":self.instance.instruction[0:8],
				"isIndex":self.instance.instruction[8],
				"operand":self.instance.instruction[9:],
				"instruction":instructions[self.instance.opcode],
				"value":decodeBits(self.instance.instruction[9:], zf=True)
			},
			"memory":None,
			"register":{
				"A":0,
				"L":0,
				"X":0,
				"PC":0,
				"SW":0
			},
			"breakPoints":self.breakPoint,
			"variables":{
				
			}
		}
		
		data.update(staticData)
		
		for i, v in enumerate(self.tracingVariables):
			value = self.instance.loadMemory(int(v[1], 16))
			data["variables"][v[1]] = {
				"address":"%06x"%v[2],
				"name":v[1],
				"data":value
			}
		
		for v in self.registers:
			data["register"][v] = decodeBits(self.registers[v].getValue())
		
		# TODO
		# send debugLines at first time
		
		# TODO
		# transport entire memory is stupid thing.
		# transport memory after these instructions
		# 0xC:"STA" > 3bytes
		# 0x10:"STX" > 3bytes
		# 0x54:"STCH" > 1bytes
		# 0x14:"STL" > 3bytes
		# 0xE8:"STSW" > 3bytes
		if startLoc == 0 and length == 0:
			opValue = decodeBits(data["instruction"]["opcode"], zf=True)
			if opValue in [0xC, 0x10, 0x54, 0x14, 0xE8]:
				if data["instruction"]["isIndex"] == "1":
					startLoc = data["register"]["X"]
				
				startLoc += data["instruction"]["value"]
				
			if opValue == 0x54:
				length = 1
			else:
				length = 3
			
		
		data["memory"] = {
			"start":startLoc,
			"length":length,
			"map":self.instance.memory[startLoc:startLoc+length]
		}
		
		return json.dumps(data)
		
	def reset(self):
		# TODO
		# reset all variables
		
		pass
	
def checkMemory(self):
	pc = self.registers["PC"].getValue()
	
	# pc = signExtend( "".join(self.memory[pc:pc+3]) )
	# print(pc)
	
def checkInstruction(self):
	# print(self.opcode, instructions[self.opcode], self.indexMode, self.address)
	pass
	
class _SIC:
	sample = 0
	mode = "SIC"
	
	memory = ["00000000"]*(2**15+1)
	memorySize = len(memory)
	
	def run(self, sequence=0):
		self.runByLine()
	
if __name__ == "__main__":
	import sys
	import select, os

	if select.select([sys.stdin,],[],[],0.0)[0]:
		# r, w = os.pipe()
		backup = open('/dev/tty')
		newTty = open('/dev/tty')
		stdinNo = sys.stdin.fileno()
		os.dup2(stdinNo, backup.fileno())
		os.dup2(newTty.fileno(), stdinNo)
		
		source = backup.read()
		# print(source)
		
	else:
		source = ""
	
	debugLines = {}
	
	for i in source.split("\\n"):
		if i and i[0] == "\\" and i[1] == "d":
			dataSet = i[2:].split(" ")
			debugLines[dataSet[0]] = dataSet
			debugLines[dataSet[1]] = dataSet
			debugLines[dataSet[2]] = dataSet
	# path = sys.argv[1]
	sic = SIC(source, debug=True)
	
	# sic = _SIC()
	debug = Debugger(SIC, sic, debugLines)
	debug.start()
	# debug.initDebugger()
	# sic.run()