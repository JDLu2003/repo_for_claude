# -*- coding: utf-8 -*-
"""RV32I 5-stage pipeline CPU block diagram generator (Visio style SVG) + geometry checker."""
import sys, html
import checker
W, H = 2800, 1880
REG_T, REG_B = 220, 960
comps, wires, texts = [], [], []

# ---------------------------------------------------------------- helpers
def comp(cid, kind, x, y, w, h, title, sub=None, ports=(), style=None, tsize=13):
    c = dict(id=cid, kind=kind, x=x, y=y, w=w, h=h, title=title, sub=sub, ports=list(ports), style=style or kind, tsize=tsize)
    comps.append(c); return c

def wire(net, pts, kind='data', label=None, lp=None, anchor='start', arrow=True, dot_start=None):
    wires.append(dict(net=net, pts=pts, kind=kind, label=label, lp=lp, anchor=anchor, arrow=arrow, dot=dot_start))

def text(x, y, s, size=11, anchor='start', color='#222', weight='normal', italic=False, family=None):
    texts.append(dict(x=x, y=y, s=s, size=size, anchor=anchor, color=color, weight=weight, italic=italic, family=family))

# ---------------------------------------------------------------- stage geometry
ST = [('IF  取指', 20, 470, '#dae8fc'), ('ID  译码/读寄存器', 540, 1130, '#d5e8d4'), ('EX  执行', 1200, 2040, '#ffe6cc'),
      ('MEM  访存', 2110, 2460, '#e1d5e7'), ('WB  写回', 2530, 2780, '#f8cecc')]
PREG = [('IF/ID', 470), ('ID/EX', 1130), ('EX/MEM', 2040), ('MEM/WB', 2460)]
PW = 70

# ---------------------------------------------------------------- rows (y of signals through pipeline regs)
R = dict(rd=238, MemRead=262, RegWrite=280, WBSel=298, MemWrite=316, Jump=334, Branch=352, Jalr=370,
         ALUSrcB=388, ALUSrcA=406, ALUOp=424, funct7=452, funct3=476, imm=510, pc=555, pc4=590,
         instr=640, rd1=665, rd2=765, rs1=896, rs2=914, alu=800, store=860, mem=840)
CTRL = ['MemRead', 'RegWrite', 'WBSel', 'MemWrite', 'Jump', 'Branch', 'Jalr', 'ALUSrcB', 'ALUSrcA', 'ALUOp']
CW = dict(MemRead='MemRead', RegWrite='RegWrite', WBSel='WBSel[1:0]', MemWrite='MemWrite', Jump='Jump', Branch='Branch',
          Jalr='Jalr', ALUSrcB='ALUSrcB', ALUSrcA='ALUSrcA[1:0]', ALUOp='ALUOp[1:0]')

# pipeline register fields  (name shown inside the register at the row)
PFIELDS = {
 'IF/ID': [('pc', R['pc']), ('pc4', R['pc4']), ('instr', R['instr'])],
 'ID/EX': [('rd', R['rd'])] + [(k if k not in ('MemRead','RegWrite','MemWrite') else {'MemRead':'MemRd','RegWrite':'RegWr','MemWrite':'MemWr'}[k], R[k]) for k in CTRL] +
          [('funct7[5]', R['funct7']), ('funct3', R['funct3']), ('imm', R['imm']), ('pc', R['pc']), ('pc4', R['pc4']),
           ('rs1_data', R['rd1']), ('rs2_data', R['rd2']), ('rs1', R['rs1']), ('rs2', R['rs2'])],
 'EX/MEM': [('rd', R['rd']), ('MemRd', R['MemRead']), ('RegWr', R['RegWrite']), ('WBSel', R['WBSel']), ('MemWr', R['MemWrite']),
            ('funct3', R['funct3']), ('pc4', R['pc4']), ('alu_res', R['alu']), ('st_data', R['store'])],
 'MEM/WB': [('rd', R['rd']), ('RegWr', R['RegWrite']), ('WBSel', R['WBSel']), ('pc4', R['pc4']), ('alu_res', R['alu']), ('rdata', R['mem'])],
}
for name, x in PREG:
    ports = []
    for f, y in PFIELDS[name]:
        ports += [('L', y, ''), ('R', y, '')]
    comp(name, 'preg', x, REG_T, PW, REG_B - REG_T, name, ports=ports)

# ================================================================= IF stage
comp('pcmux', 'mux', 60, 380, 30, 80, 'M', ports=[('L', 400, '0'), ('L', 440, '1'), ('R', 420, ''), ('T', 75, '')])
comp('pc', 'reg', 140, 390, 80, 60, 'PC', sub='', ports=[('L', 420, 'D'), ('R', 420, 'Q'), ('T', 180, 'en')])
comp('pcadd', 'adder', 290, 600, 50, 60, '+4', ports=[('L', 615, ''), ('L', 645, ''), ('R', 630, '')])
comp('imem', 'blk', 250, 690, 160, 110, 'Instruction Memory', sub='IMEM (ROM, 组合读)', ports=[('L', 720, 'addr'), ('R', R['instr'], '')])
# instr out port sits above imem? keep imem top below instr row -> use port at top-right corner via short wire
comp('haz', 'haz', 640, 118, 300, 66, 'Hazard Detection Unit', sub='load-use 检测 / 冲刷控制',
     ports=[('L', 132, ''), ('L', 148, ''), ('L', 164, ''), ('B', 680, 'rs1'), ('B', 710, 'rs2'), ('T', 800, 'pc_src'),
            ('R', 136, 'ID_EX.rd'), ('R', 152, 'ID_EX.MemRd'), ('R', 172, 'ID_EX_flush')])

