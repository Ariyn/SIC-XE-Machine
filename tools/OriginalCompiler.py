#!python3
import re, sys, struct

class UndefinedSymbol(BaseException):
	pass
	
class DuplicatedSymbol(BaseException):
	pass
	
class InvaildOperationCode(BaseException):
	pass
	
def encodeBits(value, unsigned=False, length=24):
	if value < 0 and not unsigned:
		bits = ("{0:0%db}"%length).format(value & (2**length))
	else:
		bits = ("{0:0%db}"%length).format(value)
		print(value)

	
	print(bits, length)
	if length < len(bits):
		raise OverflowError("TOO LONG INT")

	return bits

optab = {
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
	"LOAD":0xF2
}

def preCompile(lines):
	codes = re.findall("^(\.)?([A-Za-z0-9_]+)?(?:\t| )*([A-Za-z_]+)(?:\t| )*(?:([A-Za-z0-9_]+?)(?:,(X))?|((?:X|C)(?:`|').+?(?:`|')))?(?:\t| )*\n", lines, re.S|re.M)
	codes = [(i[1], i[2].upper(), i[3] or i[5], i[4]) for i in codes if i[0] != "."]
	
	retVal = []
	for i, v in enumerate(codes):
		retVal.append({
			"line number":i*5,
			"locctr":"",
			"label":v[0],
			"opcode":v[1],
			"operand":v[2],
			"isIndex":v[3]
		})
	
	return retVal

# pass 1
def AssemblerPass1(codes, symtab={}):
	locctr = 0
	
	symtab["_SUBROUTINES"] = []
	bodyCodes = codes
	
	if codes[0]["opcode"] == "START":
		symtab["_START"] = int(codes[0]["operand"], 16)
		locctr, codes[0]["locctr"] = symtab["_START"], symtab["_START"]
		bodyCodes = codes[1:]
		
	for code in bodyCodes:
		opcode, operand, label, isIndex = code["opcode"], code["operand"], code["label"], code["isIndex"]
		
		if opcode == "END":
			break
			
		code["locctr"] = locctr
		
		if label and label in symtab:
			print(locctr, label, opcode, operand)
			raise DuplicatedSymbol
		elif label:
			symtab[label] = locctr
			# print(label, locctr)
		
		if opcode in optab:
			locctr += 3
			if opcode == "JSUB" and operand not in symtab["_SUBROUTINES"]:
				symtab["_SUBROUTINES"].append(operand)
		elif opcode == "WORD":
			locctr += 3
		elif opcode == "RESW":
			# print(operand)
			locctr += 3 * int(operand)
		elif opcode == "RESB":
			locctr += int(operand)
		elif opcode == "BYTE":
			operLength = len(operand)
			if operand[0] == "X":
				operLength = len(operand[2:-1])//2
			elif operand[0] == "C":
				operLength = len(operand[2:-1])
				
			locctr += operLength
		else:
			# print(locctr, label, opcode, operand)
			raise InvaildOperationCode
			
	symtab["_PROGRAM_LENGTH"] = locctr - symtab["_START"]
	symtab["_LOCCTR"] = locctr
	
	return symtab,  codes

