#!/usr/bin/env python3
"""Minimal BIFF8 record-level editor for Sony TranslationCheck .xls files.
Only changes: VN sheet cells (AN/AU/AV) become LABELSST; new strings appended to SST; offsets recomputed
(BOUNDSHEET.lbPlyPos, INDEX, DBCELL, EXTSST). Everything else in the Workbook stream is kept byte-identical."""
import struct
CELL_TYPES={0x0201,0x00BE,0x00FD,0x0204,0x0203,0x027E,0x00BD,0x0006,0x0205,0x00D6,0x0207}
T_BOF,T_EOF,T_BOUNDSHEET,T_SST,T_CONT,T_EXTSST,T_ROW,T_DBCELL,T_INDEX,T_DEFCOLW=0x0809,0x000A,0x0085,0x00FC,0x003C,0x00FF,0x0208,0x00D7,0x020B,0x0055
T_MULBLANK,T_BLANK,T_LABELSST,T_STRING=0x00BE,0x0201,0x00FD,0x0207
def parse(stream):
    recs=[];pos=0
    while pos<len(stream):
        t,l=struct.unpack_from("<HH",stream,pos); recs.append([t,bytes(stream[pos+4:pos+4+l])]); pos+=4+l
    return recs
def serialize(recs):
    return b"".join(struct.pack("<HH",t,len(d))+d for t,d in recs)
def positions(recs):
    p=[];pos=0
    for t,d in recs: p.append(pos); pos+=4+len(d)
    return p,pos
def substreams(recs):
    """list of (start_idx, end_idx_inclusive) for each BOF..EOF"""
    out=[];st=None;depth=0
    for i,(t,d) in enumerate(recs):
        if t==T_BOF:
            if depth==0: st=i
            depth+=1
        elif t==T_EOF:
            depth-=1
            if depth==0: out.append((st,i))
    return out
# ---------------- SST ----------------
def sst_parse(recs, i_sst):
    """Return (strings, info) where info lists per-string (record_index, offset_in_record_data)."""
    segs=[(i_sst,recs[i_sst][1])]; j=i_sst+1
    while recs[j][0]==T_CONT: segs.append((j,recs[j][1])); j+=1
    tot,uniq=struct.unpack_from("<II",segs[0][1],0)
    si=0; off=8; strings=[]; locs=[]; plain=[]
    def need(n):
        nonlocal si,off
        if off+n>len(segs[si][1]) and off==len(segs[si][1]): si+=1; off=0
    for k in range(uniq):
        if off>=len(segs[si][1]): si+=1; off=0
        locs.append((segs[si][0],off))
        d=segs[si][1]
        cch,flags=struct.unpack_from("<HB",d,off); off+=3
        high=flags&1; rich=flags&8; ext=flags&4; crun=cbext=0
        if rich: crun,=struct.unpack_from("<H",d,off); off+=2
        if ext: cbext,=struct.unpack_from("<I",d,off); off+=4
        chars=[]; left=cch
        while left>0:
            d=segs[si][1]
            if off>=len(d):
                si+=1; off=0; d=segs[si][1]; high=d[0]&1; off=1
            avail=(len(d)-off)//(2 if high else 1); n=min(left,avail)
            b=d[off:off+n*(2 if high else 1)]
            chars.append(b.decode("utf-16-le") if high else b.decode("latin-1")); off+=len(b); left-=n
        skip=4*crun+cbext
        while skip>0:
            d=segs[si][1]
            if off>=len(d): si+=1; off=0; d=segs[si][1]
            n=min(skip,len(d)-off); off+=n; skip-=n
        strings.append("".join(chars)); plain.append(crun==0 and cbext==0)
    sst_parse.plain=plain
    return strings,locs,j-1,tot,uniq
def extsst_compute(recs, locs, i_extsst, dsst):
    p,_=positions(recs)
    n=(len(locs)+dsst-1)//dsst
    out=struct.pack("<H",dsst)
    for b in range(n):
        ri,off=locs[b*dsst]
        out+=struct.pack("<IHH",p[ri]+4+off,4+off,0)
    return out