# pc_f
wire('pc_f', [(220, 420), (245, 420), (245, R['pc']), (470, R['pc'])], label='pc_f[31:0]', lp=(300, R['pc'] - 5))
wire('pc_f', [(245, R['pc']), (245, 615), (290, 615)])
wire('pc_f', [(245, 615), (245, 720), (250, 720)])
text(262, 649, "4", 10, 'end', '#333'); wire('c4', [(265, 645), (290, 645)], kind='const')
wire('pc4_f', [(340, 630), (390, 630), (390, R['pc4']), (470, R['pc4'])], label='pc4_f', lp=(400, R['pc4'] - 5))
wire('pc4_f', [(390, R['pc4']), (390, 350), (40, 350), (40, 400), (60, 400)])
wire('pc_next', [(90, 420), (140, 420)], label='pc_next', lp=(94, 413))
# instr_f : imem out -> IF/ID
wire('instr_f', [(410, 745), (440, 745), (440, R['instr']), (470, R['instr'])], label='instr_f', lp=(413, 760))
# fix imem port for instr: use right side
comps[-1 if False else [c['id'] for c in comps].index('imem')]['ports'] = [('L', 720, 'addr'), ('R', 745, '')]

# ================================================================= top band: redirect + hazard
Y_TGT, Y_SRC = 98, 108
# pc_target (from EX target mux) and pc_src (from branch unit)
wire('pc_target', [(1990, R['pc'] - 9), (2025, R['pc'] - 9), (2025, Y_TGT), (25, Y_TGT), (25, 440), (60, 440)], label='pc_target[31:0]  (EX → IF 重定向地址)', lp=(1100, Y_TGT - 5))
wire('pc_src', [(2000, 343), (2010, 343), (2010, Y_SRC), (75, Y_SRC), (75, 385)], kind='haz', label='pc_src  (EX: 分支成立/跳转)', lp=(1100, Y_SRC + 12))
wire('pc_src', [(800, Y_SRC), (800, 118)], kind='haz')
# hazard outputs
wire('PCWrite', [(640, 132), (180, 132), (180, 390)], kind='haz', label='PCWrite = ~stall', lp=(250, 128))
wire('IF_ID_Write', [(640, 148), (490, 148), (490, REG_T)], kind='haz', label='IF_ID_en = ~stall', lp=(515, 144))
wire('IF_ID_Flush', [(640, 164), (520, 164), (520, REG_T)], kind='haz', label='IF_ID_flush = pc_src', lp=(527, 177))
wire('ID_EX_Flush', [(940, 172), (1165, 172), (1165, REG_T)], kind='haz', label='ID_EX_flush = stall | pc_src', lp=(955, 186))
wire('rd_e', [(1225, R['rd']), (1225, 136), (940, 136)], kind='haz', label='ID_EX.rd', lp=(1045, 132))
wire('c_MemRead', [(1210, R['MemRead']), (1210, 152), (940, 152)], kind='haz', label='ID_EX.MemRead', lp=(1045, 148))

# ================================================================= ID stage
TX = 600  # instruction trunk x
comp('ctrl', 'ctrl', 660, 250, 180, 184, 'Main Control', sub='主译码器 (opcode)', ports=[('L', 340, 'opcode')] + [('R', R[k], CW[k]) for k in CTRL])
comp('immgen', 'blk', 700, 490, 160, 40, 'Imm Gen', sub=None, ports=[('L', R['imm'], ''), ('R', R['imm'], '')], tsize=12)
comp('rf', 'rf', 700, 640, 180, 180, 'Register File', sub='32 x 32bit, x0≡0',
     ports=[('L', R['rd1'], 'ra1'), ('L', 695, 'ra2'), ('L', 740, 'wa'), ('L', 765, 'we'), ('L', 790, 'wd'),
            ('R', R['rd1'], 'rd1'), ('R', R['rd2'], 'rd2')])

# instr trunk
wire('instr_d', [(540, R['instr']), (TX, R['instr']), (TX, 196), (680, 196), (680, 184)], label='instr_d', lp=(543, R['instr'] + 14))
wire('instr_d', [(TX, 208), (710, 208), (710, 184)])
wire('instr_d', [(TX, R['rd']), (1130, R['rd'])], label='rd = instr[11:7]', lp=(870, R['rd'] - 5))
wire('instr_d', [(TX, 340), (660, 340)], label='[6:0]', lp=(605, 335))
wire('instr_d', [(TX, R['funct7']), (1130, R['funct7'])], label='funct7[5] = instr[30]', lp=(870, R['funct7'] - 5))
wire('instr_d', [(TX, R['funct3']), (1130, R['funct3'])], label='funct3 = instr[14:12]', lp=(870, R['funct3'] - 5))
wire('instr_d', [(TX, R['imm']), (700, R['imm'])], label='[31:0]', lp=(640, R['imm'] - 5))
wire('instr_d', [(TX, R['instr']), (TX, R['rs2']), (1130, R['rs2'])], label='rs2 = instr[24:20]', lp=(870, R['rs2'] - 5))
wire('instr_d', [(TX, R['rs1']), (1130, R['rs1'])], label='rs1 = instr[19:15]', lp=(870, R['rs1'] - 5))
wire('instr_d', [(TX, R['rd1']), (700, R['rd1'])], label='[19:15]', lp=(640, R['rd1'] - 5))
wire('instr_d', [(TX, 695), (700, 695)], label='[24:20]', lp=(640, 690))
text(718, 204, 'IF_ID.rs1 = instr[19:15],  IF_ID.rs2 = instr[24:20]', 9, 'start', '#555')
for k in CTRL:
    wire('c_' + k, [(840, R[k]), (1130, R[k])], kind='ctrl')
