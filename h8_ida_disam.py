def loadFile():
	"""
	Correctly loads ROM data into place
	IDA loads the ROM at 0x0 to 0x1FFFF however this is not the correct layout.
	The ROM should be loaded at 0x10000-0x2FFFF with 0x10000-0x13FFF copied to 0-3FFF
	The section from 4000 to FFFF contains an unused section, the registers and the RAM

	This function creates the required address space then deletes all the data from 0x4000
	onwards to replicate the mirrored data space. Then loads ROM data into 0x10000-0x2FFFF
	replicating the correct layout of ROM data

	TODO: Properly erase unused section 0x4000 to 0xEE7F
	"""

	print 'Loading missing ROM data'
	#Create a new segment starting from 0x4000 to 0x30000
	AddSegEx(0x4000, 0x30000, 0x0, 0, 1, 2, 0)
	#Delete the newly created segment and disable segment addresses
	#this deletes all data but keeps the address space loaded
	DelSeg(0x4000, SEGMOD_KILL)

	#Get the path to this file
	filePath = GetInputFilePath()
	#Load 0x20000 bytes starting at 0x0 in the ROM file into 0x10000 in IDA
	loadfile(filePath, 0, 0x10000, 0x20000)

def loadFlashCode():
	"""
	Loads the Reflash code into RAM as the ECU does when entering reflash mode
	The code is loaded into RAM starting at 0xF290. Once the copy is done the ECU jumps to the start of the reflash code at 0xF290

	TODO: Find start and end flash code addresses instead of using fixed values
	TODO: Force code conversion and delete names and comments
	"""
	#Get the path to this file
	filePath = GetInputFilePath()
	#Load 0xA47 bytes starting at 0x10030 in the ROM file into 0x10000 in IDA
	loadfile(filePath, 0x10030, 0xF290, 0xA47)

def createSegments():
	"""
	Recreates all the ROM segments for a H8/500 in Mode 4 Extended Max
	Page 0:
	   0 - 1FF Vector Table
	   200 - 3FFF On Chip ROM 16K
	   4000 - EE7F Unused
	   EE80 - FE7F On Chip RAM 4K
	   FE80 - FFFF On Chip Registers 384 Bytes
	Page 1:
	   10000 - 1FFFF On Chip ROM 64K
	Page 2:
	   20000 - 2FFFF On Chip ROM 64k

	TODO: Check default value of br to see if it doesn't need setting to 0x00
	"""

	#Create segment for Page 0
	print 'Creating segment for Page 0'
	AddSegEx(0x0, 0x10000, 0x0, 0, 1, 2, 0)
	RenameSeg(0x0, 'Page00')
	SetSegClass(0x10000, 'CODE')
	#SetSegDefReg(0x20000, "dp", 0x0)
	SetSegmentType(0x10000, SEG_CODE)

	#Create segment for Page 1
	print 'Creating segment for Page 1'
	AddSegEx(0x10000, 0x20000, 0x0, 0, 1, 2, 0)
	RenameSeg(0x10000, 'Page01')
	SetSegClass(0x10000, 'CODE')
	SetSegDefReg(0x10000, 'br', 0x0)
	#Setting DP to 0x1 makes some code incorrectly select from Page1 instead of Page0
	#SetSegDefReg(0x10000, "dp", 0x1)
	SetSegmentType(0x10000, SEG_CODE)

	#Create segment for Page 2
	print 'Creating segment for Page 2'
	AddSegEx(0x20000, 0x30000, 0x0, 0, 1, 2, 0)
	RenameSeg(0x20000, 'Page02')
	SetSegClass(0x20000, 'CODE')
	SetSegDefReg(0x20000, 'br', 0x0)
	#SetSegDefReg(0x20000, "dp", 0x2)
	SetSegmentType(0x20000, SEG_CODE)

	#Create segment for RAM
	print 'Creating segment for RAM'
	AddSegEx(0xEE80, 0xFE80, 0x0, 1, 2, 0, 0)
	RenameSeg(0xEE80, 'RAM')

	#Create segment for Registers
	print 'Creating segment for Registers'
	AddSegEx(0xFE80, 0x10000, 0x0, 0, 1, 2, 0)
	RenameSeg(0xFE80, 'Registers')

	#Create segment for Vector Table
	print 'Creating segment for Vector Table'
	AddSegEx(0x0, 0x200, 0x0, 0, 5, 2, 0)
	RenameSeg(0x0, 'Vectors')


def labelKnownFunctions():
	"""
	Labels known functions within the ROM.

	TODO: Look into finding all fixed address functions using signatures
	TODO: Add list of labels to function docs or make an importable file
	TODO: Make comments and names better
	"""

	#Main function
	#Address is usually the same between ROMs
	MakeNameEx(0x1517C, 'main', SN_NOCHECK)
	MakeComm(0x1517C, 'Main entry point')

	#Main function
	#Address is usually the same between ROMs
	MakeNameEx(0x20A80, 'start_main_ loop', SN_NOCHECK)
	MakeComm(0x20A80, 'Sets up and then enters main loop')

	#Main function
	#Address is usually the same between ROMs
	MakeNameEx(0x20024, 'copy_flash_code', SN_NOCHECK)
	MakeComm(0x20024, 'Copies Flash code into RAM starting at 0xF290\nStart address of copy is in R4\nEnd address of copy is in R1')

	#Byte table lookup function
	#Address is usually the same between ROMs
	MakeNameEx(0x14656, 'table_lookup_byte', SN_NOCHECK)
	MakeComm(0x14656, 'Look up the current BYTE value at the table stored in the stack')

	#Word table lookup function
	#Address is usually the same between ROMs
	MakeNameEx(0x14854, 'table_lookup_word', SN_NOCHECK)
	MakeComm(0x14854, 'Look up the current WORD value at the table stored in the stack')

	#Axis table lookup function
	#Address is usually the same between ROMs
	MakeNameEx(0x14735, 'axis_lookup', SN_NOCHECK)
	MakeComm(0x14735, 'Look up the current value in the axis stored in the stack')

	#Output pin read function
	#Signature:
 	#BF	90 			mov:g.w r0, @-sp
	#BF 98 			stc.w   sr, @-sp
	#0C 07 00 48 	orc.w   #0x700:16, sr
	#15 FE 97 D0 	bclr.b  #0:16, @PortC_PCDR:16
	#15 FE 97 D1 	bclr.b  #1:16, @PortC_PCDR:16
	#00 			nop
	#00 			nop
	#00 			nop
	#00 			nop
	foundCode = FindBinary(0x1400, SEARCH_DOWN, 'BF 90 BF 98 0C 07 00 48 15 FE 97 D0 15 FE 97 D1 00 00 00 00')
	foundFunctionAddress = GetFchunkAttr(foundCode, FUNCATTR_START)
	MakeNameEx(foundFunctionAddress, 'read_output_pins', SN_NOCHECK)
	MakeComm(foundFunctionAddress, 'Read ECU output pins using bit 0 and 1 PortC_PCDR switch')

	#ADC read function
	#Signature:
	#F8 FE A0 80 	mov:g.w @(0xFEA0:16,r0), r0
	#15 FE B8 D7	bclr.b  #7:16, @AD_ADCSR:16
	foundCode = FindBinary(0x1400, SEARCH_DOWN, 'F8 FE A0 80 15 FE B8 D7')
	foundFunctionAddress = GetFchunkAttr(foundCode, FUNCATTR_START)
	MakeNameEx(foundFunctionAddress, 'read_adc_sensor', SN_NOCHECK)
	MakeComm(foundFunctionAddress, 'Look up the current value in the ADC data register FEA0 + R0')

def labelKnownVars():
	"""
	Labels known variables within the ROM

	TODO: List know variables in documentation
	TODO: FindImmediate() seems to be broken do not use
	"""

	im = FindImmediate(0x00, SEARCH_DOWN, 0x262)
	op = GetOperandValue(im[0], 0)
	OpOff(im[0], 0, 0)
	MakeNameEx(op, 'ecu_option_0', SN_NOCHECK)
	MakeComm(op, 'ECU Option 0')
	MakeComm(im[0], 'ECU Option 0')

	addr = GetOperandValue(FindCode(FindCode(im[0], 0x01), 0x01), 1)
	MakeNameEx(addr, 'ecu_opt_0', SN_NOCHECK)
	MakeComm(addr, 'ECU Option 0')

	im = FindImmediate(0x00, SEARCH_DOWN, 0x272)
	op = GetOperandValue(im[0], 0)
	OpOff(im[0], 0, 0)
	MakeNameEx(op, 'ecu_option_1', SN_NOCHECK)
	MakeComm(op, 'ECU Option 1')
	MakeComm(im[0], 'ECU Option 1')

	addr = GetOperandValue(FindCode(FindCode(im[0], 0x01), 0x01), 1)
	MakeNameEx(addr, 'ecu_opt_1', SN_NOCHECK)
	MakeComm(addr, 'ECU Option 1')

	im = FindImmediate(0x00, SEARCH_DOWN, 0x282)
	op = GetOperandValue(im[0], 0)
	OpOff(im[0], 0, 0)
	MakeNameEx(op, 'ecu_option_2', SN_NOCHECK)
	MakeComm(op, 'ECU Option 2')
	MakeComm(im[0], 'ECU Option 2')

	addr = GetOperandValue(FindCode(FindCode(im[0], 0x01), 0x01), 1)
	MakeNameEx(addr, 'ecu_opt_2', SN_NOCHECK)
	MakeComm(addr, 'ECU Option 2')

