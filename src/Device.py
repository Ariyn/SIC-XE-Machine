from infos import *

class Device:
	name = "sample device"
	info = "you can't use this device. only for checking device works."
	
	def __call__(self):
		pass
	
	def __onload__(self):
		pass

class Storage(Device):
	pass
	
class Printer(Device):
	name = "printer"
	info = "this device print text, number on screen with python's basic print method"
	
	def __call__(self, x):
		print(decodeBits(x))
		
class BIOS(Device):
	name = "BIOS"
	info = "this device print text, number on screen with python's basic print method"
	
	firmware = "00004b04004848001e2000540c005a48001e18005a5480002c004b3c0006e0005730001ed8005728004230004828004538001e1c004528005138003f1c004e4c000000000400003000008000000000000700000a000010000001"
	def __onload__(self):
		return self.firmware
		
if __name__ == "__main__":
	p = Printer()
	print(p("00121"))