wire('imm_d', [(860, R['imm']), (1130, R['imm'])], label='imm_d[31:0]', lp=(880, R['imm'] - 5))
wire('pc_d', [(540, R['pc']), (1130, R['pc'])], label='pc_d', lp=(1060, R['pc'] - 5))
wire('pc4_d', [(540, R['pc4']), (1130, R['pc4'])], label='pc4_d', lp=(1060, R['pc4'] - 5))
wire('rd1_d', [(880, R['rd1']), (1130, R['rd1'])], label='rs1_data_d[31:0]', lp=(900, R['rd1'] - 5))
wire('rd2_d', [(880, R['rd2']), (1130, R['rd2'])], label='rs2_data_d[31:0]', lp=(900, R['rd2'] - 5))

# ================================================================= WB feedback channels (bottom band)
Y_WD, Y_WE, Y_WA = 1000, 1015, 1030
wire('wb_data', [(2650, 715), (2700, 715), (2700, Y_WD), (585, Y_WD), (585, 790), (700, 790)], label='wb_data[31:0]  (WB → 寄存器堆写数据 / 前递)', lp=(1900, Y_WD - 5))
wire('MEM_WB.RegWrite', [(2530, R['RegWrite']), (2720, R['RegWrite']), (2720, Y_WE), (570, Y_WE), (570, 765), (700, 765)], kind='ctrl', label='MEM_WB.RegWrite', lp=(1900, Y_WE - 4))
wire('MEM_WB.rd', [(2530, R['rd']), (2740, R['rd']), (2740, Y_WA), (555, Y_WA), (555, 740), (700, 740)], kind='idx', label='MEM_WB.rd[4:0]', lp=(1900, Y_WA + 12))

# ================================================================= EX stage
comp('fmA', 'mux', 1260, 645, 30, 80, 'M', ports=[('L', R['rd1'], '0'), ('L', 685, '1'), ('L', 705, '2'), ('R', 685, ''), ('B', 1275, '')])
comp('fmB', 'mux', 1320, 745, 30, 80, 'M', ports=[('L', R['rd2'], '0'), ('L', 785, '1'), ('L', 805, '2'), ('R', 785, ''), ('B', 1335, '')])
comp('fwd', 'fwd', 1260, 880, 210, 70, 'Forwarding Unit', sub='前递单元',
     ports=[('L', R['rs1'], 'rs1'), ('L', R['rs2'], 'rs2'), ('T', 1275, ''), ('T', 1335, ''), ('B', 1350, 'EXrw'), ('B', 1385, 'EXrd'), ('B', 1420, 'WBrd'), ('B', 1455, 'WBrw')])
comp('smA', 'mux', 1450, 645, 30, 80, 'M', ports=[('L', 665, '1'), ('L', 685, '0'), ('L', 705, '2'), ('R', 685, ''), ('T', 1465, '')])
comp('smB', 'mux', 1510, 745, 30, 80, 'M', ports=[('L', 765, '1'), ('L', 785, '0'), ('R', 785, ''), ('T', 1525, '')])
comp('alu', 'alu', 1600, 630, 80, 200, 'ALU', ports=[('L', 685, 'A'), ('L', 785, 'B'), ('T', 1640, ''), ('R', 700, 'zero'), ('R', 745, 'Y')])
comp('aludec', 'blk', 1560, 398, 140, 64, 'ALU Decoder', sub='ALU 控制译码', ports=[('L', R['ALUOp'], 'ALUOp'), ('L', R['funct7'], 'f7[5]'), ('B', 1600, 'f3'), ('B', 1640, 'ALUCtl')], tsize=12)
comp('badd', 'adder', 1720, 495, 50, 75, '+', ports=[('L', R['imm'], ''), ('L', R['pc'], ''), ('R', 532, '')])
comp('lsb', 'blk', 1720, 730, 100, 30, '& ~1', sub=None, ports=[('L', 745, ''), ('R', 745, '')], tsize=11)
comp('tmux', 'mux', 1960, 510, 30, 70, 'M', ports=[('L', 532, '0'), ('L', 560, '1'), ('R', R['pc'] - 9, ''), ('T', 1975, '')])
comp('bru', 'bru', 1860, 316, 140, 44, 'Branch Unit', sub=None, ports=[('L', R['Jump'], 'Jump'), ('L', R['Branch'], 'Br'), ('B', 1905, 'f3'), ('B', 1950, 'zero'), ('R', 343, '')], tsize=12)

# control rows in EX
for k in ['MemRead', 'RegWrite', 'WBSel', 'MemWrite']:
    wire('c_' + k, [(1200, R[k]), (2040, R[k])], kind='ctrl', label=CW[k] + '_e' if k != 'MemRead' else None, lp=(1250, R[k] - 4) if k != 'MemRead' else None)
