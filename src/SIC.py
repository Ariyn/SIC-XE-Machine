#!python3
from infos import *
from Device import Printer, BIOS, Storage

RegisterSize = 24 #bits
IntegerSize = 24 #Bits
CharacterSize = 24 #Bits
WordSize = 8 #Bits

class SIC:
	# Interger 24Bits
	# Character 8Bits
	mode = "SIC"
	ccPointer = 8
	DebugPC = 2**15+1
	MaximumCycle = DebugPC
	pc = 0

	instruction = "000000000000000000000000"
	opcode = decodeBits(instruction[0:8], zf=True)
	indexMode = decodeBits(instruction[8:9], zf=True)
	address = decodeBits(instruction[9:24], zf=True)

	function = None

	# instructions = [
	# 	"NOP",
	# 	"LDA","LDX","LDCH","LDL",
	# 	"STA","STX","STCH","STL","STSW",
	# 	"ADD", "STB", "MUL","DIV",
	# 	"AND","OR","COMP","TIX",
	# 	"J", "JLT", "JGT","JEQ",
	# 	"JSUB","RSUB",
	# 	"TD","RD","WD"
	# ]

	def __init__(self, source=None, debug = False):
		self.registerValues = [Register(0,"A"),Register(1, "X"),Register(2, "L"),Register(),Register(),Register(),Register(),Register(),Register(8, "PC"),Register(9, "SW")]

		self.registers = {
			"A"	:	self.registerValues[0],
			"X"	:	self.registerValues[1],
			"L" :	self.registerValues[2],
			"PC":	self.registerValues[8],
			"SW":	self.registerValues[9],
			0	:	self.registerValues[0],
			1	:	self.registerValues[1],
			2	:	self.registerValues[2],
			8	:	self.registerValues[8],
			9	:	self.registerValues[9],
		}
		self.registers["L"].setValue(encodeBits(2**15+1))
		# lambda x:print(decodeBits(x))

		self.memory = ["00000000"]*(2**15+1)
		self.memorySize = len(self.memory)
		
		self.devices = [BIOS(source), Storage(), Printer()]
		self.deviceInit()
		self.debug = None

		self.isRunnable = True
		
	def checkMemory(self):
		pass
	def checkInstruction(self):
		pass
	def runByLine(self):
		pass
		
	def deviceInit(self):
		for i in self.devices:
			# print(i)
			d = i.__onload__()
			# print(d)
			if type(i) == BIOS:
				# print(d)
				hexInt = 0
				for index in range(0, len(d)):
					value = d[index]
					
					if index % 2 == 1:
						self.memory[index//2] = self.memory[index//2][:4]+encodeBits(int(value, 16), length=4)
					else:
						self.memory[index//2] = encodeBits(int(value, 16)<<4, length=8)
					# print(value, value2, encodeBits(int(value, 16)<<4 |int(value2, 16), length=8))
					# self.memory[index//2] = encodeBits(int(value, 16)<<4 |int(value2, 16), length=8)

	def run(self, sequence = 0):
		cycle = 0
		
		if sequence:
			self.MaximumCycle = cycle + sequence
			
		while self.isRunnable and cycle < self.MaximumCycle:			
			self.loadInst()
			self.parseInst()
			# print("opcode ", self.opcode)
			
			self.checkInstruction()
			
			self.execInst()
			self.addPC()
			
			cycle += 1
			# print("here")
		
		retVal = decodeBits(self.registers["A"].getValue())
		# print("SIC ends with %d"%retVal)
		# exit(retVal)

	def storeDataRegister(self, reg, address):
		regValue = self.registers[reg].getValue()
		self.setMemory(address, regValue)

	def setMemory(self, address, value):
		size = len(value) // 8

		for i in range(0, size):
			self.memory[address+i] = value[8*i:8*(i+1)]
			# self.memory[address+1], self.memory[address+2] = value[0:8], value[8:16], value[16:24]

	def loadDataRegister(self, reg, address):
		data = self.loadMemory(address)
		self.registers[reg].setValue(data)

	def loadMemory(self, address, size=3):
		value = ""

		if self.memorySize < address+size:
			print(2**15, self.memorySize, address, size)
			self.isRunnable = False
			# raise MemoryOverFlow
		else:
			for i in range(0, size):
				value += self.memory[address+i]

		return signExtend(value)

	def loadInst(self):
		pc = decodeBits(self.registers["PC"].getValue())
		inst = self.loadMemory(pc)
		self.instruction = inst
		self.pc = pc

	def parseInst(self):
		inst = self.instruction
		self.opcode = decodeBits(inst[0:8], zf=True)
		self.indexMode = decodeBits(inst[8:9], zf=True)
		self.address = decodeBits(inst[9:24], zf=True)
		
		if self.opcode in instructions:
			i = instructions[self.opcode]
			self.function = getattr(self, i)
		else:
			print("%06x"%self.opcode)
			raise WrongOpcodeError

	def execInst(self):
		# print(decodeBits(self.registers["PC"].getValue()), " : ", hex(self.opcode), "("+str(encodeBits(self.opcode))+")", self.indexMode, self.address)
		if self.indexMode:
			address = decodeBits(self.registers["X"].getValue())+self.address
		else:
			address = self.address
		
		self.function(address)

	def addPC(self, delta = 3):
		pc = decodeBits(self.registers["PC"].getValue()) + delta
		if 2**15 <= pc or self.DebugPC <= pc:
			self.isRunnable = False
		
		self.registers["PC"].setValue(encodeBits(pc))
		
		# print(pc)

	def LDA(self, address):
		data = self.loadMemory(address)
		
		try:
			self.registers["A"].setValue(data)
		except WrongBitSize:
			print(self.opcode, decodeBits(self.registers["PC"].getValue()), address, data)
			exit(-3)

	def LDX(self, address):
		data = self.loadMemory(address)
		self.registers["X"].setValue(data)

	def LDCH(self, address):
		# print(address, self.loadMemory(address))
		data = self.loadMemory(address)[0:8]

		self.registers["A"].setValue(data, startBit = 16, dataLength = 8)

	def LDL(self, address):
		data = self.loadMemory(address)

		self.registers["L"].setValue(data)

	def STA(self, address):
		data = self.registers["A"].getValue()
		self.setMemory(address, data)

	def STX(self, address):
		data = self.registers["X"].getValue()
		self.setMemory(address, data)

	def STCH(self, address):
		data = self.registers["A"].getValue()[16:24]
		self.setMemory(address, data)

	def STL(self, address):
		data = self.registers["L"].getValue()
		self.setMemory(address, data)

	def STSW(self, address):
		data = self.registers["SW"].getValue()
		self.setMemory(address, data)

	def ADD(self, address):
		value = decodeBits(self.loadMemory(address))
		value2 = decodeBits(self.registers["A"].getValue())
		
		addValue = value2 + value

		self.registers["A"].setValue(encodeBits(addValue))

	def SUB(self, address):
		value = decodeBits(self.loadMemory(address))
		value2 = decodeBits(self.registers["A"].getValue())
		
		addValue = value2 - value

		self.registers["A"].setValue(encodeBits(addValue))

	def MUL(self, address):
		value = decodeBits(self.loadMemory(address))
		value2 = decodeBits(self.registers["A"].getValue())
		
		addValue = value2 * value

		self.registers["A"].setValue(encodeBits(addValue))

	def DIV(self, address):
		value = decodeBits(self.loadMemory(address))
		value2 = decodeBits(self.registers["A"].getValue())
		
		addValue = value2 // value

		self.registers["A"].setValue(encodeBits(addValue))

	def AND(self, address):
		value = decodeBits(self.loadMemory(address))
		value2 = decodeBits(self.registers["A"].getValue())
		
		addValue = value2 & value

		self.registers["A"].setValue(encodeBits(addValue))

	def OR(self, address):
		value = decodeBits(self.loadMemory(address))
		value2 = decodeBits(self.registers["A"].getValue())
		
		addValue = value2 | value

		self.registers["A"].setValue(encodeBits(addValue))

	def COMP(self, address, reg = "A"):
		value = decodeBits(self.loadMemory(address))
		value2 = decodeBits(self.registers[reg].getValue())

		# print(self.registers[reg].getValue(), self.loadMemory(address), value, value2, address)
		comps = ""

		if value < value2:
			comps = "100"
		elif value == value2:
			comps = "010"
		elif value > value2:
			comps = "001"

		self.registers["SW"].setValue(comps, startBit = self.ccPointer, dataLength = 3)

	def TIX(self, address):
		data = decodeBits(self.registers["X"].getValue()) +1
		data = encodeBits(data)

		self.registers["X"].setValue(data)
		self.COMP(address, reg="X")

	def J(self, address):
		data = encodeBits(address-3)
		self.registers["PC"].setValue(data)

	def JLT(self, address):
		# print("JLT")
		cc = self.registers["SW"].getValue()[self.ccPointer:self.ccPointer+3]
		# print(cc)

		if cc == "001":
			self.J(address)

	def JGT(self, address):
		cc = self.registers["SW"].getValue()[self.ccPointer:self.ccPointer+3]
		# print("JGT", address, cc)
		if cc == "100":
			self.J(address)

	def JEQ(self, address):
		cc = self.registers["SW"].getValue()[self.ccPointer:self.ccPointer+3]
		if cc == "010":
			self.J(address)

	def JSUB(self, address):
		# print("SUB!", address, self.registers["PC"].getValue())
		self.registers["L"].setValue(self.registers["PC"].getValue())
		self.J(address)

	def RSUB(self, address):
		data = self.registers["L"].getValue()
		# print(data)
		# self.J(decodeBits(data))
		self.registers["PC"].setValue(data)

	def TD(self, address):
		# print("TESTING!!")
		# print(address)
		address = decodeBits(self.loadMemory(address))
		ready = self.devices[address].__test__()
		
		if ready:
			comps = "100"
		else:
			comps = "010"
		# print(comps, self.devices[address], ready)
		self.registers["SW"].setValue(comps, startBit = self.ccPointer, dataLength = 3)

		
	def RD(self, address):
		address = decodeBits(self.loadMemory(address))
		# print(address)
		data = self.devices[address]()
		self.registers["A"].setValue(data, startBit = 16, dataLength = 8)
		# print("RD!", data)
		# address = decodeBits(address)

	def WD(self, address):
		# print("WD", address)
		address = decodeBits(self.loadMemory(address))
		data = self.registers["A"].getValue()[-8:]
		self.devices[address](data)


## dump into real binary file? or just string binary?
	def DUMP(self, address, path="sample_DUMP"):
		sa = decodeBits(self.registers["X"].getValue())
		print(address)
		memoryString = "\n".join(self.memory[sa:sa+address])
		memoryString = "memorydump SA=%d EA=%d\n" %(sa, sa+address) + memoryString
		file = open(path, "w")
		file.write(memoryString)
		# file.close()

	def LOAD(self, path="sample_DUMP"):
		with open(path, "rb") as file:
			# memoryList = file.read()
			# memoryInfo, memoryList = None, memoryString.split("\n")
			
			memoryInfo, memoryList = None, loadBinFile(file)
			if memoryList[0][0:10] == "memorydump":
				memoryList, memoryInfo = memoryList[1:], memoryList[0].split(" ")

			if not memoryInfo:
				sa = decodeBits(self.registers["X"].getValue())
				ea = len(memoryList)
				# print(sa, ea)
			else:
				sa, ea = int(memoryInfo[1][3:]), int(memoryInfo[2][3:])
			
			# change this with word sizze
			for i in range(sa, ea):
				m = i*3
				self.memory[m], self.memory[m+1], self.memory[m+2] = memoryList[i][0:8], memoryList[i][8:16], memoryList[i][16:24]
				# print(memoryList[i], self.memory[m], self.memory[m+1], self.memory[m+2])

	# debug functions
	def setRegister(self, reg, value):
		self.registers[reg].setValue(value)


if __name__ == "__main__":
	import sys
	import select

	if select.select([sys.stdin,],[],[],0.0)[0]:
		source = input()
	else:
		source = None
	# path = sys.argv[1]
	sic = SIC(source, debug=True)
	# sic.MaximumCycle = 200
	
	# sic.LOAD(path)
	# print(sic.memory)
	sic.run()