def createStructs():
	"""
	Creates data structures used by code in the ROM.

	TODO: Figure out adding arrays to strucs
	"""

    id = AddStrucEx(-1, 'map_3d_byte', 0)
    AddStrucMember(id, 'dimensions', -1, FF_BYTE | FF_0NUMD, 0, 1)
    AddStrucMember(id, 'adder', -1, FF_BYTE | FF_0NUMD, 0, 1)
    AddStrucMember(id, 'index_x', -1, FF_WORD, 0, 2)
    AddStrucMember(id, 'index_y', -1, FF_WORD, 0, 2)
    AddStrucMember(id, 'nrows', -1, FF_BYTE | FF_0NUMD, 0, 1)
    AddStrucMember(id, 'data', -1, FF_BYTE | FF_0NUMD, 0, 1)

    id = AddStrucEx(-1, 'map_3d_word', 0)
    AddStrucMember(id, 'dimensions', -1, FF_WORD | FF_0NUMD, 0, 2)
    AddStrucMember(id, 'adder', -1, FF_WORD | FF_0NUMD, 0, 2)
    AddStrucMember(id, 'index_x', -1, FF_WORD, 0, 2)
    AddStrucMember(id, 'index_y', -1, FF_WORD, 0, 2)
    AddStrucMember(id, 'nrows', -1, FF_WORD | FF_0NUMD, 0, 2)
    AddStrucMember(id, 'data', -1, FF_WORD | FF_0NUMD, 0, 2)

    id = AddStrucEx(-1, 'map_2d_byte', 0)
    AddStrucMember(id, 'dimensions', -1, FF_BYTE | FF_0NUMD, 0, 1)
    AddStrucMember(id, 'adder', -1, FF_BYTE | FF_0NUMD, 0, 1)
    AddStrucMember(id, 'index_x', -1, FF_WORD, 0, 2)
    AddStrucMember(id, 'data', -1, FF_BYTE | FF_0NUMD, 0, 1)

    id = AddStrucEx(-1, 'map_2d_word', 0)
    AddStrucMember(id, 'dimensions', -1, FF_WORD | FF_0NUMD, 0, 2)
    AddStrucMember(id, 'adder', -1, FF_WORD | FF_0NUMD, 0, 2)
    AddStrucMember(id, 'index_x', -1, FF_WORD, 0, 2)
    AddStrucMember(id, 'data', -1, FF_WORD | FF_0NUMD, 0, 2)

    id = AddStrucEx(-1, 'axis_table', 0)
    AddStrucMember(id, 'output', -1, FF_WORD, 0, 2)
    AddStrucMember(id, 'input', -1, FF_WORD, 0, 2)
    AddStrucMember(id, 'length', -1, FF_WORD | FF_0NUMD, 0, 2)
    AddStrucMember(id, 'data', -1, FF_WORD | FF_0NUMD, 0, 2)