text(1250, R['MemRead'] - 4, 'MemRead_e', 10, 'start', '#c55a11')
wire('c_Jump', [(1200, R['Jump']), (1860, R['Jump'])], kind='ctrl', label='Jump_e', lp=(1250, R['Jump'] - 4))
wire('c_Branch', [(1200, R['Branch']), (1860, R['Branch'])], kind='ctrl', label='Branch_e', lp=(1250, R['Branch'] - 4))
wire('c_Jalr', [(1200, R['Jalr']), (1975, R['Jalr']), (1975, 515)], kind='ctrl', label='Jalr_e', lp=(1250, R['Jalr'] - 4))
wire('c_ALUSrcB', [(1200, R['ALUSrcB']), (1525, R['ALUSrcB']), (1525, 750)], kind='ctrl', label='ALUSrcB_e', lp=(1250, R['ALUSrcB'] - 4))
wire('c_ALUSrcA', [(1200, R['ALUSrcA']), (1465, R['ALUSrcA']), (1465, 650)], kind='ctrl', label='ALUSrcA_e[1:0]', lp=(1250, R['ALUSrcA'] - 4))
wire('c_ALUOp', [(1200, R['ALUOp']), (1560, R['ALUOp'])], kind='ctrl', label='ALUOp_e[1:0]', lp=(1250, R['ALUOp'] - 4))
wire('rd_e', [(1200, R['rd']), (2040, R['rd'])], kind='idx', label='rd_e[4:0]', lp=(1250, R['rd'] - 4))
wire('funct7_e', [(1200, R['funct7']), (1560, R['funct7'])], label='funct7[5]_e', lp=(1250, R['funct7'] - 4))
wire('funct3_e', [(1200, R['funct3']), (2040, R['funct3'])], label='funct3_e[2:0]', lp=(1250, R['funct3'] - 4))
wire('funct3_e', [(1600, R['funct3']), (1600, 462)])
wire('funct3_e', [(1905, R['funct3']), (1905, 360)])
wire('ALUCtl', [(1640, 462), (1640, 655)], kind='ctrl', label='ALUCtl[3:0]', lp=(1645, 500))
wire('imm_e', [(1200, R['imm']), (1720, R['imm'])], label='imm_e[31:0]', lp=(1250, R['imm'] - 4))
wire('imm_e', [(1495, R['imm']), (1495, 765), (1510, 765)])
wire('pc_e', [(1200, R['pc']), (1720, R['pc'])], label='pc_e[31:0]', lp=(1250, R['pc'] - 4))
wire('pc_e', [(1435, R['pc']), (1435, 665), (1450, 665)])
text(1433, 709, "0", 10, 'end', '#333'); wire('c0', [(1438, 705), (1450, 705)], kind='const')
wire('pc4_e', [(1200, R['pc4']), (2040, R['pc4'])], label='pc4_e[31:0]', lp=(1250, R['pc4'] - 4))
wire('rd1_e', [(1200, R['rd1']), (1260, R['rd1'])])
wire('rd2_e', [(1200, R['rd2']), (1320, R['rd2'])])
wire('rs1_e', [(1200, R['rs1']), (1260, R['rs1'])], kind='idx')
wire('rs2_e', [(1200, R['rs2']), (1260, R['rs2'])], kind='idx')
wire('FwdA', [(1275, 880), (1275, 720)], kind='fwd', label='ForwardA[1:0]', lp=(1280, 739))
wire('FwdB', [(1335, 880), (1335, 820)], kind='fwd', label='ForwardB[1:0]', lp=(1340, 872))
wire('rs1f', [(1290, 685), (1450, 685)], label='rs1_fwd', lp=(1375, 680))
wire('rs2f', [(1350, 785), (1510, 785)], label='rs2_fwd', lp=(1420, 780))
wire('rs2f', [(1430, 785), (1430, R['store']), (2040, R['store'])], label='store_data (rs2_fwd)', lp=(1760, R['store'] - 5))
wire('opA', [(1480, 685), (1600, 685)], label='opA', lp=(1540, 680))
wire('opB', [(1540, 785), (1600, 785)], label='opB', lp=(1555, 780))
wire('alu_y', [(1680, 745), (1720, 745)])
wire('alu_y', [(1700, 745), (1700, R['alu']), (2040, R['alu'])], label='alu_result[31:0]', lp=(1760, R['alu'] - 5))
wire('zero', [(1680, 700), (1950, 700), (1950, 360)], kind='ctrl', label='zero', lp=(1690, 695))
wire('br_tgt', [(1770, 532), (1960, 532)], label='pc_e + imm_e', lp=(1800, 527))
wire('jalr_tgt', [(1820, 745), (1840, 745), (1840, 560), (1960, 560)], label='(rs1+imm)&~1', lp=(1845, 577))
# forward data feeds (from WB / MEM)
wire('wb_data', [(1232, Y_WD), (1232, 685), (1260, 685)])
wire('wb_data', [(1232, 785), (1320, 785)])
Y_XF, Y_XR, Y_XW = 972, 1045, 1060
wire('exm_fwd', [(2180, 680), (2200, 680), (2200, Y_XF), (1246, Y_XF), (1246, 705), (1260, 705)], label='exmem_fwd[31:0] (EX/MEM → 前递)', lp=(1730, Y_XF - 4))
wire('exm_fwd', [(1246, 805), (1320, 805)])

