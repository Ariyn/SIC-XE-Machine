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

path = sys.argv[1]
lines = open(path, "r").read()+"\n"

codes = re.findall("^(\.)?([A-Za-z0-9_]+)?(?:\t| )*([A-Za-z_]+)(?:\t| )*(?:([A-Za-z0-9_]+?)(?:,(X))?|((?:X|C)`[A-Za-z0-9_]+`))?(?:\t| )*\n", lines, re.S|re.M)
print(len(codes))
for i in codes:
	print(i)
codes = [(i[1], i[2].upper(), i[3] or i[5], i[4]) for i in codes if i[0] != "."]

# pass 1
def AssemblerPass1(codes, symtab={}, debug = False):
	debugList = []
	locctr = 0
	
	symtab["_SUBROUTINES"] = []
	if codes[0][1] == "START":
		symtab["_START"] = int(codes[0][2], 16)
		locctr = symtab["_START"]
		codes = codes[1:]
		
	for label, opcode, operand, isIndex in codes:
		if opcode == "END":
			break
			
		# print("%x"%locctr, label, opcode, operand)
		
		if label and label in symtab:
			raise DuplicatedSymbol
		else:
			symtab[label] = locctr
		
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
			raise InvaildOperationCode
		# print(locctr)
		debugList.append("%x"%locctr)
			
	symtab["_PROGRAM_LENGTH"] = locctr - symtab["_START"]
	symtab["_LOCCTR"] = locctr
	
	if debug:
		return symtab, debugList
	else:
		return symtab

def AssemblerPass2(codes, symtab, debug= False):
	data = ""
	textRecords = []
	debugList = []
	
	if codes[0][1] == "START":
		# print(codes[0], encodeBits(symtab["_PROGRAM_LENGTH"], length=6))
		data += "H%s%s%x"%(codes[0][0][:6]+" "*(6-len(codes[0][0])), codes[0][2][:6].zfill(6),symtab["_PROGRAM_LENGTH"])
		print(data)
	
	newRT = lambda sr=0, ll=0:{"text":"T", "startRecord":sr+ll, "length":0, "codes":""}
	textRecords.append(newRT(symtab["_START"], 0))
	tr = textRecords[-1]
	endRecord = ""
	
	for label, opcode, operand, isIndex in codes:
		objectCode, newSubRoutine = None, False
		if opcode in optab:
			if operand:
				if operand in symtab:
					operand = symtab[operand]
				else:
					operand = 0
					raise UndefinedSymbol
			else:
				operand = 0
			
			if label in symtab["_SUBROUTINES"]:
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
		elif opcode == "WORD":
			objectCode = "%06x"%int(operand)
		elif opcode == "END":
			if operand and operand in symtab:
				operand = symtab[operand]
			else:
				operand = 0
			endRecord= "E%06x"%int(operand)
			
		if objectCode != None:
			debugList.append(objectCode)
			thisCodeLen = len(objectCode)

			if 60 < thisCodeLen+tr["length"] or newSubRoutine:
				textRecords.append(newRT(tr["startRecord"], tr["length"]))
				tr = textRecords[-1]
				
			tr["codes"] += objectCode
			tr["length"] += thisCodeLen
			
			# print(tr["length"], len(tr["codes"]))
				
	for i in textRecords:
		print("T%06x%02x%s"%(i["startRecord"], i["length"]//2, i["codes"]))
	print(endRecord)
	
	return debugList
		
symtab, dbList = AssemblerPass1(codes, debug=True)
# print(symtab["_SUBROUTINES"])
dbList2 = AssemblerPass2(codes, symtab, debug=True)
# for i in range(0, len(dbList)):
# 	print(dbList[i], dbList2[i])