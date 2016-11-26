from Device import Device
from infos import *
import threading, time
import types
import curses
import operator

from SIC import *

## TODO
## arrow up : previous command
## memory map no arrow when start
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
	cmdList = ["c", "q", "r", "b", "t", "d", "rb", "de", "re"]
	registers = {}
	debugLines = {}
	tracingVariables = []
	isRun = False
	
	def __init__(self, cls, instance, debugLines):
		self.instance = instance
		self.addMethod(instance, checkMemory)
		self.addMethod(instance, checkInstruction)
		self.addMethod(instance, self.MakeRunByLine())
		# delattr(Debugger, "checkMemory")
		
		for i in ["A", "PC", "SW", "L", "X"]:
			self.registers[i] = instance.registers[i]
			
		self.debugLines = debugLines
		
	def start(self):
		curses.wrapper(self.curseMain)
		
	def curseMain(self, stdscr):
		self.window = stdscr
		stdscr.keypad(False);
		self.windowSize = stdscr.getmaxyx()
		self.memoryMapHeight = self.windowSize[0] - len(self.dataAssign) - 5

		while self.runnable:
			stdscr.clear()
			
			self.instance.checkMemory()
			
			self.instance.runByLine()
			
			if self.isRun:
				self.instance.run(1)
			
			if not self.instance.isRunnable:
				break
			
			if not self.needInput:
				time.sleep(self.delay)
			
			stdscr.refresh()
			
		stdscr.addstr(3, 20, "done")
		# time.sleep(5)
		exit(0)
		# stdscr.getkey()
		
	def drawInstruction(self):
		stdscr = self.window
		stdscr.addstr(3, 20, "%05x" % self.instance.pc)
		stdscr.addstr(4, 20, self.instance.instruction[0:8])
		stdscr.addstr(4, 29, self.instance.instruction[8])
		stdscr.addstr(4, 31, self.instance.instruction[9:])
		stdscr.addstr(5, 20, instructions[self.instance.opcode])
		stdscr.addstr(5, 31, "%06x" %decodeBits(self.instance.instruction[9:], zf=True))
	
	def drawMemory(self):
		stdscr = self.window
		staticSize = len(self.dataAssign)+5
		ran = range(self.memoryStart, self.memoryStart+self.memoryMapHeight)
		
		if  self.instance.pc+3 not in ran:
			self.memoryStart = max(0, 3+self.instance.pc-self.memoryMapHeight)
			ran = range(self.memoryStart, self.memoryStart+self.memoryMapHeight)
			
		for index, i in enumerate(ran):
			v = self.instance.memory[i]
			stdscr.addstr(staticSize+index, 0, "0x%05x %s" % (i, v))
			if self.instance.pc == i:
				stdscr.addstr(staticSize+index, 17, "◀")
	
	def drawRegisters(self):
		stdscr = self.window
		stdscr.addstr(0, 50, "registers")
		for i, v in enumerate(sorted(self.registers.items(), key=operator.itemgetter(0))):
			value = v[1].getValue()
			stdscr.addstr(i+1, 50, "%s"%v[0])
			stdscr.addstr(i+1, 55, "%s %06x"%(value, decodeBits(value)))
		# time.sleep(3)
		pass
	
	def drawBreakPoints(self):
		stdscr = self.window
		startLoc = len(self.registers)+2
		stdscr.addstr(startLoc, 50, "breakPoints %d"%len(self.breakPoint))
		
		stdscr.addstr(startLoc+1, 50, " ".join(["%x"%i for i in self.breakPoint]))
			
	def drawVariables(self):
		stdscr = self.window
		startLoc = len(self.registers)+5
		stdscr.addstr(startLoc, 50, "variables %d"%len(self.tracingVariables))

		for i, v in enumerate(self.tracingVariables):
			value = self.instance.loadMemory(int(v[1], 16))
			stdscr.addstr(startLoc+1+i, 50, "%-6s %s %s" % (v[2], v[1], value))
		
	def setTracingVariable(self, name):
		if name in self.debugLines and self.debugLines[name] not in self.tracingVariables:
			self.tracingVariables.append(self.debugLines[name])
			
			# print(self.tracingVariables)
			# time.sleep(3)
	
	def addMethod(self, cls, func):
		return setattr(cls, func.__name__, types.MethodType(func, cls))
		
	def MakeRunByLine(debugger):
		def runByLine(self):
			debugger.window.addstr(0, 20, "SIC Debugger")
			
			debugger.isRun = False
			pc = self.pc
			
			if pc in debugger.breakPoint:
				debugger.needInput = True
			
			debugger.drawInstruction()
			debugger.drawMemory()
			debugger.drawRegisters()
			debugger.drawVariables()
			debugger.drawBreakPoints()

			if debugger.needInput:
				curses.echo()
				curses.curs_set(1)
				NotYetKey = True
				
				while NotYetKey:
					debugger.window.move(debugger.windowSize[0]-1, debugger.windowSize[1]//2)
					
					key = debugger.window.getstr().decode()
					if key and 0 < len(key) and (key[0] in debugger.cmdList or key[0:2] in debugger.cmdList):
						NotYetKey = False
				if key[0:2] == "rb":
					value = int(key.split(" ")[1], 16)
					debugger.breakPoint.remove(value)
				elif key[0:2] == "de":
					self.delay = int(key.split(" ")[1])
				elif key[0:2] == "re":
					debugger.reset()
				elif key[0] == "r":
					debugger.needInput = False
					debugger.isRun = True
				elif key[0] == "q":
					debugger.runnable = False
					debugger.window.addstr(2, 20, str(debugger.runnable))
				elif key[0] == "b":
					value = int(key.split(" ")[1], 16)
					debugger.breakPoint.append(value)
				elif key[0] == "c":
					debugger.isRun = True
				elif key[0] == "t":
					keys = key.split(" ")
					debugger.setTracingVariable(keys[1])
					debugger.isRun = False
				elif key[0] == "d":
					keys = key.split(" ")
					debugger.DUMP(int(keys[1], 16), int(keys[2], 16))
					
				
				debugger.key = key
				curses.noecho()
				curses.curs_set(0)
				debugger.window.addstr(1, 20, "%s"%debugger.key)
			else:
				debugger.isRun = True

		return runByLine
		
	def DUMP(self, sa, size, path="sample_DUMP"):
		if size == 0:
			m = self.instance.memory
		else:
			m = self.instance.memory[sa:sa+size]
		# print(sa, sa+size)
		# memoryString = "\n".join(["%05x %s %5s %s %05x" %(3*i+sa, "".join(v), instructions[decodeBits(v[0], zf=True)], v[1][0], decodeBits(v[1][1:]+v[2], zf=True)) for i, v in enumerate(zip(m[0::3], m[1::3], m[2::3]))])
		memoryString = "\n".join(["%05x %s"%(sa+i*3, "".join(v)) for i, v in enumerate(zip(m[0::3], m[1::3], m[2::3]))])
		memoryString = "memorydump FROM %05x TO 0x%05x\n" %(sa, sa+size) + memoryString
		
		
		file = open(path, "w")
		file.write(memoryString)
		file.close()
		
	def reset(self):
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
	
	