# ================================================================= MEM stage
comp('dmem', 'blk', 2230, 740, 150, 160, 'Data Memory', sub='DMEM (同步写, 组合读)',
     ports=[('L', R['alu'], 'addr'), ('L', R['store'], 'wdata'), ('T', 2260, 'f3'), ('T', 2300, 'we'), ('T', 2340, 're'), ('R', R['mem'], 'rdata')])
comp('xmux', 'mux', 2150, 640, 30, 80, 'M', ports=[('L', 660, '1'), ('L', 700, '0'), ('R', 680, ''), ('T', 2165, '')])
wire('c_MemRead', [(2110, R['MemRead']), (2340, R['MemRead']), (2340, 740)], kind='ctrl', label='MemRead_m', lp=(2180, R['MemRead'] - 4))
wire('c_RegWrite', [(2110, R['RegWrite']), (2460, R['RegWrite'])], kind='ctrl', label='RegWrite_m', lp=(2180, R['RegWrite'] - 4))
wire('c_WBSel', [(2110, R['WBSel']), (2460, R['WBSel'])], kind='ctrl', label='WBSel_m[1:0]', lp=(2180, R['WBSel'] - 4))
wire('c_WBSel', [(2165, R['WBSel']), (2165, 645)], kind='ctrl', label='WBSel_m[1]', lp=(2170, 620))
wire('c_MemWrite', [(2110, R['MemWrite']), (2300, R['MemWrite']), (2300, 740)], kind='ctrl', label='MemWrite_m', lp=(2180, R['MemWrite'] - 4))
wire('rd_m', [(2110, R['rd']), (2460, R['rd'])], kind='idx', label='rd_m[4:0]', lp=(2180, R['rd'] - 4))
wire('funct3_m', [(2110, R['funct3']), (2260, R['funct3']), (2260, 740)], label='funct3_m', lp=(2180, R['funct3'] - 4))
wire('pc4_m', [(2110, R['pc4']), (2460, R['pc4'])], label='pc4_m', lp=(2300, R['pc4'] - 4))
wire('pc4_m', [(2135, R['pc4']), (2135, 660), (2150, 660)])
wire('alu_m', [(2110, R['alu']), (2230, R['alu'])], label='alu_result_m', lp=(2115, R['alu'] + 13))
wire('alu_m', [(2125, R['alu']), (2125, 700), (2150, 700)])
wire('alu_m', [(2212, R['alu']), (2212, 925), (2440, 925), (2440, R['alu']), (2460, R['alu'])])
wire('st_m', [(2110, R['store']), (2230, R['store'])], label='store_data_m', lp=(2115, R['store'] + 13))
wire('rdata_m', [(2380, R['mem']), (2460, R['mem'])])
wire('rd_m', [(2400, R['rd']), (2400, Y_XR), (1385, Y_XR), (1385, 950)], kind='idx', label='EX_MEM.rd[4:0]', lp=(1900, Y_XR + 12))
wire('c_RegWrite', [(2415, R['RegWrite']), (2415, Y_XW), (1350, Y_XW), (1350, 950)], kind='ctrl', label='EX_MEM.RegWrite', lp=(1900, Y_XW + 12))
wire('MEM_WB.rd', [(1420, Y_WA), (1420, 950)], kind='idx')
wire('MEM_WB.RegWrite', [(1455, Y_WE), (1455, 950)], kind='ctrl')

# ================================================================= WB stage
comp('wbmux', 'mux', 2620, 570, 30, 290, 'M', ports=[('L', R['pc4'], '2'), ('L', R['alu'], '0'), ('L', R['mem'], '1'), ('R', 715, ''), ('T', 2635, '')])
wire('c_WBSel', [(2530, R['WBSel']), (2635, R['WBSel']), (2635, 574)], kind='ctrl', label='WBSel_w[1:0]', lp=(2545, R['WBSel'] - 4))
wire('pc4_w', [(2530, R['pc4']), (2620, R['pc4'])], label='pc4_w', lp=(2545, R['pc4'] - 4))
wire('alu_w', [(2530, R['alu']), (2620, R['alu'])], label='alu_result_w', lp=(2540, R['alu'] - 4))
wire('rdata_w', [(2530, R['mem']), (2620, R['mem'])], label='rdata_w', lp=(2545, R['mem'] - 4))


# ================================================================= design tables (below diagram)
EXTRA = []
MONO = 'Consolas, Menlo, DejaVu Sans Mono, monospace'
def panel(x, y, w, h, title):
    EXTRA.append('<rect x="%d" y="%d" width="%d" height="%d" rx="4" fill="#ffffff" stroke="#8ea9c8" stroke-width="1.2" filter="url(#sh)"/>' % (x, y, w, h))
    EXTRA.append('<rect x="%d" y="%d" width="%d" height="26" rx="4" fill="#dbe7f5" stroke="#8ea9c8" stroke-width="1.2"/>' % (x, y, w))
    EXTRA.append('<text x="%d" y="%d" font-size="14" font-weight="bold" fill="#1f3864">%s</text>' % (x + 10, y + 18, html.escape(title)))
