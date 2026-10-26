import pickle,sys,re
D=pickle.load(open(sys.argv[1],'rb')); A=sorted(D)
# 1) breakpoint positions: pea axis_end ... (inline search) ... move.w d0, VAR
pos={}
for i,a in enumerate(A):
    s,m,o=D[a]
    if m=='pea.l' and re.fullmatch(r'\$5[0-9a-f]{4}\.l',o):
        # look back 3 for count and input, forward 25 for the store
        cnt=inp=None
        for j in range(i-1,max(i-4,0),-1):
            mm,oo=D[A[j]][1],D[A[j]][2]
            if mm=='move.w' and oo.endswith('-(a7)'):
                src=oo.rsplit(',',1)[0]
                if src.startswith('#'): cnt=src
                else: inp=src
        if cnt is None: continue
        for j in range(i+1,min(i+25,len(A))):
            mm,oo=D[A[j]][1],D[A[j]][2]
            if mm=='move.w' and oo.startswith('d0, $') and oo.endswith('(a5)'):
                pos.setdefault(oo[4:],(o[1:6],cnt,inp)); break
            if mm in('jsr','rts'): break
# 2) 2D lookups
for i,a in enumerate(A):
    s,m,o=D[a]
    if m=='jsr' and o in('$49a6c.l','$49aba.l'):
        st=[]
        for j in range(i-1,max(i-8,0),-1):
            mm,oo=D[A[j]][1],D[A[j]][2]
            if mm=='pea.l' or (oo.endswith('-(a7)') and mm.startswith('move')): st.append(oo.rsplit(',',1)[0] if mm!='pea.l' else oo)
            if len(st)==4: break
        if len(st)==4:
            tbl,x,y,stride=st[0],st[1],st[2],st[3]
            print(f'{a:06x} {o[1:6]} tbl={tbl} x={x}->{pos.get(x)} y={y}->{pos.get(y)} stride={stride}')