def createVTEntries():


	# Dictionary of H8 vectors
	# Key is the address of the register in hex
	# Value is a dictionary containing:
	#		The name of the vector
	#		A comment describing the register's purpose
	vectorTable = {
		0x000: {"name": "ev_reset_PC", 			"comment": "Reset (initial PC value)"},
		0x004: {"name": "", 					"comment": "(Reserved for system)"},
		0x008: {"name": "ev_invalid_inst", 		"comment": "Invalid instruction"},
		0x00C: {"name": "ev_DIVXU", 			"comment": "DIVXU instruction (zero divisor)"},
		0x010: {"name": "ev_TRAP/VS", 			"comment": "TRAP/VS instruction"},
		0x014: {"name": "", 					"comment": "(Reserved for system)"},
		0x018: {"name": "", 					"comment": "(Reserved for system)"},
		0x01C: {"name": "", 					"comment": "(Reserved for system)"},
		0x020: {"name": "ev_address_err", 		"comment": "Address error"},
		0x024: {"name": "ev_trace", 			"comment": "Trace"},
		0x028: {"name": "", 					"comment": "(Reserved for system)"},
		0x02C: {"name": "eiv_NMI", 				"comment": "External interrupt: NMI"},
		0x030: {"name": "", 					"comment": "(Reserved for system)"},
		0x034: {"name": "", 					"comment": "(Reserved for system)"},
		0x038: {"name": "", 					"comment": "(Reserved for system)"},
		0x03C: {"name": "", 					"comment": "(Reserved for system)"},
		0x040: {"name": "ev_TRAPA_0", 			"comment": "TRAPA instruction 0"},
		0x044: {"name": "ev_TRAPA_1", 			"comment": "TRAPA instruction 1"},
		0x048: {"name": "ev_TRAPA_2", 			"comment": "TRAPA instruction 2"},
		0x04C: {"name": "ev_TRAPA_3", 			"comment": "TRAPA instruction 3"},
		0x050: {"name": "ev_TRAPA_4", 			"comment": "TRAPA instruction 4"},
		0x054: {"name": "ev_TRAPA_5", 			"comment": "TRAPA instruction 5"},
		0x058: {"name": "ev_TRAPA_6", 			"comment": "TRAPA instruction 6"},
		0x05C: {"name": "ev_TRAPA_7", 			"comment": "TRAPA instruction 7"},
		0x060: {"name": "ev_TRAPA_8", 			"comment": "TRAPA instruction 8"},
		0x064: {"name": "ev_TRAPA_9", 			"comment": "TRAPA instruction 9"},
		0x068: {"name": "ev_TRAPA_A", 			"comment": "TRAPA instruction A"},
		0x06C: {"name": "ev_TRAPA_B", 			"comment": "TRAPA instruction B"},
		0x070: {"name": "ev_TRAPA_C", 			"comment": "TRAPA instruction C"},
		0x074: {"name": "ev_TRAPA_D", 			"comment": "TRAPA instruction D"},
		0x078: {"name": "ev_TRAPA_E", 			"comment": "TRAPA instruction E"},
		0x07C: {"name": "ev_TRAPA_F", 			"comment": "TRAPA instruction F"},
		0x080: {"name": "eiv_IRQ0", 			"comment": "External interrupt: IRQ0"},
		0x084: {"name": "ev_WDT_Interval", 		"comment": "WDT interval timer interrupt"},
		0x088: {"name": "ev_ADI", 				"comment": "A\D Converter Interrupt"},
		0x090: {"name": "eiv_IRQ1", 			"comment": "External interrupt: IRQ1"},
		0x094: {"name": "eiv_IRQ2", 			"comment": "External interrupt: IRQ2"},
		0x098: {"name": "eiv_IRQ3", 			"comment": "External interrupt: IRQ3"},
		0x0A0: {"name": "iiv_IPU1_IMI1", 		"comment": "Internal Interrupt IPU channel 1 IMI 1"},
		0x0A4: {"name": "iiv_IPU1_IMI2", 		"comment": "Internal Interrupt IPU channel 1 IMI 2"},
		0x0A8: {"name": "iiv_IPU1_CMI1-2", 		"comment": "Internal Interrupt IPU channel 1 CMI 1-2"},
		0x0AC: {"name": "iiv_IPU1_OVI", 		"comment": "Internal Interrupt IPU channel 1 OVI"},
		0x0B0: {"name": "iiv_IPU1_IMI3", 		"comment": "Internal Interrupt IPU channel 1 IMI 3"},
		0x0B4: {"name": "iiv_IPU1_IMI4", 		"comment": "Internal Interrupt IPU channel 1 IMI 4"},
		0x0B8: {"name": "iiv_IPU1_CMI3-4", 		"comment": "Internal Interrupt IPU channel 1 CMI 3-4"},
		0x0C0: {"name": "iiv_IPU2_IMI1", 		"comment": "Internal Interrupt IPU channel 2 IMI 1"},
		0x0C4: {"name": "iiv_IPU2_IMI2", 		"comment": "Internal Interrupt IPU channel 2 IMI 2"},
		0x0C8: {"name": "iiv_IPU2_CMI1-2", 		"comment": "Internal Interrupt IPU channel 2 CMI 1-2"},
		0x0CC: {"name": "iiv_IPU2_OVI", 		"comment": "Internal Interrupt IPU channel 2 OVI"},
		0x0D0: {"name": "iiv_IPU3_IMI1", 		"comment": "Internal Interrupt IPU channel 3 IMI 1"},
		0x0D4: {"name": "iiv_IPU3_IMI2", 		"comment": "Internal Interrupt IPU channel 3 IMI 2"},
		0x0D8: {"name": "iiv_IPU3_CMI1-2", 		"comment": "Internal Interrupt IPU channel 3 CMI 1-2"},
		0x0DC: {"name": "iiv_IPU3_OVI", 		"comment": "Internal Interrupt IPU channel 3 OVI"},
		0x0E0: {"name": "iiv_IPU4_IMI1", 		"comment": "Internal Interrupt IPU channel 4 IMI 1"},
		0x0E4: {"name": "iiv_IPU4_IMI2", 		"comment": "Internal Interrupt IPU channel 4 IMI 2"},
		0x0E8: {"name": "iiv_IPU4_CMI1-2",		"comment": "Internal Interrupt IPU channel 4 CMI 1-2"},
		0x0EC: {"name": "iiv_IPU4_OVI", 		"comment": "Internal Interrupt IPU channel 4 OVI"},
		0x0F0: {"name": "iiv_IPU5_IMI1", 		"comment": "Internal Interrupt IPU channel 5 IMI 1"},
		0x0F4: {"name": "iiv_IPU5_IMI2", 		"comment": "Internal Interrupt IPU channel 5 IMI 2"},
		0x0F8: {"name": "iiv_IPU5_CMI1-2", 		"comment": "Internal Interrupt IPU channel 5 CMI 1-2"},
		0x0FC: {"name": "iiv_IPU5_OVI", 		"comment": "Internal Interrupt IPU channel 5 OVI"},
		0x100: {"name": "iiv_IPU6_IMI1", 		"comment": "Internal Interrupt IPU channel 6 IMI 1"},
		0x104: {"name": "iiv_IPU6_IMI2", 		"comment": "Internal Interrupt IPU channel 6 IMI 2"},
		0x10C: {"name": "iiv_IPU6_OVI", 		"comment": "Internal Interrupt IPU channel 6 OVI"},
		0x110: {"name": "iiv_IPU7_IMI1", 		"comment": "Internal Interrupt IPU channel 7 IMI 1"},
		0x114: {"name": "iiv_IPU7_IMI2", 		"comment": "Internal Interrupt IPU channel 7 IMI 2"},
		0x11C: {"name": "iiv_IPU7_OVI", 		"comment": "Internal Interrupt IPU channel 7 OVI"},
		0x120: {"name": "iiv_SCI1_ERI1", 		"comment": "Internal Interrupt SCI1 ERI 1"},
		0x124: {"name": "iiv_SCI1_RI1", 		"comment": "Internal Interrupt SCI1 RI 1"},
		0x128: {"name": "iiv_SCI1_TI1", 		"comment": "Internal Interrupt SCI1 TI 1"},
		0x12C: {"name": "iiv_SCI1_TEI1", 		"comment": "Internal Interrupt SCI1 TEI 1"},
		0x130: {"name": "iiv_SCI2-3_ERI2-3", 	"comment": "Internal Interrupt SCI2/3 ERI 2-3"},
		0x134: {"name": "iiv_SCI2-3_RI2-3", 	"comment": "Internal Interrupt SCI2/3 RI 2-3"},
		0x138: {"name": "iiv_SCI2-3_TI2-3", 	"comment": "Internal Interrupt SCI2/3 TI 2-3"},
		0x13C: {"name": "iiv_SCI2-3_TEI2-3", 	"comment": "Internal Interrupt SCI2/3 TEI 2-3"},
		0x140: {"name": "dtv_IPU6_IMI1", 		"comment": "Data Transfer Interrupt IPU channel 6 IMI 1"},
		0x144: {"name": "dtv_IPU6_IMI2", 		"comment": "Data Transfer Interrupt IPU channel 6 IMI 2"},
		0x150: {"name": "dtv_IPU7_IMI1", 		"comment": "Data Transfer Interrupt IPU channel 7 IMI 1"},
		0x154: {"name": "dtv_IPU7_IMI2", 		"comment": "Data Transfer Interrupt IPU channel 7 IMI 2"},
		0x164: {"name": "dtv_SCI1_RI1", 		"comment": "Data Transfer Interrupt RI 1"},
		0x168: {"name": "dtv_SCI1_TI1", 		"comment": "Data Transfer Interrupt TI 1"},
		0x174: {"name": "dtv_SCI2-3_RI2-3", 	"comment": "Data Transfer Interrupt RI 1-2"},
		0x178: {"name": "dtv_SCI2-3_TI2-3", 	"comment": "Data Transfer Interrupt TI 2-3"},
		0x180: {"name": "dtv_IRQ0", 			"comment": "Data Transfer Interrupt IRQ 0"},
		0x184: {"name": "dtv_WDT_Interval",		"comment": "Data Transfer Interrupt WDT Interval"},
		0x188: {"name": "dtv_ADI", 				"comment": "Data Transfer Interrupt A/D Interrupt"},
		0x190: {"name": "dtv_IRQ1", 			"comment": "Data Transfer Interrupt IRQ 1"},
		0x194: {"name": "dtv_IRQ2", 			"comment": "Data Transfer Interrupt IRQ 2"},
		0x198: {"name": "dtv_IRQ3", 			"comment": "Data Transfer Interrupt IRQ 3"},
		0x1A0: {"name": "dtv_IPU1_IMI1", 		"comment": "Data Transfer Interrupt IPU channel 1 IMI 1"},
		0x1A4: {"name": "dtv_IPU1_IMI2", 		"comment": "Data Transfer Interrupt IPU channel 1 IMI 2"},
		0x1A8: {"name": "dtv_IPU1_CMI1-2", 		"comment": "Data Transfer Interrupt IPU channel 1 CMI 1-2"},
		0x1B0: {"name": "dtv_IPU1_IMI3", 		"comment": "Data Transfer Interrupt IPU channel 1 IMI 3"},
		0x1B4: {"name": "dtv_IPU1_IMI4", 		"comment": "Data Transfer Interrupt IPU channel 1 IMI 4"},
		0x1B8: {"name": "dtv_IPU1_CMI3-4", 		"comment": "Data Transfer Interrupt IPU channel 1 CMI 3-4"},
		0x1C0: {"name": "dtv_IPU2_IMI1", 		"comment": "Data Transfer Interrupt IPU channel 2 IMI 1"},
		0x1C4: {"name": "dtv_IPU2_IMI2", 		"comment": "Data Transfer Interrupt IPU channel 2 IMI 2"},
		0x1C8: {"name": "dtv_IPU2_CMI1-2", 		"comment": "Data Transfer Interrupt IPU channel 2 CMI 1-2"},
		0x1D0: {"name": "dtv_IPU3_IMI1", 		"comment": "Data Transfer Interrupt IPU channel 3 IMI 1"},
		0x1D4: {"name": "dtv_IPU3_IMI2", 		"comment": "Data Transfer Interrupt IPU channel 3 IMI 2"},
		0x1D8: {"name": "dtv_IPU3_CMI1-2", 		"comment": "Data Transfer Interrupt IPU channel 3 CMI 1-2"},
		0x1E0: {"name": "dtv_IPU4_IMI1", 		"comment": "Data Transfer Interrupt IPU channel 4 IMI 1"},
		0x1E4: {"name": "dtv_IPU4_IMI2", 		"comment": "Data Transfer Interrupt IPU channel 4 IMI 2"},
		0x1E8: {"name": "dtv_IPU4_CMI1-2", 		"comment": "Data Transfer Interrupt IPU channel 4 CMI 1-2"},
		0x1F0: {"name": "dtv_IPU5_IMI1", 		"comment": "Data Transfer Interrupt IPU channel 5 IMI 1"},
		0x1F4: {"name": "dtv_IPU5_IMI2", 		"comment": "Data Transfer Interrupt IPU channel 5 IMI 2"},
		0x1F8: {"name": "dtv_IPU5_CMI1-2", 		"comment": "Data Transfer Interrupt IPU channel 5 CMI 1-2"}
	}

	nameCounter = 0
	addr = 0x10000

	while(addr < 0x10200):
		MakeDword(addr)
		OpOff(addr, 0, 0)
		j = Dword(addr)

		if (addr < 0x10140):
			MakeCode(j)
			AutoMark(j, AU_PROC)
			AddCodeXref(addr, j, fl_F)
			print "Adding vector table xRef: %X, %X" % (addr, j)
		else:
			print "Adding DTC vector table xRef: %X, %X" % (addr, j)
			name = Name(j)

			if name == "" or "unk_" in name:
				add_dref(addr, j, dr_R)
				MakeWord(j)
				MakeNameEx(j, "DTC_vec_DTMR_" + str(nameCounter), SN_NOCHECK)
				MakeComm(j, "Data Transfer Mode")

				MakeWord(j + 2)
				MakeNameEx(j + 2, "DTC_vec_DTSR_" + str(nameCounter), SN_NOCHECK)
				MakeComm(j + 2, "Source Address")

				MakeWord(j + 4)
				MakeNameEx(j + 4, "DTC_vec_DTDR_" + str(nameCounter), SN_NOCHECK)
				MakeComm(j + 4, "Destination Address")

				MakeWord(j + 6)
				MakeNameEx(j + 6, "DTC_vec_DTCR_" + str(nameCounter), SN_NOCHECK)
				MakeComm(j + 6, "Transfer Count")

				nameCounter = nameCounter + 1

		addr = addr + 4

	for addr in range (0x000, 0x200):
		MakeDword(addr)
		OpOff(addr, 0, 0)
		if addr in vectorTable:
			print str(addr) + vectorTable[addr]["name"] + vectorTable[addr]["comment"]
			MakeNameEx(addr, vectorTable[addr]["name"], SN_NOLIST)
			MakeComm(addr, vectorTable[addr]["comment"])
			MakeComm(addr + 0x10000, vectorTable[addr]["comment"])