def table(x, y, cols, rows, rh=19, fs=10.5, mono_from=0):
    tw = sum(cols)
    for r, row in enumerate(rows):
        yy = y + r * rh
        if r == 0:
            EXTRA.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#eef3fa"/>' % (x, yy, tw, rh))
        elif r % 2 == 0:
            EXTRA.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#f8fafc"/>' % (x, yy, tw, rh))
        cx = x
        for c, cell in enumerate(row):
            fam = MONO if (r > 0 and c >= mono_from) else 'inherit'
            EXTRA.append('<text x="%g" y="%g" font-size="%g" fill="#222" text-anchor="middle" font-weight="%s" font-family="%s">%s</text>' % (
                cx + cols[c] / 2, yy + rh - 5.5, fs, 'bold' if r == 0 else 'normal', fam, html.escape(str(cell))))
            cx += cols[c]
    for r in range(len(rows) + 1):
        EXTRA.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#b8c6d8" stroke-width="0.8"/>' % (x, y + r * rh, x + tw, y + r * rh))
    cx = x
    for c in cols + [0]:
        EXTRA.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#b8c6d8" stroke-width="0.8"/>' % (cx, y, cx, y + len(rows) * rh))
        cx += c
def lines(x, y, items, fs=11, lh=17, mono=True):
    for i, t in enumerate(items):
        col = '#1f3864' if t.startswith('■') else '#222'
        fam = MONO if (mono and not t.startswith('■')) else 'inherit'
        wt = 'bold' if t.startswith('■') else 'normal'
        EXTRA.append('<text x="%d" y="%d" font-size="%g" fill="%s" font-weight="%s" font-family="%s" xml:space="preserve">%s</text>' % (x, y + i * lh, fs, col, wt, fam, html.escape(t)))

Y0 = 1100
# ---- legend
panel(20, Y0, 470, 330, '图例 / 约定')
lg = [('data', '数据通路 (32 bit 为主)'), ('idx', '寄存器号 rs1/rs2/rd [4:0]'), ('ctrl', '控制信号 (主译码/流水线控制)'),
      ('haz', '冒险检测输出 (stall / flush / 重定向)'), ('fwd', '前递选择 ForwardA/B')]
for i, (k, t) in enumerate(lg):
    yy = Y0 + 48 + i * 24
    d = ' stroke-dasharray="%s"' % checker.DASH[k] if k in checker.DASH else ''
    EXTRA.append('<line x1="36" y1="%d" x2="110" y2="%d" stroke="%s" stroke-width="%s"%s marker-end="url(#ar_%s)"/>' % (yy, yy, checker.COL[k], checker.WID[k] + .4, d, k))
    EXTRA.append('<text x="122" y="%d" font-size="11.5" fill="#222">%s</text>' % (yy + 4, t))
yy = Y0 + 48 + 5 * 24
EXTRA.append('<line x1="36" y1="%d" x2="110" y2="%d" stroke="#1f3a68" stroke-width="1.6"/><circle cx="73" cy="%d" r="3.3" fill="#1f3a68"/><line x1="73" y1="%d" x2="73" y2="%d" stroke="#1f3a68" stroke-width="1.6"/>' % (yy, yy, yy, yy, yy + 14))
EXTRA.append('<text x="122" y="%d" font-size="11.5" fill="#222">实心圆点 = 同一信号分叉 (电气连接)</text>' % (yy + 4))
yy += 26
EXTRA.append('<path d="M36,%d L68,%d A5,5 0 0 1 78,%d L110,%d" fill="none" stroke="#1f3a68" stroke-width="1.6"/><line x1="73" y1="%d" x2="73" y2="%d" stroke="#c55a11" stroke-width="1.2"/>' % (yy, yy, yy, yy, yy - 12, yy + 12))
EXTRA.append('<text x="122" y="%d" font-size="11.5" fill="#222">跨线弧 (line jump) = 交叉但不相连</text>' % (yy + 4))
lines(36, yy + 32, ['信号命名: <名>_<级>  f=IF d=ID e=EX m=MEM w=WB',
                    '流水线寄存器内每一行 = 一个字段 (同一 y 坐标直通)',
                    '△ = posedge clk;  所有寄存器同步复位 rst',
                    '多路选择器端口旁的数字 = 选择信号取值',
                    '寄存器堆: 写优先旁路, 读地址 == 写地址时直接输出 wd'], fs=10.5, lh=17, mono=False)

# ---- main control truth table
panel(510, Y0, 800, 330, 'Main Control 真值表 (ID 级, 输入 opcode = instr[6:0])')
cols = [70, 72, 60, 52, 62, 64, 54, 44, 40, 64, 62, 56, 46]
rows = [['类型', 'opcode', 'RegWrite', 'WBSel', 'MemRead', 'MemWrite', 'Branch', 'Jump', 'Jalr', 'ALUSrcA', 'ALUSrcB', 'ALUOp', 'Imm'],
        ['R-type', '0110011', 1, '00', 0, 0, 0, 0, 0, '00', 0, '10', '-'],
        ['I-ALU', '0010011', 1, '00', 0, 0, 0, 0, 0, '00', 1, '11', 'I'],
        ['LOAD', '0000011', 1, '01', 1, 0, 0, 0, 0, '00', 1, '00', 'I'],
        ['STORE', '0100011', 0, '00', 0, 1, 0, 0, 0, '00', 1, '00', 'S'],
        ['BRANCH', '1100011', 0, '00', 0, 0, 1, 0, 0, '00', 0, '01', 'B'],
        ['JAL', '1101111', 1, '10', 0, 0, 0, 1, 0, '00', 0, '00', 'J'],
        ['JALR', '1100111', 1, '10', 0, 0, 0, 1, 1, '00', 1, '00', 'I'],
        ['LUI', '0110111', 1, '00', 0, 0, 0, 0, 0, '10', 1, '00', 'U'],
        ['AUIPC', '0010111', 1, '00', 0, 0, 0, 0, 0, '01', 1, '00', 'U'],
        ['其他/气泡', '-', 0, '00', 0, 0, 0, 0, 0, '00', 0, '00', '-']]
