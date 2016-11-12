#!python3
import re, sys, struct
	
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

	
path = sys.argv[1]

binaryFile = open(path.replace(".asm", ".sicp"),"rb")
d = loadBinFile(binaryFile)
print(d)