def AssemblerPass2(codes, symtab):	
	bodyCodes = codes
	RSUB_ON, length = False, 0
	
	if codes[0]["opcode"] == "START":
		# print(codes[0], encodeBits(symtab["_PROGRAM_LENGTH"], length=6))
		codes[0].update({
			"name":codes[0]["label"][:6]+" "*(6-len(codes[0]["label"])),
			"startRecord":codes[0]["operand"][:6].zfill(6),
			"length":symtab["_PROGRAM_LENGTH"]
		})
		bodyCodes = codes[1:]
	
	for code in bodyCodes:
		code["newSubRoutine"], code["notInCode"] = False, False
		label, opcode, operand, isIndex = code["label"], code["opcode"], code["operand"], code["isIndex"]
		objectCode, newSubRoutine = None, False
		
		if opcode in optab:
			if operand:
				if operand in symtab:
					operand = symtab[operand]
				else:
					print(label, opcode, operand)
					operand = 0
					raise UndefinedSymbol
			else:
				operand = 0
			
			if opcode == "RSUB":
				RSUB_ON = True
			elif RSUB_ON:
				print(opcode)
				code["newSubRoutine"], RSUB_ON = True, False
			# if label in symtab["_SUBROUTINES"]:
				newSubRoutine = True
			
			objectCode = "%06x"%((optab[opcode]<<16)|((1 if isIndex else 0)<<15)|operand)
			# objectCode = "%x%d%02x"%(optab[opcode], 1 if isIndex else 0, operand)
		elif opcode == "BYTE":
			objectCode = 0
			if operand[0] == "X":
				objectCode = ("%0"+str(len(operand[2:-1]))+"x")%int(operand[2:-1], 16)
			elif operand[0] == "C":
				for index, v in enumerate(operand[2:-1]):
					objectCode = ord(v)|objectCode<<8
				objectCode = "%06x"%objectCode
			if RSUB_ON:
				code["newSubRoutine"], RSUB_ON = True, False
				newSubRoutine = True
		elif opcode == "WORD":
			objectCode = "%06x"%int(operand)	
			if RSUB_ON:
				code["newSubRoutine"], RSUB_ON = True, False
				newSubRoutine = True
		elif opcode == "RESW":
			code["notInCode"] = True
			RSUB_ON = True
			objectCode = "000000"*int(operand)
		elif opcode == "RESB":
			code["notInCode"] = True
			RSUB_ON = True
			objectCode = "00"*int(operand)
		elif opcode == "END":
			if operand and operand in symtab:
				operand = symtab[operand]
			else:
				operand = 0
			code["operand"] = operand
			# endRecordString = "E%06x"%int(operand)
		
		code["objectCode"] = objectCode

		if not code["notInCode"] and objectCode:
			length += len(objectCode)
		
		if 60 < length:
			code["newSubRoutine"] = True
			newSubRoutine = True
		
		if newSubRoutine:
			length = 0
			newSubRoutine = False

	
	return codes

def AssemblerPass3(codes):
	datas = []
	# if codes[0]["opcode"] == "START":
	datas.append("H%s%s%x" % (codes[0]["name"], codes[0]["startRecord"], codes[0]["length"]))
	
	datas.append("T%06x"%codes[0]["locctr"]+"%02x")
	
	for code in codes[1:-1]:
		if code["newSubRoutine"]:
			lastLength = len(datas[-1])-11
			datas[-1] = datas[-1]%(lastLength)
			
			if lastLength == 0:
				datas.pop()
			datas.append("T%06x"%code["locctr"]+"%02x")
		
		if not code["notInCode"]:
			datas[-1] += code["objectCode"]
	
	lastLength = len(datas[-1])-11
	datas[-1] = datas[-1]%(lastLength)
	if lastLength == 0:
		datas.pop()
	datas.append("E%06x" % (codes[-1]["operand"]))
	
	# for i in datas:
	# 	print(i)
		
	return datas

def writeBinFile(data, binFile):
	# bytearray(len(data))
	tempList = []
	textEncode, byteEncode = lambda x:[ord(e) for e in x], lambda x:[(int(e[0], 16)<<4 | int(e[1], 16)) & 0xFF for e in zip(x[0::2], x[1::2])]
	
	tempList += textEncode(data[0][0:7])
	tempList += byteEncode(data[0][7:])
	for i in range(1, len(data)):
		tempList += textEncode(data[i][0])
		tempList += byteEncode(data[i][1:])
	
	binFile.write(bytearray(tempList))

bootloader, visualizer = False, False

if 3 <= len(sys.argv):
	t = sys.argv[2]
	if t == "-b":
		bootloader = True
	elif t == "-v":
		visualizer = True
	## -b option
	## this will specially compile for bootloader

path = sys.argv[1]
lines = open(path, "r").read()+"\n"

codes = preCompile(lines)
symtab, codes = AssemblerPass1(codes)
# exit(3)
codes = AssemblerPass2(codes, symtab)
data = AssemblerPass3(codes)

if visualizer:
	# print(len(dbList))
	# debug = [("START", 0)]+debug+[("END", 0)]
	# print(dbList[0])
	for record in codes:
		print("%s\t%s\t%s\t%s\t%s"%(record["locctr"], record["label"], record["opcode"], record["operand"], record["objectCode"] if record["opcode"] not in ["RESB", "RESW", "START", "END"] else ""))
		# print(compile, record)
	# codes = "".join([i["codes"] for i in dbList2])
		# bytes = zip(i["codes"][0::2], i["codes"][1::2])
else:
	binaryFile = open(path.replace(".asm", ".sicp"),"wb")
	stringFile = open(path.replace(".asm", ".sics"), "w")
	
	stringFile.write("\\n".join(data))
	writeBinFile(data, binaryFile)