table(522, Y0 + 38, cols, rows, rh=21, mono_from=1)
lines(522, Y0 + 285, ['JAL 的跳转目标由 EX 级加法器 pc_e+imm_e 计算, ALU 空闲;  JALR 目标 = (rs1+imm)&~1 由 ALU 计算。',
                      'LUI: 0 + imm;  AUIPC: pc + imm;  BRANCH: ALU 做比较 (SUB/SLT/SLTU), 结果看 zero。'], fs=10.5, lh=17, mono=False)

# ---- ALU decoder table
panel(1330, Y0, 340, 400, 'ALU Decoder (EX 级)')
rows = [['ALUOp', 'funct3', 'f7[5]', '操作', 'ALUCtl'],
        ['00', 'xxx', 'x', 'ADD', '0000'], ['01', '00x', 'x', 'SUB', '0001'], ['01', '10x', 'x', 'SLT', '0011'], ['01', '11x', 'x', 'SLTU', '0100'],
        ['10', '000', '0', 'ADD', '0000'], ['10', '000', '1', 'SUB', '0001'], ['11', '000', 'x', 'ADD', '0000'],
        ['1x', '001', 'x', 'SLL', '0010'], ['1x', '010', 'x', 'SLT', '0011'], ['1x', '011', 'x', 'SLTU', '0100'], ['1x', '100', 'x', 'XOR', '0101'],
        ['1x', '101', '0', 'SRL', '0110'], ['1x', '101', '1', 'SRA', '0111'], ['1x', '110', 'x', 'OR', '1000'], ['1x', '111', 'x', 'AND', '1001']]
table(1342, Y0 + 38, [60, 60, 50, 80, 66], rows, rh=20, mono_from=0)
lines(1342, Y0 + 385, ['zero = (Y == 32\'d0);  f7[5] = instr[30]'], fs=10.5)

# ---- mux encoding
panel(1690, Y0, 520, 400, '多路选择器编码')
rows = [['MUX', '选择信号', '取值 → 输出'],
        ['PC mux (IF)', 'pc_src', '0: pc_f+4    1: pc_target'],
        ['ForwardA mux', 'ForwardA[1:0]', '00: rs1_data  01: wb_data  10: exmem_fwd'],
        ['ForwardB mux', 'ForwardB[1:0]', '00: rs2_data  01: wb_data  10: exmem_fwd'],
        ['ALU A mux', 'ALUSrcA[1:0]', '00: rs1_fwd   01: pc_e   10: 32\'d0'],
        ['ALU B mux', 'ALUSrcB', '0: rs2_fwd    1: imm_e'],
        ['Target mux', 'Jalr_e', '0: pc_e+imm_e   1: alu_result&~1'],
        ['EX/MEM 前递 mux', 'WBSel_m[1]', '0: alu_result_m   1: pc4_m'],
        ['WB mux', 'WBSel_w[1:0]', '00: alu_result  01: rdata  10: pc4']]
table(1702, Y0 + 38, [120, 110, 266], rows, rh=22, fs=10.5, mono_from=1)
lines(1702, Y0 + 256, ['■ 流水线寄存器行为 (Verilog)',
                       'always @(posedge clk)',
                       '  if (rst || flush) q <= 0;   // 气泡: 控制位全 0',
                       '  else if (en)      q <= d;',
                       'IF/ID : en = ~stall, flush = pc_src (instr 清为 NOP 0x00000013)',
                       'ID/EX : en = 1,      flush = stall | pc_src',
                       'EX/MEM, MEM/WB : en = 1, flush = 0;   PC: en = ~stall'], fs=10.5, lh=17)

# ---- equations
panel(2230, Y0, 550, 400, '冒险 / 前递 / 分支 逻辑方程')
lines(2242, Y0 + 46, [
 '■ Hazard Detection Unit (ID 级, 组合逻辑)',
 'stall = ID_EX.MemRead && ID_EX.rd != 0 &&',
 '        (ID_EX.rd == IF_ID.rs1 || ID_EX.rd == IF_ID.rs2);',
 'PCWrite = IF_ID_en = ~stall;',
 'IF_ID_flush = pc_src;   ID_EX_flush = stall | pc_src;',
 '■ Forwarding Unit (EX 级, EX/MEM 优先)',
 'if (EX_MEM.RegWrite && EX_MEM.rd!=0 && EX_MEM.rd==ID_EX.rs1)',
 '      ForwardA = 2\'b10;',
 'else if (MEM_WB.RegWrite && MEM_WB.rd!=0 && MEM_WB.rd==ID_EX.rs1)',
 '      ForwardA = 2\'b01;   else ForwardA = 2\'b00;',
 'ForwardB: 同上, 把 rs1 换成 rs2',
 '■ Branch Unit (EX 级)',
 'br_true = zero ^ funct3[0] ^ funct3[2];',
 'pc_src  = Jump | (Branch & br_true);',
 'pc_target = Jalr ? (alu_result & ~32\'d1) : (pc_e + imm_e);',
 'pc_next   = pc_src ? pc_target : pc_f + 4;'], fs=10.5, lh=19.5)

