from Device import Device
from infos import *
import threading, time
import types
import curses

from SIC import *

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
	
	def initDebugger(self, cls, instance):
		self.instance = instance
		self.addMethod(instance, checkMemory)
		self.addMethod(instance, checkInstruction)
		self.addMethod(instance, self.MakeRunByLine())
		# delattr(Debugger, "checkMemory")

		curses.wrapper(self.curseMain)
	
	def curseMain(self, stdscr):
		self.window = stdscr
		self.windowSize = stdscr.getmaxyx()
		self.memoryMapHeight = self.windowSize[0] - len(self.dataAssign) - 5
		
		while self.runnable:
			stdscr.clear()
			stdscr.addstr(3, 20, str(id(self)))

			# stdscr.addstr(3, 20, str(self.runnable))
			# for i in self.dataAssign:	
			# 	stdscr.addstr(i[0], i[1], i[2] % self.instance.__getattribute__(i[3]))
			# 
			# stdscr.addstr(len(self.dataAssign), 0, "%d"%self.memoryMapHeight)
			# self.drawMemory(stdscr)
			stdscr.addstr(6, 20, str(self.runnable))
			stdscr.addstr(0, 0, str(decodeBits(self.instance.registers["PC"].getValue())))
			self.instance.run(1)
			
			if not self.instance.isRunnable:
				break
			
			stdscr.refresh()
			time.sleep(self.delay)
			
		stdscr.addstr(3, 20, "done")
		# time.sleep(5)
		exit(0)
		# stdscr.getkey()
	
	def drawMemory(self, stdscr):
		for i in range(self.memoryStart, self.memoryStart+self.memoryMapHeight):
			v = self.instance.memory[i]
			stdscr.addstr(len(self.dataAssign)+5+i, 0, "%s 0x%05x" % (v, i))
			
	
	def addMethod(self, cls, func):
		return setattr(cls, func.__name__, types.MethodType(func, cls))
		
	def MakeRunByLine(debugger):
		def runByLine(self):
			debugger.window.addstr(0, 20, "sample test")
		
			if debugger.needInput:
				curses.echo()
				curses.curs_set(1)
				# NotYetKey = True
				
				# while NotYetKey:
				debugger.window.move(debugger.windowSize[0]-1, debugger.windowSize[1]//2)
				
				key = debugger.window.getstr().decode()
					# if key:
					# 	NotYetKey = False
				if key[0] == "r":
					debugger.needInput = False
				elif key[0] == "q":
					debugger.runnable = False
					debugger.window.addstr(2, 20, str(debugger.runnable))
				elif key[0] == "b":
					keys = key.split(" ")
					debugger.breakPoint.append(int(keys[1]))
				
				debugger.key = key
				curses.noecho()
				curses.curs_set(0)
				debugger.window.addstr(1, 20, "%s"%debugger.key)
			
			pc = decodeBits(self.registers["PC"].getValue())
			if pc in debugger.breakPoint:
				debugger.needInput = True

		return runByLine
	
def checkMemory(self):
	pc = decodeBits(self.registers["PC"].getValue())
	
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
		if i[0] == "\\" and i[1] == "d":
			dataSet = i[2:].split(" ")
			debugLines[dataSet[0]] = dataSet
			debugLines[dataSet[1]] = dataSet
			
	# print(debugLines)
	
	# exit(0)
	# path = sys.argv[1]
	sic = SIC(source, debug=True)
	
	# sic = _SIC()
	debug = Debugger()
	debug.initDebugger(SIC, sic)
	# sic.run()
	
	