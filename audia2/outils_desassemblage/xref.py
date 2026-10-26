import re,struct,capstone,sys
d=open(sys.argv[1],'rb').read()
md=capstone.Cs(capstone.CS_ARCH_M68K, capstone.CS_MODE_BIG_ENDIAN|capstone.CS_MODE_M68K_040)
def find(off,lim=0x58000):
    hits=set()
    for m in re.finditer(re.escape(struct.pack('>H',off)),d[:lim]):
        p=m.start()
        for back in (2,4,6):
            a=p-back
            if a<0 or a%2: continue
            for i in md.disasm(d[a:a+10],a):
                if f'${off:x}(a5' in i.op_str and a+i.size>p: hits.add((a,i.mnemonic,i.op_str))
                break
    return sorted(hits)
for o in sys.argv[2:]:
    h=find(int(o,16)); print('==',o,len(h))
    for x in h: print(' ',hex(x[0]),x[1],x[2])