Y1 = 1520
# ---- pipeline register fields
panel(20, Y1, 900, 340, '流水线寄存器字段 (位宽)')
rows = [['寄存器', '控制字段', '数据字段', '合计'],
        ['IF/ID', '—', 'pc[31:0], pc4[31:0], instr[31:0]', '96'],
        ['ID/EX', 'RegWrite, WBSel[1:0], MemRead, MemWrite, Branch,', 'pc, pc4, rs1_data, rs2_data, imm (各32),', ''],
        ['', 'Jump, Jalr, ALUSrcA[1:0], ALUSrcB, ALUOp[1:0]  (13b)', 'rs1, rs2, rd (各5), funct3[2:0], funct7[5]', '192'],
        ['EX/MEM', 'RegWrite, WBSel[1:0], MemRead, MemWrite  (5b)', 'alu_result, store_data, pc4 (各32), rd[4:0], funct3', '109'],
        ['MEM/WB', 'RegWrite, WBSel[1:0]  (3b)', 'alu_result, rdata, pc4 (各32), rd[4:0]', '104']]
table(32, Y1 + 38, [80, 330, 400, 66], rows, rh=24, fs=10.5, mono_from=1)
lines(32, Y1 + 205, ['■ 模块划分建议 (每个方框 = 一个 Verilog module)',
                     'pc_reg, imem, adder(+4), if_id_reg, control, imm_gen, regfile, hazard_unit, id_ex_reg,',
                     'mux3 x3 (ForwardA/B, ALUSrcA), mux2 x5, alu_decoder, alu, branch_unit, adder(pc+imm),',
                     'forwarding_unit, ex_mem_reg, dmem, mem_wb_reg, top (连线与本图一一对应)',
                     '■ 端口宽度: 数据 32 bit; 寄存器号 5 bit; ALUCtl 4 bit; funct3 3 bit'], fs=10.5, lh=19)

# ---- Imm gen
panel(940, Y1, 640, 340, 'Imm Gen (ID 级, 内部按 opcode 选择格式)')
rows = [['格式', '适用 opcode', 'imm[31:0] (i = instr)'],
        ['I', 'I-ALU, LOAD, JALR', "{{21{i[31]}}, i[30:20]}"],
        ['S', 'STORE', "{{21{i[31]}}, i[30:25], i[11:7]}"],
        ['B', 'BRANCH', "{{20{i[31]}}, i[7], i[30:25], i[11:8], 1'b0}"],
        ['U', 'LUI, AUIPC', "{i[31:12], 12'b0}"],
        ['J', 'JAL', "{{12{i[31]}}, i[19:12], i[20], i[30:21], 1'b0}"]]
table(952, Y1 + 38, [60, 150, 406], rows, rh=24, fs=10.5, mono_from=1)
lines(952, Y1 + 205, ['■ Register File',
                      '2 读 1 写; 读为组合逻辑, 写在 posedge clk (we && wa != 0)',
                      'rd1 = (we && wa!=0 && wa==ra1) ? wd : rf[ra1];  rd2 同理',
                      '→ WB 与 ID 同周期访问同一寄存器时无需额外前递'], fs=10.5, lh=19)

# ---- DMEM
panel(1600, Y1, 590, 340, 'Data Memory (MEM 级)')
rows = [['funct3', 'LOAD', 'STORE', '说明'],
        ['000', 'LB', 'SB', '字节, 符号扩展'], ['001', 'LH', 'SH', '半字, 符号扩展'], ['010', 'LW', 'SW', '字'],
        ['100', 'LBU', '—', '字节, 零扩展'], ['101', 'LHU', '—', '半字, 零扩展']]
table(1612, Y1 + 38, [80, 80, 80, 326], rows, rh=24, fs=10.5, mono_from=0)
lines(1612, Y1 + 205, ['■ 接口',
                       'addr = alu_result_m, wdata = store_data_m (rs2 经前递)',
                       'we = MemWrite_m: 按 addr[1:0] 与 funct3 生成字节使能 be[3:0], 数据左移对齐',
                       're = MemRead_m : 读出字按 addr[1:0] 右移, 再按 funct3 扩展 → rdata_m',
                       '写: posedge clk 同步;  读: 组合 (或同步读 + 调整时序)'], fs=10.5, lh=19)

# ---- timing notes
panel(2210, Y1, 570, 340, '时序与冒险处理小结')
lines(2222, Y1 + 46, ['■ 数据冒险',
                      '· EX→EX : EX/MEM 前递 (exmem_fwd, 含 JAL/JALR 的 pc+4)',
                      '· MEM→EX: MEM/WB 前递 (wb_data, 含 load 数据)',
                      '· WB→ID : 寄存器堆写优先旁路',
                      '· load-use: 停顿 1 拍 (PC/IF_ID 保持, ID/EX 插气泡)',
                      '■ 控制冒险',
                      '· 静态预测不跳转; 分支/JAL/JALR 在 EX 解析',
                      '· pc_src=1: PC ← pc_target, 冲刷 IF/ID 与 ID/EX (2 拍代价)',
                      '■ 其它',
                      '· store 的 rs2 同样经过 ForwardB → store_data',
                      '· x0 写被屏蔽; rd==0 不参与前递/停顿比较',
                      '· 本图中 stall 与 pc_src 不会同时有效 (EX 为 load 时',
                      '  不可能是分支), 因此无需优先级处理'], fs=10.5, lh=19.5, mono=False)

# ================================================================= output
import checker
checker.run(comps, wires, texts, globals())
