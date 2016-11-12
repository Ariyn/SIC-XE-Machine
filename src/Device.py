from infos import *

class Device:
	name = "sample device"
	info = "you can't use this device. only for checking device works."
	def __call__(self):
		pass
	
	
class Printer(Device):
	name = "printer"
	info = "this device print text, number on screen with python's basic print method"
	
	def __call__(self, x):
		print(decodeBits(x))
		
if __name__ == "__main__":
	p = Printer()
	print(p("00121"))