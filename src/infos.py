instructions = {
	"LDA":0x0,
	"LDX":0x4,
	"LDCH":0x50,
	"LDL":0x8,

	"STA":0xC,
	"STX":0x10,
	"STCH":0x54,
	"STL":0x14,
	"STSW":0xE8,

	"ADD":0x18,
	"SUB":0x1C,
	"MUL":0x20,
	"DIV":0x24,

	"AND":0x40,
	"OR":0x44,

	"COMP":0x28,
	"TIX":0x2C,

	"J":0x3C,
	"JLT":0x38,
	"JGT":0x34,
	"JEQ":0x30,

	"JSUB":0x48,
	"RSUB":0x4C,

	"TD":0xE0,
	"RD":0xD8,
	"WD":0xDC,

	"DUMP":0xF1,
	"LOAD":0xF2,
	
	0x0:"LDA",
	0x4:"LDX",
	0x50:"LDCH",
	0x8:"LDL",

	0xC:"STA",
	0x10:"STX",
	0x54:"STCH",
	0x14:"STL",
	0xE8:"STSW",

	0x18:"ADD",
	0x1C:"SUB",
	0x20:"MUL",
	0x24:"DIV",

	0x40:"AND",
	0x44:"OR",

	0x28:"COMP",
	0x2C:"TIX",

	0x3C:"J",
	0x38:"JLT",
	0x34:"JGT",
	0x30:"JEQ",

	0x48:"JSUB",
	0x4C:"RSUB",

	0xE0:"TD",
	0xD8:"RD",
	0xDC:"WD",

	0xF1:"DUMP",
	0xF2:"LOAD"
}

class AccessNotUsedRegisterError(BaseException):
	pass

class WrongBitSize(BaseException):
	# def __init__(self, message, errors):
	# 	super(WrongBitSize, self).__init__(message)

	# 	self.errors = errors
	pass

class MemoryOverFlow(BaseException):
	pass

class WrongOpcodeError(BaseException):
	pass

class Register:
	def __init__(self, number=-1, name="None"):
		self.valueBits = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		self.value = 0
		self.name = name
		self.number = number

	def setValue(self, dataBits, startBit = 0, dataLength = 24):
		if self.checkNotUsed():
			raise AccessNotUsedRegisterError

		# if len(dataBits) != len(self.valueBits) - startBit:
		if len(dataBits) != dataLength:
			raise WrongBitSize

		for i, v in enumerate(dataBits):
			self.valueBits[i+startBit] = v

		# self.value = SIC.decodeBits(self.valueBits)

	def getValue(self, decode=False):
		if self.checkNotUsed():
			raise AccessNotUsedRegisterError

		x = "".join([str(i) for i in self.valueBits])

		return x

	def checkNotUsed(self):
		if self.number == -1:
			return True
		else:
			return False
def loadBinFile(file):
	retVal = []
	binArr = True
	while True:
		binArr = bytearray(file.read(3))
		number = 0
		for i in range(0, len(binArr)):
			number = number << 8
			number += binArr[i]
			# print(binArr[i], number)
		
		if not binArr:
			break
		# print(binArr, number)
		# print(encodeBits(number))
		retVal.append(encodeBits(number))
	
	return retVal
	
def decodeBits(bits, unsigned=False, zf=False, length=24):
	if zf:
		bits = zeroFill(bits, length)

	if len(bits) < length:
		raise WrongBitSize

	value = int(bits, 2)

	if not unsigned and bits[0] == "1":
		newBits = "".join(["0" if i == "1" else "1" for i in bits])

		value = -(int(newBits, 2)+1)
		
	if length < len(bits):
		raise OverflowError("TOO LONG INT")

	return value

def encodeBits(value, unsigned=False, length=24):
	if value < 0 and not unsigned:
		bits = ("{0:0%db}"%length).format(value & (2**length))
	else:
		bits = ("{0:0%db}"%length).format(value)


	if length < len(bits):
		raise OverflowError("TOO LONG INT")

	return bits

def signExtend(bits, length=24):
	val = bits[0] * (length - len(bits))
	bits = val + bits
	return bits

def zeroFill(bits, length=24):
	return "0" * (length - len(bits)) + bits