# ---------------- DBCELL / INDEX ----------------
def sheet_recompute(recs, s, e):
    """Recompute DBCELL and INDEX records for substream recs[s..e]; returns new list of records (same length)."""
    p,_=positions(recs)
    idx=[i for i in range(s,e+1) if recs[i][0]==T_INDEX]
    dbs=[i for i in range(s,e+1) if recs[i][0]==T_DBCELL]
    # build blocks: between previous DBCELL (or start) and this DBCELL
    prev=s
    for di in dbs:
        rows=[i for i in range(prev,di) if recs[i][0]==T_ROW]
        if not rows: prev=di+1; continue
        rownums=[struct.unpack_from("<H",recs[i][1],0)[0] for i in rows]
        first_cell={}
        for i in range(rows[-1]+1,di):
            if recs[i][0] in CELL_TYPES and recs[i][0]!=T_STRING:
                r,=struct.unpack_from("<H",recs[i][1],0)
                if r not in first_cell: first_cell[r]=i
        dbRtrw=p[di]-p[rows[0]]
        rgdb=[]; last=None
        for k,rn in enumerate(rownums):
            fc=first_cell.get(rn)
            if k==0:
                ref=p[rows[1]] if len(rows)>1 else p[rows[0]]+4+len(recs[rows[0]][1])
                rgdb.append(p[fc]-ref if fc is not None else 0)
                last=fc if fc is not None else last
            else:
                if fc is None: rgdb.append(0)
                else:
                    rgdb.append(p[fc]-p[last] if last is not None else 0); last=fc
        recs[di]=[T_DBCELL,struct.pack("<I",dbRtrw)+b"".join(struct.pack("<H",x) for x in rgdb)]
        prev=di+1
    if idx:
        ii=idx[0]; d=recs[ii][1]
        res,rwMic,rwMac,ibXF=struct.unpack_from("<IIII",d,0)
        dcw=[i for i in range(s,e+1) if recs[i][0]==T_DEFCOLW]
        ibXF=p[dcw[0]] if dcw else ibXF
        recs[ii]=[T_INDEX,struct.pack("<IIII",res,rwMic,rwMac,ibXF)+b"".join(struct.pack("<I",p[i]) for i in dbs)]
    return recs
def fix_boundsheets(recs):
    p,_=positions(recs); subs=substreams(recs)
    bsi=[i for i,(t,d) in enumerate(recs) if t==T_BOUNDSHEET]
    for k,i in enumerate(bsi):
        d=recs[i][1]; recs[i]=[T_BOUNDSHEET,struct.pack("<I",p[subs[k+1][0]])+d[4:]]
    return recs

# ---------------- modification ----------------
MAXREC=8224
def enc_xlstring(s):
    cu=s.encode("utf-16-le"); cch=len(cu)//2
    try:
        b=s.encode("latin-1")
        if all(ord(ch)<256 for ch in s): return struct.pack("<HB",cch,0)+b
    except UnicodeEncodeError: pass
    return struct.pack("<HB",cch,1)+cu