# H8 Register creaation functiom as per H8 documentation
def labelRegisters():

	# Dictionary of H8 registers
	# Key is the address of the register in hex
	# Value is a dictionary containing:
	#		The name of the register
	#		The type of register (byte, word, long)
	#		The initial value of the register (If there is no value set to 0xFF (some already are 0xFF))
	#		A comment describing the register's purpose
	registers = {
		0xFE80: {"name": "Port1_P1DDR",  "type": "byte", "initial": 0x00, "comment": "Port 1 data direction register"},
		0xFE81: {"name": "Port2_P2DDR",  "type": "byte", "initial": 0x00, "comment": "Port 2 data direction register"},
		0xFE82: {"name": "Port1_P1DR",   "type": "byte", "initial": 0x00, "comment": "Port 1 data register"},
		0xFE83: {"name": "Port2_P2DR",   "type": "byte", "initial": 0x00, "comment": "Port 2 data register"},
		0xFE84: {"name": "Port3_P3DDR",  "type": "byte", "initial": 0xC0, "comment": "Port 3 data direction register"},
		0xFE85: {"name": "Port4_P4DDR",  "type": "byte", "initial": 0x00, "comment": "Port 4 data direction register"},
		0xFE86: {"name": "Port3_P3DR",   "type": "byte", "initial": 0xC0, "comment": "Port 3 data register"},
		0xFE87: {"name": "Port4_P4DR",   "type": "byte", "initial": 0x00, "comment": "Port 4 data register"},
		0xFE88: {"name": "Port5_P5DDR",  "type": "byte", "initial": 0x00, "comment": "Port 5 data direction register"},
		0xFE89: {"name": "Port6_P6DDR",  "type": "byte", "initial": 0xE0, "comment": "Port 6 data direction register"},
		0xFE8A: {"name": "Port5_P5DR",   "type": "byte", "initial": 0x00, "comment": "Port 5 data register"},
		0xFE8B: {"name": "Port6_P6DR",   "type": "byte", "initial": 0xE0, "comment": "Port 6 data register"},
		0xFE8C: {"name": "Port7_P7DDR",  "type": "byte", "initial": 0x00, "comment": "Port 7 data direction register"},
		0xFE8E: {"name": "Port7_P7DR",   "type": "byte", "initial": 0x00, "comment": "Port 7 data register"},
		0xFE8F: {"name": "Port8_P8DR",   "type": "byte", "initial": 0xFF, "comment": "Port 8 data register"},
		0xFE91: {"name": "PortA_PADDR",  "type": "byte", "initial": 0x80, "comment": "Port A data direction register"},
		0xFE92: {"name": "Port9_P9DR",   "type": "byte", "initial": 0xFF, "comment": "Port 9 data register"},
		0xFE93: {"name": "PortA_PADR",   "type": "byte", "initial": 0x80, "comment": "Port A data register"},
		0xFE94: {"name": "PortB_P BDDR", "type": "byte", "initial": 0x00, "comment": "Port B data direction register"},
		0xFE95: {"name": "PortC_PCDDR",  "type": "byte", "initial": 0x00, "comment": "Port C data direction register"},
		0xFE96: {"name": "PortB_PBDR",   "type": "byte", "initial": 0x00, "comment": "Port B data register"},
		0xFE97: {"name": "PortC_PCDR",   "type": "byte", "initial": 0x00, "comment": "Port C data register"},
		0xFE98: {"name": "PortB_PBPCR",  "type": "byte", "initial": 0x00, "comment": "Port B pull-up transistor control register"},
		0xFE99: {"name": "PortC_PCPCR",  "type": "byte", "initial": 0x00, "comment": "Port C pull-up transistor control register"},
		0xFE9A: {"name": "oCR_oCR",      "type": "byte", "initial": 0xFF, "comment": "o control register (System clock output)"},
		0xFEA0: {"name": "AD_ADDR0H",    "type": "byte", "initial": 0x00, "comment": "A/D data register 0 (high)"},
		0xFEA1: {"name": "AD_ADDR0L",    "type": "byte", "initial": 0x00, "comment": "A/D data register 0 (low)"},
		0xFEA2: {"name": "AD_ADDR1H",    "type": "byte", "initial": 0x00, "comment": "A/D data register 1 (high)"},
		0xFEA3: {"name": "AD_ADDR1L",    "type": "byte", "initial": 0x00, "comment": "A/D data register 1 (low)"},
		0xFEA4: {"name": "AD_ADDR2H",    "type": "byte", "initial": 0x00, "comment": "A/D data register 2 (high)"},
		0xFEA5: {"name": "AD_ADDR2L",    "type": "byte", "initial": 0x00, "comment": "A/D data register 2 (low)"},
		0xFEA6: {"name": "AD_ADDR3H",    "type": "byte", "initial": 0x00, "comment": "A/D data register 3 (high)"},
		0xFEA7: {"name": "AD_ADDR3L",    "type": "byte", "initial": 0x00, "comment": "A/D data register 3 (low)"},
		0xFEA8: {"name": "AD_ADDR4H",    "type": "byte", "initial": 0x00, "comment": "A/D data register 4 (high)"},
		0xFEA9: {"name": "AD_ADDR4L",    "type": "byte", "initial": 0x00, "comment": "A/D data register 4 (low)"},
		0xFEAA: {"name": "AD_ADDR5H",    "type": "byte", "initial": 0x00, "comment": "A/D data register 5 (high)"},
		0xFEAB: {"name": "AD_ADDR5L",    "type": "byte", "initial": 0x00, "comment": "A/D data register 5 (low)"},
		0xFEAC: {"name": "AD_ADDR6H",    "type": "byte", "initial": 0x00, "comment": "A/D data register 6 (high)"},
		0xFEAD: {"name": "AD_ADDR6L",    "type": "byte", "initial": 0x00, "comment": "A/D data register 6 (low)"},
		0xFEAE: {"name": "AD_ADDR7H",    "type": "byte", "initial": 0x00, "comment": "A/D data register 7 (high)"},
		0xFEAF: {"name": "AD_ADDR7L",    "type": "byte", "initial": 0x00, "comment": "A/D data register 7 (low)"},
		0xFEB0: {"name": "AD_ADDR8H",    "type": "byte", "initial": 0x00, "comment": "A/D data register 8 (high)"},
		0xFEB1: {"name": "AD_ADDR8L",    "type": "byte", "initial": 0x00, "comment": "A/D data register 8 (low)"},
		0xFEB2: {"name": "AD_ADDR9H",    "type": "byte", "initial": 0x00, "comment": "A/D data register 9 (high)"},
		0xFEB3: {"name": "AD_ADDR9L",    "type": "byte", "initial": 0x00, "comment": "A/D data register 9 (low)"},
		0xFEB4: {"name": "AD_ADDRAH",    "type": "byte", "initial": 0x00, "comment": "A/D data register A (high)"},
		0xFEB5: {"name": "AD_ADDRAL",    "type": "byte", "initial": 0x00, "comment": "A/D data register A (low)"},
		0xFEB6: {"name": "AD_ADDRBH",    "type": "byte", "initial": 0x00, "comment": "A/D data register B (high)"},
		0xFEB7: {"name": "AD_ADDRBL",    "type": "byte", "initial": 0x00, "comment": "A/D data register B (low)"},
		0xFEB8: {"name": "AD_ADCSR",     "type": "byte", "initial": 0x00, "comment": "A/D control/status register"},
		0xFEB9: {"name": "AD_ADCR",      "type": "byte", "initial": 0x1F, "comment": "A/D control register"},
		0xFEC0: {"name": "SCI3_SMR",     "type": "byte", "initial": 0x00, "comment": "Serial Communication Interface 3 Serial mode register"},
		0xFEC1: {"name": "SCI3_BRR",     "type": "byte", "initial": 0xFF, "comment": "Serial Communication Interface 3 Bit rate register"},
		0xFEC2: {"name": "SCI3_SCR",     "type": "byte", "initial": 0x00, "comment": "Serial Communication Interface 3 Serial control register"},
		0xFEC3: {"name": "SCI3_TDR",     "type": "byte", "initial": 0xFF, "comment": "Serial Communication Interface 3 Transmit data register"},
		0xFEC4: {"name": "SCI3_SSR",     "type": "byte", "initial": 0x84, "comment": "Serial Communication Interface 3 Serial status register"},
		0xFEC5: {"name": "SCI3_RDR",     "type": "byte", "initial": 0x00, "comment": "Serial Communication Interface 3 Receive data register"},
		0xFEC8: {"name": "SCI1_SMR",     "type": "byte", "initial": 0x00, "comment": "Serial Communication Interface 1 Serial mode register"},
		0xFEC9: {"name": "SCI1_BRR",     "type": "byte", "initial": 0xFF, "comment": "Serial Communication Interface 1 Bit rate register"},
		0xFECA: {"name": "SCI1_SCR",     "type": "byte", "initial": 0x00, "comment": "Serial Communication Interface 1 Serial control register"},
		0xFECB: {"name": "SCI1_TDR",     "type": "byte", "initial": 0xFF, "comment": "Serial Communication Interface 1 Transmit data register"},
		0xFECC: {"name": "SCI1_SSR",     "type": "byte", "initial": 0x84, "comment": "Serial Communication Interface 1 Serial status register"},
		0xFECD: {"name": "SCI1_RDR",     "type": "byte", "initial": 0x00, "comment": "Serial Communication Interface 1 Receive data register"},
		0xFED0: {"name": "SCI2_SMR",     "type": "byte", "initial": 0x00, "comment": "Serial Communication Interface 2 Serial mode register"},
		0xFED1: {"name": "SCI2_BRR",     "type": "byte", "initial": 0xFF, "comment": "Serial Communication Interface 2 Bit rate register"},
		0xFED2: {"name": "SCI2_SCR",     "type": "byte", "initial": 0x00, "comment": "Serial Communication Interface 2 Serial control register"},
		0xFED3: {"name": "SCI2_TDR",     "type": "byte", "initial": 0xFF, "comment": "Serial Communication Interface 2 Transmit data register"},
		0xFED4: {"name": "SCI2_SSR",     "type": "byte", "initial": 0x84, "comment": "Serial Communication Interface 2 Serial status register"},
		0xFED5: {"name": "SCI2_RDR",     "type": "byte", "initial": 0x00, "comment": "Serial Communication Interface 2 Receive data register"},
		0xFEDA: {"name": "PortA_PACR",   "type": "byte", "initial": 0x90, "comment": "Port A control register"},
		0xFEDB: {"name": "Port67_P67CR", "type": "byte", "initial": 0x3E, "comment": "Port 6/7 control register"},
		0xFEDC: {"name": "AD_ADTRGR",    "type": "byte", "initial": 0xFF, "comment": "A/D trigger register"},
		0xFEDE: {"name": "INTC_IRQFR",   "type": "byte", "initial": 0xF1, "comment": "IRQ flag register"},
		0xFEDF: {"name": "BSC_BCR",      "type": "byte", "initial": 0xBF, "comment": "Bus control register"},
		0xFEE0: {"name": "FLM_FLMCR",    "type": "byte", "initial": 0x00, "comment": "Flash memory control register"},
		0xFEE2: {"name": "FLM_EBR1",     "type": "byte", "initial": 0x00, "comment": "Flash memory Erase block register 1"},
		0xFEE3: {"name": "FLM_EBR2",     "type": "byte", "initial": 0x00, "comment": "Flash memory Erase block register 2"},
		0xFEEC: {"name": "FLM_FLMER",    "type": "byte", "initial": 0x71, "comment": "Flash memory emulation register"},
		0xFEED: {"name": "FLM_FLMSR",    "type": "byte", "initial": 0x7F, "comment": "Flash memory status register"},
		0xFEF0: {"name": "PWM1_TCR",     "type": "byte", "initial": 0x38, "comment": "PWM 1 Timer control register"},
		0xFEF1: {"name": "PWM1_DTR",     "type": "byte", "initial": 0xFF, "comment": "PWM 1 Duty register"},
		0xFEF2: {"name": "PWM1_TCNT",    "type": "byte", "initial": 0x00, "comment": "PWM 1 Timer counter"},
		0xFEF4: {"name": "PWM2_TCR",     "type": "byte", "initial": 0x38, "comment": "PWM 2 Timer control register"},
		0xFEF5: {"name": "PWM2_DTR",     "type": "byte", "initial": 0xFF, "comment": "PWM 2 Duty register"},
		0xFEF6: {"name": "PWM2_TCNT",    "type": "byte", "initial": 0x00, "comment": "PWM 2 Timer counter"},
		0xFEF8: {"name": "PWM3_TCR",     "type": "byte", "initial": 0x38, "comment": "PWM 3 Timer control register"},
		0xFEF9: {"name": "PWM3_DTR",     "type": "byte", "initial": 0xFF, "comment": "PWM 3 Duty register"},
		0xFEFA: {"name": "PWM3_TCNT",    "type": "byte", "initial": 0x00, "comment": "PWM 3 Timer counter"},
		0xFF00: {"name": "INTC_IPRA",    "type": "byte", "initial": 0x00, "comment": "Interrupt priority register A"},
		0xFF01: {"name": "INTC_IPRB",    "type": "byte", "initial": 0x00, "comment": "Interrupt priority register B"},
		0xFF02: {"name": "INTC_IPRC",    "type": "byte", "initial": 0x00, "comment": "Interrupt priority register C"},
		0xFF03: {"name": "INTC_IPRD",    "type": "byte", "initial": 0x00, "comment": "Interrupt priority register D"},
		0xFF04: {"name": "INTC_IPRE",    "type": "byte", "initial": 0x00, "comment": "Interrupt priority register E"},
		0xFF05: {"name": "INTC_IPRF",    "type": "byte", "initial": 0x00, "comment": "Interrupt priority register F"},
		0xFF08: {"name": "DTC_DTEA",     "type": "byte", "initial": 0x00, "comment": "Data transfer enable register A"},
		0xFF09: {"name": "DTC_DTEB",     "type": "byte", "initial": 0x00, "comment": "Data transfer enable register B"},
		0xFF0A: {"name": "DTC_DTEC",     "type": "byte", "initial": 0x00, "comment": "Data transfer enable register C"},
		0xFF0B: {"name": "DTC_DTED",     "type": "byte", "initial": 0x00, "comment": "Data transfer enable register D"},
		0xFF0C: {"name": "DTC_DTEE",     "type": "byte", "initial": 0x00, "comment": "Data transfer enable register E"},
		0xFF0D: {"name": "DTC_DTEF",     "type": "byte", "initial": 0x00, "comment": "Data transfer enable register F"},
		0xFF10: {"name": "WDT_TCSR",     "type": "byte", "initial": 0x18, "comment": "Watch Dog Timer control/status register"},
		0xFF11: {"name": "WDT_TCNT",     "type": "byte", "initial": 0x00, "comment": "Watch Dog Timer counter"},
		0xFF14: {"name": "WSC_WCR",      "type": "byte", "initial": 0xF3, "comment": "Wait-state control Register"},
		0xFF15: {"name": "RAM_RAMCR",    "type": "byte", "initial": 0xFF, "comment": "RAM control register"},
		0xFF16: {"name": "BSC_ARBT",     "type": "byte", "initial": 0xFF, "comment": "Bus controller Byte area top register"},
		0xFF17: {"name": "BSC_AR3T",     "type": "byte", "initial": 0xEE, "comment": "Bus controller Three-state area top register"},
		0xFF19: {"name": "SYSC_MDCR",    "type": "byte", "initial": 0xFF, "comment": "Mode control register"},
		0xFF1A: {"name": "SYSC_SBYCR",   "type": "byte", "initial": 0x7F, "comment": "Software standby control register"},
		0xFF1B: {"name": "SYSC_BRCR",    "type": "byte", "initial": 0xFE, "comment": "Bus Release Control Register"},
		0xFF1C: {"name": "SYSC_NMICR",   "type": "byte", "initial": 0xFE, "comment": "NMI control register"},
		0xFF1D: {"name": "SYSC_IRQCR",   "type": "byte", "initial": 0xF0, "comment": "IRQ control register"},
		0xFF1E: {"name": "SYSC_writeCR", "type": "byte", "initial": 0xFF, "comment": "Unsure. Possibly related to RSTCSR"},
		0xFF1F: {"name": "SYSC_RSTCSR",  "type": "byte", "initial": 0x3F, "comment": "Watch Dog Timer Reset control/status register"},
		0xFF20: {"name": "IPU1_T1CRH",   "type": "byte", "initial": 0xC0, "comment": "IPU Channel 1 Timer control register (high)"},
		0xFF21: {"name": "IPU1_T1CRL",   "type": "byte", "initial": 0x80, "comment": "IPU Channel 1 Timer control register (low)"},
		0xFF22: {"name": "IPU1_T1SRAH",  "type": "byte", "initial": 0xE0, "comment": "IPU Channel 1 Timer status register A (high)"},
		0xFF23: {"name": "IPU1_T1SRAL",  "type": "byte", "initial": 0xE0, "comment": "IPU Channel 1 Timer status register A (low)"},
		0xFF24: {"name": "IPU1_T1OERA",  "type": "byte", "initial": 0x00, "comment": "IPU Channel 1 Timer output enable register A"},
		0xFF25: {"name": "IPU1_TMDRA",   "type": "byte", "initial": 0x00, "comment": "IPU Channel 1 Timer mode register A"},
		0xFF26: {"name": "IPU1_T1CNTH",  "type": "byte", "initial": 0x00, "comment": "IPU Channel 1 Timer counter register A (high)"},
		0xFF27: {"name": "IPU1_T1CNTL",  "type": "byte", "initial": 0x00, "comment": "IPU Channel 1 Timer counter register A (low)"},
		0xFF28: {"name": "IPU1_T1GR1H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 1 General register 1 (high)"},
		0xFF29: {"name": "IPU1_T1GR1L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 1 General register 1 (low)"},
		0xFF2A: {"name": "IPU1_T1GR2H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 1 General register 2 (high)"},
		0xFF2B: {"name": "IPU1_T1GR2L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 1 General register 2 (low)"},
		0xFF2C: {"name": "IPU1_T1DR1H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 1 Dedicated register 1 (high)"},
		0xFF2D: {"name": "IPU1_T1DR1L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 1 Dedicated register 1 (low)"},
		0xFF2E: {"name": "IPU1_T1DR2H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 1 Dedicated register 2 (high)"},
		0xFF2F: {"name": "IPU1_T1DR2L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 1 Dedicated register 2 (low)"},
		0xFF30: {"name": "IPU1_TSTR",    "type": "byte", "initial": 0x80, "comment": "IPU Channel 1 Timer start register"},
		0xFF31: {"name": "IPU1_T1CRA",   "type": "byte", "initial": 0xF0, "comment": "IPU Channel 1 Timer control register A"},
		0xFF32: {"name": "IPU1_T1SRBH",  "type": "byte", "initial": 0xF0, "comment": "IPU Channel 1 Timer status register B (high)"},
		0xFF33: {"name": "IPU1_T1SRBL",  "type": "byte", "initial": 0xF0, "comment": "IPU Channel 1 Timer status register B (low)"},
		0xFF34: {"name": "IPU1_T1OERB",  "type": "byte", "initial": 0x00, "comment": "IPU Channel 1 Timer output enable register B"},
		0xFF35: {"name": "IPU1_TMDRB",   "type": "byte", "initial": 0xC0, "comment": "IPU Channel 1 Timer mode register B"},
		0xFF38: {"name": "IPU1_T1GR3H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 1 General register 3 (high)"},
		0xFF39: {"name": "IPU1_T1GR3L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 1 General register 3 (low)"},
		0xFF3A: {"name": "IPU1_T1GR4H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 1 General register 4 (high)"},
		0xFF3B: {"name": "IPU1_T1GR4L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 1 General register 4 (low)"},
		0xFF3C: {"name": "IPU1_T1DR3H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 3 Dedicated register 1 (high)"},
		0xFF3D: {"name": "IPU1_T1DR3L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 3 Dedicated register 1 (low)"},
		0xFF3E: {"name": "IPU1_T1DR4H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 4 Dedicated register 1 (high)"},
		0xFF3F: {"name": "IPU1_T1DR4L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 4 Dedicated register 1 (low)"},
		0xFF40: {"name": "IPU2_T2CRH",   "type": "byte", "initial": 0xC0, "comment": "IPU Channel 2 Timer control register (high)"},
		0xFF41: {"name": "IPU2_T2CRL",   "type": "byte", "initial": 0xC0, "comment": "IPU Channel 2 Timer control register (low)"},
		0xFF42: {"name": "IPU2_T2SRH",   "type": "byte", "initial": 0xE0, "comment": "IPU Channel 2 Timer status register (high)"},
		0xFF43: {"name": "IPU2_T2SRL",   "type": "byte", "initial": 0xE0, "comment": "IPU Channel 2 Timer status register (low)"},
		0xFF44: {"name": "IPU2_T2OER",   "type": "byte", "initial": 0x00, "comment": "IPU Channel 2 Timer output enable register"},
		0xFF46: {"name": "IPU2_T2CNTH",  "type": "byte", "initial": 0x00, "comment": "IPU Channel 2 Timer counter register (high)"},
		0xFF47: {"name": "IPU2_T2CNTL",  "type": "byte", "initial": 0x00, "comment": "IPU Channel 2 Timer counter register (low)"},
		0xFF48: {"name": "IPU2_T2GR1H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 2 General register 1 (high)"},
		0xFF49: {"name": "IPU2_T2GR1L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 2 General register 1 (low)"},
		0xFF4A: {"name": "IPU2_T2GR2H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 2 General register 2 (high)"},
		0xFF4B: {"name": "IPU2_T2GR2L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 2 General register 2 (low)"},
		0xFF4C: {"name": "IPU2_T2DR1H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 2 Dedicated register 1 (high)"},
		0xFF4D: {"name": "IPU2_T2DR1L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 2 Dedicated register 1 (low)"},
		0xFF4E: {"name": "IPU2_T2DR2H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 2 Dedicated register 2 (high)"},
		0xFF4F: {"name": "IPU2_T2DR2L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 2 Dedicated register 2 (low)"},
		0xFF50: {"name": "IPU3_T3CRH",   "type": "byte", "initial": 0xC0, "comment": "IPU Channel 3 Timer control register (high)"},
		0xFF51: {"name": "IPU3_T3CRL",   "type": "byte", "initial": 0xC0, "comment": "IPU Channel 3 Timer control register (low)"},
		0xFF52: {"name": "IPU3_T3SRH",   "type": "byte", "initial": 0xE0, "comment": "IPU Channel 3 Timer status register (high)"},
		0xFF53: {"name": "IPU3_T3SRL",   "type": "byte", "initial": 0xE0, "comment": "IPU Channel 3 Timer status register (low)"},
		0xFF54: {"name": "IPU3_T3OER",   "type": "byte", "initial": 0x00, "comment": "IPU Channel 3 Timer output enable register"},
		0xFF56: {"name": "IPU3_T3CNTH",  "type": "byte", "initial": 0x00, "comment": "IPU Channel 3 Timer counter register (high)"},
		0xFF57: {"name": "IPU3_T3CNTL",  "type": "byte", "initial": 0x00, "comment": "IPU Channel 3 Timer counter register (low)"},
		0xFF58: {"name": "IPU3_T3GR1H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 3 General register 1 (high)"},
		0xFF59: {"name": "IPU3_T3GR1L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 3 General register 1 (low)"},
		0xFF5A: {"name": "IPU3_T3GR2H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 3 General register 2 (high)"},
		0xFF5B: {"name": "IPU3_T3GR2L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 3 General register 2 (low)"},
		0xFF5C: {"name": "IPU3_T3DR1H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 3 Dedicated register 1 (high)"},
		0xFF5D: {"name": "IPU3_T3DR1L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 3 Dedicated register 1 (low)"},
		0xFF5E: {"name": "IPU3_T3DR2H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 3 Dedicated register 2 (high)"},
		0xFF5F: {"name": "IPU3_T3DR2L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 3 Dedicated register 2 (low)"},
		0xFF60: {"name": "IPU4_T4CRH",   "type": "byte", "initial": 0xC0, "comment": "IPU Channel 4 Timer control register (high)"},
		0xFF61: {"name": "IPU4_T4CRL",   "type": "byte", "initial": 0xC0, "comment": "IPU Channel 4 Timer control register (low)"},
		0xFF62: {"name": "IPU4_T4SRH",   "type": "byte", "initial": 0xE0, "comment": "IPU Channel 4 Timer status register (high)"},
		0xFF63: {"name": "IPU4_T4SRL",   "type": "byte", "initial": 0xE0, "comment": "IPU Channel 4 Timer status register (low)"},
		0xFF64: {"name": "IPU4_T4OER",   "type": "byte", "initial": 0x00, "comment": "IPU Channel 4 Timer output enable register"},
		0xFF66: {"name": "IPU4_T4CNTH",  "type": "byte", "initial": 0x00, "comment": "IPU Channel 4 Timer counter register (high)"},
		0xFF67: {"name": "IPU4_T4CNTL",  "type": "byte", "initial": 0x00, "comment": "IPU Channel 4 Timer counter register (low)"},
		0xFF68: {"name": "IPU4_T4GR1H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 4 General register 1 (high)"},
		0xFF69: {"name": "IPU4_T4GR1L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 4 General register 1 (low)"},
		0xFF6A: {"name": "IPU4_T4GR2H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 4 General register 2 (high)"},
		0xFF6B: {"name": "IPU4_T4GR2L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 4 General register 2 (low)"},
		0xFF6C: {"name": "IPU4_T4DR1H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 4 Dedicated register 1 (high)"},
		0xFF6D: {"name": "IPU4_T4DR1L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 4 Dedicated register 1 (low)"},
		0xFF6E: {"name": "IPU4_T4DR2H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 4 Dedicated register 2 (high)"},
		0xFF6F: {"name": "IPU4_T4DR2L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 4 Dedicated register 2 (low)"},
		0xFF70: {"name": "IPU5_T5CRH",   "type": "byte", "initial": 0xC0, "comment": "IPU Channel 5 Timer control register (high)"},
		0xFF71: {"name": "IPU5_T5CRL",   "type": "byte", "initial": 0xC0, "comment": "IPU Channel 5 Timer control register (low)"},
		0xFF72: {"name": "IPU5_T5SRH",   "type": "byte", "initial": 0xE0, "comment": "IPU Channel 5 Timer status register (high)"},
		0xFF73: {"name": "IPU5_T5SRL",   "type": "byte", "initial": 0xE0, "comment": "IPU Channel 5 Timer status register (low)"},
		0xFF74: {"name": "IPU5_T5OER",   "type": "byte", "initial": 0x00, "comment": "IPU Channel 5 Timer output enable register"},
		0xFF76: {"name": "IPU5_T5CNTH",  "type": "byte", "initial": 0x00, "comment": "IPU Channel 5 Timer counter register (high)"},
		0xFF77: {"name": "IPU5_T5CNTL",  "type": "byte", "initial": 0x00, "comment": "IPU Channel 5 Timer counter register (low)"},
		0xFF78: {"name": "IPU5_T5GR1H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 5 General register 1 (high)"},
		0xFF79: {"name": "IPU5_T5GR1L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 5 General register 1 (low)"},
		0xFF7A: {"name": "IPU5_T5GR2H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 5 General register 2 (high)"},
		0xFF7B: {"name": "IPU5_T5GR2L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 5 General register 2 (low)"},
		0xFF7C: {"name": "IPU5_T5DR1H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 5 Dedicated register 1 (high)"},
		0xFF7D: {"name": "IPU5_T5DR1L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 5 Dedicated register 1 (low)"},
		0xFF7E: {"name": "IPU5_T5DR2H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 5 Dedicated register 2 (high)"},
		0xFF7F: {"name": "IPU5_T5DR2L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 5 Dedicated register 2 (low)"},
		0xFF80: {"name": "IPU6_T6CRH",   "type": "byte", "initial": 0xC0, "comment": "IPU Channel 6 Timer control register (high)"},
		0xFF81: {"name": "IPU6_T6CRL",   "type": "byte", "initial": 0xC0, "comment": "IPU Channel 6 Timer control register (low)"},
		0xFF82: {"name": "IPU6_T6SRH",   "type": "byte", "initial": 0xF8, "comment": "IPU Channel 6 Timer status register (high)"},
		0xFF83: {"name": "IPU6_T6SRL",   "type": "byte", "initial": 0xF8, "comment": "IPU Channel 6 Timer status register (low)"},
		0xFF84: {"name": "IPU6_T6OER",   "type": "byte", "initial": 0xF0, "comment": "IPU Channel 6 Timer output enable register"},
		0xFF86: {"name": "IPU6_T6CNTH",  "type": "byte", "initial": 0x00, "comment": "IPU Channel 6 Timer counter register (high)"},
		0xFF87: {"name": "IPU6_T6CNTL",  "type": "byte", "initial": 0x00, "comment": "IPU Channel 6 Timer counter register (low)"},
		0xFF88: {"name": "IPU6_T6GR1H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 6 General register 1 (high)"},
		0xFF89: {"name": "IPU6_T6GR1L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 6 General register 1 (low)"},
		0xFF8A: {"name": "IPU6_T6GR2H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 6 General register 2 (high)"},
		0xFF8B: {"name": "IPU6_T6GR2L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 6 General register 2 (low)"},
		0xFF90: {"name": "IPU7_T7CRH",   "type": "byte", "initial": 0xC0, "comment": "IPU Channel 6 Timer control register (high)"},
		0xFF91: {"name": "IPU7_T7CRL",   "type": "byte", "initial": 0xC0, "comment": "IPU Channel 6 Timer control register (low)"},
		0xFF92: {"name": "IPU7_T7SRH",   "type": "byte", "initial": 0xF8, "comment": "IPU Channel 6 Timer status register (high)"},
		0xFF93: {"name": "IPU7_T7SRL",   "type": "byte", "initial": 0xF8, "comment": "IPU Channel 6 Timer status register (low)"},
		0xFF94: {"name": "IPU7_T7OER",   "type": "byte", "initial": 0xF0, "comment": "IPU Channel 6 Timer output enable register"},
		0xFF96: {"name": "IPU7_T7CNTH",  "type": "byte", "initial": 0x00, "comment": "IPU Channel 6 Timer counter register (high)"},
		0xFF97: {"name": "IPU7_T7CNTL",  "type": "byte", "initial": 0x00, "comment": "IPU Channel 6 Timer counter register (low)"},
		0xFF98: {"name": "IPU7_T7GR1H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 6 General register 1 (high)"},
		0xFF99: {"name": "IPU7_T7GR1L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 6 General register 1 (low)"},
		0xFF9A: {"name": "IPU7_T7GR2H",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 6 General register 2 (high)"},
		0xFF9B: {"name": "IPU7_T7GR2L",  "type": "byte", "initial": 0xFF, "comment": "IPU Channel 6 General register 2 (low)"},
		0xFFA0: {"name": "MULT_MLTCR",   "type": "byte", "initial": 0x38, "comment": "MULT control register"},
		0xFFA1: {"name": "MULT_MLTBR",   "type": "byte", "initial": 0x00, "comment": "MULT base address register"},
		0xFFA2: {"name": "MULT_MLTMAR",  "type": "byte", "initial": 0x00, "comment": "MULT multiplier address register"},
		0xFFA3: {"name": "MULT_MLTAR",   "type": "byte", "initial": 0x00, "comment": "MULT multiplicand address register"},
		0xFFB0: {"name": "MULT_CA",      "type": "word", "initial": 0x00, "comment": "MULT multiplier register A"},
		0xFFB2: {"name": "MULT_CB",      "type": "word", "initial": 0x00, "comment": "MULT multiplier register B"},
		0xFFB4: {"name": "MULT_CC",      "type": "word", "initial": 0x00, "comment": "MULT multiplier register C"},
		0xFFB6: {"name": "MULT_XH",      "type": "word", "initial": 0xFFFF, "comment": "MULT result register, extended high word"},
		0xFFB8: {"name": "MULT_H",       "type": "word", "initial": 0xFFFF, "comment": "MULT result register, high word"},
		0xFFBA: {"name": "MULT_L",       "type": "word", "initial": 0xFFFF, "comment": "MULT result register, low word"},
		0xFFBC: {"name": "MULT_MR",      "type": "word", "initial": 0x0000, "comment": "MULT immediate multiplier register"},
		0xFFBE: {"name": "MULT_MMR",     "type": "word", "initial": 0x0000, "comment": "MULT immediate multiplicand register"},
	}

	#Loop through register dictionary
	for key, value in registers.iteritems():
		#Print the values being using for debugging purposes
		print str(key) + " " + value["name"] + " " + value["comment"]

		#Register key is the address. Check what type of register we need to make
		if (value["type"] == "word"):
			MakeWord(key)
			PatchWord(key, value["initial"])

		else:
			MakeByte(key)
			PatchByte(key, value["initial"])

		#Name the byte in IDA
		MakeNameEx(key, value["name"], SN_NOLIST)

		#Add comment to byte in IDA
		MakeComm(key, value["comment"])

def createMutTable(startAddress, endAddress):
	labelDict = {
		"MUT_04": ["TimingAdv_inter", "Timing Advance Interpolated"],
		"MUT_06": ["TimingAdv_scal", "Timing Advance Scaled"],
		"MUT_06": ["TimingAdv", "Timing Advance"],
		"MUT_07": ["CoolantTemp", "Coolant Temp"],
		"MUT_0C": ["LTFTLo", "Fuel Trim Low (LTFT]"],
		"MUT_0D": ["LTFTMid", "Fuel Trim Mid (LTFT]"],
		"MUT_0E": ["LTFTHigh", "Fuel Trim High (LTFT]"],
		"MUT_0F": ["STFT", "Oxygen Feedback Trim (STFT]"],
		"MUT_10": ["CoolantTempScaled", "Coolant Temp Scaled"],
		"MUT_11": ["MAFAirTempScaled", "MAF Air Temp Scaled"],
		"MUT_12": ["EGRTemp", "EGR Temperature"],
		"MUT_13": ["O2Sensor", "Front Oxygen Sensor"],
		"MUT_14": ["Battery", "Battery Level"],
		"MUT_15": ["Baro", "Barometer"],
		"MUT_16": ["ISCSteps", "ISC Steps"],
		"MUT_17": ["TPS", "Throttle Position"],
		"MUT_18": ["open_loop_bit_array", "Open Loop Bit Array"],
		"MUT_19": ["startup_check_bits", "Startup Check Bits"],
		"MUT_1A": ["AirFlow", "Air Flow - (TPS Idle Adder ?]"],
		"MUT_1A": ["TPS_idle_adder", "TPS Idle Adder"],
		"MUT_1C": ["Load", "ECULoad"],
		"MUT_1D": ["AccelEnrich", "Acceleration Enrichment - (Manifold_Absolute_Pressure_Mean ?]"],
		"MUT_1F": ["PrevLoad", "ECU Load Previous"],
		"MUT_20": ["RPM_Idle_Scaled", "Engine RPM Idle Scaled"],
		"MUT_21": ["RPM", "Engine RPM"],
		"MUT_22": ["idle_value_??", "Idle Related Value (unknown]"],
		"MUT_24": ["TargetIdleRPM", "Target Idle RPM"],
		"MUT_25": ["ISCV_Value", "Idle Stepper Value"],
		"MUT_26": ["KnockSum", "Knock Sum"],
		"MUT_27": ["OctaneFlag", "Octane Level"],
		"MUT_29": ["InjPulseWidth", "Injector Pulse Width (LSB]"],
		"MUT_2A": ["InjPulseWidth", "Injector Pulse Width (MSB]"],
		"MUT_2C": ["AirVol", "Air Volume"],
		"MUT_2D": ["Ign_bat_trim", "Ignition Battery Trim"],
		"MUT_2E": ["speed_freq", "Vehicle speed Frequency"],
		"MUT_2F": ["Speed", "Speed"],
		"MUT_30": ["Knock", "Knock Voltage"],
		"MUT_31": ["VE", "Volumetric Efficiency"],
		"MUT_32": ["AFRMAP", "Air/Fuel Ratio (Map reference]"],
		"MUT_33": ["Corr_TimingAdv", "Corrected Timing Advance"],
		"MUT_34": ["map_index", "MAP Index"],
		"MUT_35": ["limp_fuel_tps", "Limp Home Fuel TPS Based"],
		"MUT_36": ["active_faults", "Active Fault Count"],
		"MUT_37": ["Stored_Fault_Count", "Count"],
		"MUT_38": ["MAP", "Boost (MDP]"],
		"MUT_39": ["fuel_tabk_pres", "Fuel Tank Pressure"],
		"MUT_3A": ["UnscaledAirTemp", "Unscaled Air Temperature"],
		"MUT_3B": ["masked_map_index", "Masked Map Index"],
		"MUT_3C": ["rear_02_1", "Rear Oxygen Sensor #1"],
		"MUT_3D": ["front_02_2", "Front Oxygen Sensor #2"],
		"MUT_3E": ["rear_02_2", "Rear Oxygen Sensor #2"],
		"MUT_3F": ["STFT_02_map_index", "Short Term Fuel Feedback Trim O2 Map Index"],
		"MUT_40": ["Stored_faults_low", "Stored Faults Lo"],
		"MUT_41": ["stored_faults_high", "Stored Faults Hi"],
		"MUT_42": ["stored_faults_low_1", "Stored Faults Lo 1"],
		"MUT_43": ["stored_faults_high_1", "Stored Faults Hi 1"],
		"MUT_44": ["stored_faults_low_2", "Stored Faults Lo 2"],
		"MUT_45": ["stored_faults_high_2", "Stored Faults Hi 2"],
		"MUT_47": ["active_faults_low", "Active Faults Lo"],
		"MUT_48": ["active_faults_high", "Active Faults Hi"],
		"MUT_49": ["ACRelaySw", "Air Conditioning Relay"],
		"MUT_4A": ["PurgeDuty", "Purge Solenoid Duty Cycle"],
		"MUT_4C": ["", "Fuel Trim Low Bank 2"],
		"MUT_4D": ["", "Fuel Trim Mid Bank 2"],
		"MUT_4E": ["", "Fuel Trim High Bank 2"],
		"MUT_4F": ["", "Oxygen Feedback Trim Bank 2"],
		"MUT_50": ["", "Long Fuel Trim Bank 1"],
		"MUT_51": ["", "Long Fuel Trim Bank 2"],
		"MUT_52": ["", "Rear Long Fuel Trim Bank 1"],
		"MUT_53": ["", "Rear Long Fuel Trim Bank 2"],
		"MUT_54": ["AccelEnrichTPS", "Acceleration Enrichment (increasing TPS]"],
		"MUT_55": ["DecelLeanTPS", "Deceleration Enleanment (decreasing TPS]"],
		"MUT_56": ["AccelLoadChg", "Acceleration Load Change"],
		"MUT_57": ["DecelLoadChg", "Deceleration Load Change"],
		"MUT_58": ["", "AFR Ct Adder"],
		"MUT_5B": ["", "Rear O2 Voltage"],
		"MUT_5C": ["", "ADC Rear O2 Voltage"],
		"MUT_60": ["", "Rear O2 Trim - Low"],
		"MUT_61": ["", "Rear O2 Trim - Mid"],
		"MUT_62": ["", "Rear O2 Trim - High"],
		"MUT_63": ["", "Rear O2 Feedback Trim"],
		"MUT_6A": ["knock_adc", "knock adc processed"],
		"MUT_6B": ["knock_base", "knock base"],
		"MUT_6C": ["knock_var", "knock var (AKA Knock Sum Addition]"],
		"MUT_6D": ["knock_change", "knock change"],
		"MUT_6E": ["knock_dynamics", "knock dynamics"],
		"MUT_6F": ["knock_flag", "knock flag (AKA Knock Acceleration]"],
		"MUT_70": ["", "Array of Serial Receive Data Register 2 RDR 2 Values"],
		"MUT_71": ["", "Sensor Error"] ,"MUT_72": ["", "Knock Present"],
		"MUT_73": ["", "Throttle Position Delta 1"],
		"MUT_74": ["", "Throttle Position Delta 2"],
		"MUT_76": ["ISCV_%_Demand", "ISCV % Demand (Columns]"],
		"MUT_79": ["InjectorLatency", "Injector Latency"],
		"MUT_7A": ["", "Continuous Monitor Completion Status 1"],
		"MUT_7B": ["", "Continuous Monitor Completion Status 2"],
		"MUT_7C": ["", "Continuous Monitor Completion Status 3"],
		"MUT_7D": ["", "Non Continuous Monitor Completion Status OBD"],
		"MUT_7E": ["", "Continuous Monitor Completion Status Low 4"],
		"MUT_7F": ["", "Continuous Monitor Completion Status High 4"],
		"MUT_80": ["", "ECU ID Type (LSB]"],
		"MUT_81": ["", "ECU ID Type (MSB]"],
		"MUT_82": ["", "ECU ID Version"],
		"MUT_83": ["", "ADC Channel F"],
		"MUT_84": ["ThermoFanDuty", "Thermo Fan Dutycycle"],
		"MUT_85": ["EgrDuty", "EGR Dutycycle"],
		"MUT_86": ["WGDC", "Wastegate Duty Cycle"],
		"MUT_87": ["FuelTemperature", "Fuel Temperature"],
		"MUT_88": ["FuelLevel", "Fuel Level"],
		"MUT_89": ["", "ADC Channel 8 2"],
		"MUT_8A": ["LoadError", "Load Error - (Throttle Position Corrected ?]"],
		"MUT_8B": ["WGDCCorr", "WGDC Correction"],
		"MUT_8E": ["", "Solenoid Duty"],
		"MUT_90": ["", "Timer Status Register 9 TSR9"],
		"MUT_96": ["MAF_ADC", "RAW MAF ADC value"],
		"MUT_9A": ["ACClutch", "AC clutch"],
		"MUT_9B": ["", "Output Pins"],
		"MUT_A2": ["CrankPulse", "Crankshaft sensor pulse"],
		"MUT_A2": ["MafPulse", "MAF sensor pulse"],
		"MUT_A2": ["CamPulse", "Camshaft sensor pulse"],
		"MUT_A8": ["ATInShaftPulse", "Input shaft speed pulse (A/T]"],
		"MUT_A8": ["ATOutShaftPulse", "Output shaft speed pulse (A/T]"],
		"MUT_A8": ["ATGearL", "Gear: Low (A/T]"],
		"MUT_A8": ["ATGear2", "Gear: 2 (A/T]"],
		"MUT_A8": ["ATGear3", "Gear: 3 (A/T]"],
		"MUT_A9": ["O2HeaterFrontLeft", "Front O2 heater bank 1 (left]"],
		"MUT_A9": ["O2HeaterRearLeft", "Rear O2 heater bank 1 (left]"],
		"MUT_A9": ["O2HeaterFrontRight", "Front O2 heater bank 2 (right]"],
		"MUT_A9": ["O2HeaterRearRight", "Rear O2 heater bank 2 (right]"],
		"MUT_AA": ["Braking", "Brakes Pressed"],
		"MUT_B3": ["ATGearNeutral", "Gear: Neutral (A/T]"],
		"MUT_B3": ["ATGearDrive", "Gear: Drive (A/T]"],
		"MUT_B4": ["ATGearPark", "Gear: Park (A/T]"],
		"MUT_B4": ["ATGearRev", "Gear: Reverse (A/T]"],
		"MUT_B7": ["O2HeaterBrokenFrRt", "front O2 heater circuit open (broken]: bank 2 (right]"],
		"MUT_B8": ["O2HeaterBrokenFrLt", "front O2 heater circuit open (broken]: bank 1 (left]"],
		"MUT_B8": ["NewACSwitch", "Air Conditioning Switch (Mattjin]"],
		"MUT_B8": ["PowerSteering", "Power Steering"],
		"MUT_B9": ["O2HeaterBrokenRearRt", "rear O2 heater circuit open (broken]: bank 2 (right]"],
		"MUT_BA": ["O2HeaterBrokenRearLt", "rear O2 heater circuit open (broken]: bank 1 (left]"],
		"MUT_C3": ["", "SAS (Speed Adjusting Screw]"],
		"MUT_C5": ["", "Purge solenoid venting"],
		"MUT_CA": ["", "Invalid command"],
		"MUT_CB": ["", "Invalid command"],
		"MUT_CD": ["", "A/C fan high"],
		"MUT_CE": ["", "A/C fan low"],
		"MUT_CF": ["", "Main fan high"],
		"MUT_D0": ["", "Main fan low"],
		"MUT_D2": ["", "Lower RPM"],
		"MUT_D3": ["", "Boost control solenoid"],
		"MUT_D5": ["", "EGR solenoid"],
		"MUT_D6": ["", "Fuel pressure solenoid"],
		"MUT_D7": ["", "Purge solenoid"],
		"MUT_D8": ["", "Fuel pump"],
		"MUT_D9": ["", "Fix timing at 5 degrees"],
		"MUT_DA": ["", "Disable injector 1"],
		"MUT_DB": ["", "Disable injector 2"],
		"MUT_DC": ["", "Disable injector 3"],
		"MUT_DD": ["", "Disable injector 4"],
		"MUT_DE": ["", "Disable injector 5 (unused]"],
		"MUT_DF": ["", "Disable injector 6 (unused]"],
		"MUT_EC": ["", "Calibration F6A"],
		"MUT_ED": ["", "Calibration"],
		"MUT_EE": ["", "Calibration"],
		"MUT_EF": ["", "Calibration"],
		"MUT_F3": ["", "Cancel previously-active command (ie. SAS mode]"],
		"MUT_F9": ["", "some keep alive function to keep the accuator engaged. response is 0xff"],
		"MUT_FA": ["", "Clear active and stored faults"] ,"MUT_FB": ["", "Force tests to run"],
		"MUT_FC": ["", "Clear active faults"],
		"MUT_FE": ["", "Immobilizer"],
		"MUT_FF": ["", "Init code"]
	}

	counter = 0
	currentAddress = startAddress

	while (currentAddress <= endAddress):
		MakeWord(currentAddress)

		name = "MUT_%02X" % counter
		print name

		value = Word(currentAddress)
		print "%04X" % value

		MakeNameEx(currentAddress, name, SN_CHECK)
		#add_dref(currentAddress, value, dr_R)

		if((value % 2) != 0):
			value = value - 1
			MakeWord(value)

		if(labelDict.has_key(name)):
			if(labelDict[name][0] != ""):
				print labelDict[name][0]
				MakeNameEx(value, labelDict[name][0], SN_CHECK)

			if(labelDict[name][1] != ""):
				print labelDict[name][1]
				MakeComm(value, labelDict[name][1])
				MakeComm(currentAddress, labelDict[name][1])

		currentAddress = currentAddress + 2
		counter = counter + 1

	print "finished"

#main
loadFile()
createSegments()
createStructs()
LowVoids(0)
HighVoids(0x1000)
labelRegisters()
createVTEntries()
createMutTable(0x2FAD0, 0x2FCEE)
labelKnownFunctions()
#labelKnownVars()
