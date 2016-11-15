from infos import *

class Device:
	name = "sample device"
	info = "you can't use this device. only for checking device works."
	
	def __call__(self):
		pass
	
	def __onload__(self):
		pass

class Storage(Device):
	def __call__(self):
		pass
	
class Printer(Device):
	name = "printer"
	info = "this device print text, number on screen with python's basic print method"
	
	def __call__(self, x):
		print("P:", decodeBits(x))
		
class BIOS(Device):
	name = "BIOS"
	info = "this device print text, number on screen with python's basic print method"
	
	# firmware = "00004b04004848001e2000540c005a48001e18005a5480002c004b3c0006e0005730001ed8005728004230004828004538001e1c004528005138003f1c004e4c000000000400003000008000000000000700000a000010000001"
	
	firmware = "HPIBONA0000006f\nT0000001814000c48002d08000c4c0000\nT00002d4200006618005d0c006600006918005d0c00690000660c006c1800690c006600806c\nT00004e300c0069dc006328006038003f4c000000000100001e000002\nE000000"
	## BIOS must return value with parsed location
	## if RESW is 1
	## BIOS will return 3bytes with 0
	
	def __onload__(self):
		loc = 0
		retVal = []
		
		for i in self.firmware.split("\n"):
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
				pass
				# for e in retVal:
				# 	
				# 	print(e)
		
		# print("done")
		return "".join(retVal)
		# self.firmware
		
if __name__ == "__main__":
	p = Printer()
	print(p("00121"))