def apply_cells(stream, targets):
    """targets: dict {(row0, col0): text} for the LAST sheet named 'VN'. Returns new stream bytes and stats."""
    recs=parse(stream)
    # find VN substream via BOUNDSHEET names
    subs=substreams(recs)
    bsi=[i for i,(t,d) in enumerate(recs) if t==T_BOUNDSHEET]
    names=[]
    for i in bsi:
        d=recs[i][1]; cch=d[6]; fl=d[7]
        names.append(d[8:8+cch*2].decode("utf-16-le") if fl&1 else d[8:8+cch].decode("latin-1"))
    k=names.index("VN"); vs,ve=subs[k+1]
    # SST
    i_sst=[i for i,(t,d) in enumerate(recs) if t==T_SST][0]
    strings,locs,last,tot,uniq=sst_parse(recs,i_sst)
    plain=sst_parse.plain
    index={}
    for i,st_ in enumerate(strings):
        if plain[i] and st_ not in index: index[st_]=i
    new=[]
    def sst_idx(s):
        if s in index: return index[s]
        index[s]=len(strings)+len(new); new.append(s); return index[s]
    # build cell replacements in VN sheet
    by_row={}
    for (r,c),txt in targets.items(): by_row.setdefault(r,{})[c]=sst_idx(txt)
    out=[]; done=set(); nrefs=0
    for i,(t,d) in enumerate(recs):
        if not (vs<=i<=ve) or t not in (T_MULBLANK,T_BLANK,T_LABELSST):
            out.append([t,d]); continue
        r,c0=struct.unpack_from("<HH",d,0)
        tg=by_row.get(r)
        if not tg: out.append([t,d]); continue
        if t==T_BLANK or t==T_LABELSST:
            if c0 in tg:
                if t==T_LABELSST: raise RuntimeError(f"target cell already has a value: row {r} col {c0}")
                xf,=struct.unpack_from("<H",d,4)
                out.append([T_LABELSST,struct.pack("<HHHI",r,c0,xf,tg[c0])]); done.add((r,c0)); nrefs+=1
                if t==T_LABELSST: nrefs-=1  # replaced an existing reference
            else: out.append([t,d])
            continue
        # MULBLANK
        c1,=struct.unpack_from("<H",d,len(d)-2)
        xfs=list(struct.unpack_from("<%dH"%(c1-c0+1),d,4))
        if not any(c0<=c<=c1 for c in tg): out.append([t,d]); continue
        seg=[]
        def flush():
            if not seg: return
            if len(seg)==1: out.append([T_BLANK,struct.pack("<HHH",r,seg[0][0],seg[0][1])])
            else: out.append([T_MULBLANK,struct.pack("<HH",r,seg[0][0])+b"".join(struct.pack("<H",x) for _,x in seg)+struct.pack("<H",seg[-1][0])])
            seg.clear()
        for j,c in enumerate(range(c0,c1+1)):
            if c in tg:
                flush(); out.append([T_LABELSST,struct.pack("<HHHI",r,c,xfs[j],tg[c])]); done.add((r,c)); nrefs+=1
            else: seg.append((c,xfs[j]))
        flush()
    missing=[k for k in targets if k not in done]
    if missing: raise RuntimeError(f"cells not found as BLANK/MULBLANK: {missing[:5]} ... ({len(missing)})")
    recs=out
    # append new strings to SST chain
    i_sst=[i for i,(t,d) in enumerate(recs) if t==T_SST][0]
    j=i_sst
    while recs[j+1][0]==T_CONT: j+=1
    ins=j+1; tail=recs[j]
    for s in new:
        b=enc_xlstring(s)
        if len(b)>MAXREC-1: raise RuntimeError("string too long for one record")
        if len(tail[1])+len(b)<=MAXREC: tail[1]=tail[1]+b
        else:
            tail=[T_CONT,b]; recs.insert(ins,tail); ins+=1
    d=recs[i_sst][1]; recs[i_sst][1]=struct.pack("<II",tot+nrefs,uniq+len(new))+d[8:]
    # recompute EXTSST after layout (positions depend on earlier records only, so compute iteratively)
    i_ext=[i for i,(t,d) in enumerate(recs) if t==T_EXTSST][0]
    strings2,locs2,_,_,uniq2=sst_parse(recs,i_sst)
    dsst=max(8,(uniq2+127)//128)
    recs[i_ext]=[T_EXTSST,extsst_compute(recs,locs2,i_ext,dsst)]
    # positions before EXTSST unaffected by its size; now fix sheets
    for s,e in substreams(recs)[1:]: recs=sheet_recompute(recs,s,e)
    recs=fix_boundsheets(recs)
    for s,e in substreams(recs)[1:]: recs=sheet_recompute(recs,s,e)   # again: BOUNDSHEET size constant, but be safe
    return serialize(recs), {"new_strings":len(new),"new_refs":nrefs,"cells":len(done),"sst_unique":uniq2,"dsst":dsst}

# ---------------- OLE in-place stream replacement ----------------
FREESECT,ENDOFCHAIN,FATSECT,DIFSECT=0xFFFFFFFF,0xFFFFFFFE,0xFFFFFFFD,0xFFFFFFFC
def ole_replace_stream(data, stream_name, newstream):
    data=bytearray(data)
    hdr=data[:512]
    ss=1<<struct.unpack_from("<H",hdr,0x1E)[0]; assert ss==512
    nfat,=struct.unpack_from("<I",hdr,0x2C); dirstart,=struct.unpack_from("<I",hdr,0x30)
    cutoff,=struct.unpack_from("<I",hdr,0x38); difstart,ndif=struct.unpack_from("<II",hdr,0x44)
    difat=list(struct.unpack_from("<109I",hdr,0x4C))
    assert ndif==0 or difstart==ENDOFCHAIN or True
    if ndif: raise RuntimeError("DIFAT chain not supported")
    fatsecs=[x for x in difat if x!=FREESECT][:nfat]
    off=lambda s: 512+s*512
    fat=[]
    for s in fatsecs: fat+=list(struct.unpack_from("<128I",data,off(s)))
    def chain(s):
        out=[]
        while s not in (ENDOFCHAIN,FREESECT): out.append(s); s=fat[s]
        return out
    # directory
    dsecs=chain(dirstart); entry=None; nmatch=0
    for ds in dsecs:
        for k in range(4):
            eo=off(ds)+k*128; nl,=struct.unpack_from("<H",data,eo+64)
            nm=bytes(data[eo:eo+max(0,nl-2)]).decode("utf-16-le")
            if nm==stream_name and data[eo+66]==2: entry=eo; nmatch+=1
    if entry is None: raise RuntimeError("stream not found")
    if nmatch!=1: raise RuntimeError(f"{nmatch} streams named {stream_name}; refusing to guess")
    start,=struct.unpack_from("<I",data,entry+116); size,=struct.unpack_from("<I",data,entry+120)
    assert size>=cutoff and len(newstream)>=cutoff
    old=chain(start); need=(len(newstream)+511)//512
    total_secs=(len(data)-512+511)//512
    if len(data)<512+total_secs*512: data+=b"\0"*(512+total_secs*512-len(data))
    secs=old[:need]
    for s in old[need:]: fat[s]=FREESECT
    while len(secs)<need:
        secs.append(total_secs); total_secs+=1
        while total_secs>len(fat):   # grow FAT by one sector, placed at end
            fs=total_secs; total_secs+=1
            fat+= [FREESECT]*128
            fatsecs.append(fs); fat[fs]=FATSECT
            if len(fatsecs)>109: raise RuntimeError("needs DIFAT")
    for a,b in zip(secs,secs[1:]): fat[a]=b
    fat[secs[-1]]=ENDOFCHAIN
    # FAT entries for appended sectors beyond len(fat) handled above; write sectors
    data+=b"\0"*(512+total_secs*512-len(data))
    padded=newstream+b"\0"*(need*512-len(newstream))
    for k,s in enumerate(secs): data[off(s):off(s)+512]=padded[k*512:(k+1)*512]
    for k,fs in enumerate(fatsecs): data[off(fs):off(fs)+512]=struct.pack("<128I",*fat[k*128:(k+1)*128])
    struct.pack_into("<I",data,0x2C,len(fatsecs))
    difat=fatsecs+[FREESECT]*(109-len(fatsecs)); struct.pack_into("<109I",data,0x4C,*difat)
    struct.pack_into("<II",data,entry+116,secs[0],len(newstream)); 
    return bytes(data)
