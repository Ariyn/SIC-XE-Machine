## SIC-XE Machine
This is a Simulator for [SIC-XE](https://en.wikipedia.org/wiki/Simplified_Instructional_Computer). SIC-XE is Simple conceptural computer language. so it's machine never exists for officially. This project oriented from System Software project.

this project includes Assembler, SIC machine Simulator, Debugger, web visualizer.

## usuage
```python
from SIC import SIC
sic = SIC(path/to/source.asm, debug=True)
sic.run()
```

source.asm
```asm
.sample 2+2 = 5
.
BB		START	0
		LDA		SUM
		ADD		TWO
		ADD		TWO
		STA		SUM
		WD		OUTPUT
SUM		RESW	1
TWO		WORD	2
OUTPUT	WORD	2
		END		BB
```

output
```bash
> python3 SIC-Run.py
4
```
