#!python3
import re, sys, struct
from SIC import instructions, IntegerSize, RegisterSize, CharacterSize, WordSize
from infos import decodeBits, encodeBits, signExtend, zeroFill


compileInst = ["BYTE", "WORD", "RESW", "RESB", "START", "TWORD"]


# path = "sample.asm"
# path = "2+2=5.asm"
path = sys.argv[1]

binaryFile = open(path.replace(".asm", ".sicp"),"wb")
stringFile = open(path.replace(".asm", ".sics"), "w")
lines = open(path, "r").read()+"\n"
# .split("\n")
codes = re.findall("(\.)?([A-Za-z0-9_]+)?(?:\t| )*([A-Za-z_]+)(?:\t| )*([A-Za-z0-9_]+|(X|C)'[A-Za-z0-9_]+')?\n", lines, re.S|re.M)
codes = [(i[1], i[2], i[3]) for i in codes if i[0] != "."]
compiledCodes = []
symTable = {}

finalCodes, finalStrCodes = [], []

for i, v in enumerate(codes):
	inst, value = v[1], v[2]
	naming = v[0] if v[0] else None
	# print(inst)

	if inst in instructions:
		instCode = instructions[inst]
	elif inst in compileInst:
		instCode = inst
		if instCode in ["WORD", "TWORD", "RESW", "RESB"]:
			value = int(value)
			# print(naming, inst, value)


	# newCode = [opcode, index mode, value, naming]
	newCode = [instCode, 0, value, naming]
	if naming:
		symTable[naming] = i*3

	compiledCodes.append(newCode)

for i, v in enumerate(compiledCodes):
	if v[2] in symTable:
		v[2] = symTable[v[2]]

	if type(v[0]) == int:
		opcode = encodeBits(v[0], length=8)
		if v[2]:
			try:
				v[2] = int(v[2])
			except:
				pass
			# print(v)
			value = encodeBits(v[2], length=15)
		else:
			value = encodeBits(0, length=15)

	elif v[0] in ["TWORD", "WORD"]:
		value = encodeBits(v[2])
		# print(v[0], v[2], value)
		opcode, value = value[0:8], value[9:]
	
	strCode = opcode+str(v[1])+value
	bCode = decodeBits(strCode)
	# print(type(bCode), bCode)
	finalStrCodes.append(strCode)
	# finalStrCodes.append(strCode[0:8]+"\n"+strCode[8:16]+"\n"+strCode[16:24])
	finalCodes.append(bCode)

binArr = bytearray(3)
for i in finalCodes:
	# b = struct.pack('i', i)
	
	j = i
	for e in range(0, 3):
		b = j & 0xFF
		binArr[2-e] = b
		# chr(b).encode()
		j = j>>8
	binaryFile.write(binArr)
	# print(len(b))
	# binaryFile.write(b)
	
stringFile.write("\n".join(finalStrCodes))