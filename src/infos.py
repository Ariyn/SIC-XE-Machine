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