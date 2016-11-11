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