from infos import *

class Device:
	name = "sample device"
	info = "you can't use this device. only for checking device works."
	
	def __call__(self):
		pass
	
	def __onload__(self):
		pass
	
	def __test__(self):
		pass

class Storage(Device):
	index = 0
	programPath = "../asm/2+2=5.sicp"
	
	def __onload__(self):
		self.program = open(self.programPath, "rb").read()
		for i in range(0, len(self.program)):
			v = self.program[i]
		
	def __call__(self):
		if len(self.program) <= self.index:
			d = 4
		else:
			d = self.program[self.index]
		bits = encodeBits(d)[-8:]
		try:
			print(chr(decodeBits(bits, length=8)))
		except:
			pass
		
		self.index += 1
		return bits
	
	def __test__(self):
		return True
	
class Printer(Device):
	name = "printer"
	info = "this device print text, number on screen with python's basic print method"
	
	def __test__(self):
		return True
		
	def __call__(self, x):
		print("P:%d with %s"%(decodeBits(x, length = 8), x), chr(decodeBits(x, length = 8)))
		
class BIOS(Device):
	name = "BIOS"
	info = "this device print text, number on screen with python's basic print method"
	
	# firmware = "00004b04004848001e2000540c005a48001e18005a5480002c004b3c0006e0005730001ed8005728004230004828004538001e1c004528005138003f1c004e4c000000000400003000008000000000000700000a000010000001"
	
	firmware = "HBOOT  0000005d\nT0000003c00004b04004848001e2000540c005a48001e18005a5480002c004b3c0006\nT00001e42e0005730001ed8005728004230004828004538001e1c004528005138003f1c004e\nT00003f064c0000\nT0000423000000400003000008000000000000700000a000010000001\nE000000"
	## BIOS must return value with parsed location
	## if RESW is 1
	## BIOS will return 3bytes with 0

	def __init__(self, source=None):
		if source:
			self.firmware = source
		
	def __onload__(self):
		loc = 0
		retVal = []
		
		for i in self.firmware.split("\\n"):
			if i[0] == "H":
				name, start, size = i[1:7], i[7:13], i[13:15]
				# print(name, start, size)
				loc = int(start, 16)
			elif i[0] == "T":
				start, size = int(i[1:7], 16), int(i[7:9], 16)
				# print("m,s ", start, size)
				
				if loc < start:
					# print("start - loc", start, loc, start-loc)
					for counter in range(0, start-loc):
						retVal.append("00")
						loc += 1
				
				for z in zip(i[9:size*2+9:2], i[10:size*2+9:2]):
					# print(int(z[0]+z[1], 16))
					retVal.append(z[0]+z[1])
					# retVal.append(int(z[0]+z[1], 16))
					loc += 1
			elif i[0] == "E":
				break
				# for e in retVal:
				# 	
				# 	print(e)
		
		# print("done")
		return "".join(retVal)
		# self.firmware
		
if __name__ == "__main__":
	p = Printer()
	print(p("00121"))