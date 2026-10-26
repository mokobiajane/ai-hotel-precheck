import random, json, csv, re, itertools, datetime as dt
from collections import Counter, defaultdict
random.seed(2026)
OUT="/mnt/user-data/outputs/hw3_sample/"
ROOMS={"Standard Double":["standard double room","double room (standard)","a standard double"],
"Standard Twin":["standard twin room","twin room (standard)","a standard twin"],
"Deluxe Double":["deluxe double room","a deluxe double"],
"Family Room":["family room","a family room"],
"Single":["single room","a single room"],
"Suite":["junior suite","a suite"]}
MEALS={"RO":["room only","without meals"],"BB":["bed and breakfast","breakfast included"],
"HB":["half board","breakfast and dinner included"],"FB":["full board","all three meals included"],
"AI":["all inclusive","all-inclusive package"]}
NUM={1:"one",2:"two",3:"three",4:"four",5:"five"}
MON=["January","February","March","April","May","June","July","August","September","October","November","December"]
def typo(s):
    if random.random()<0.10 and len(s)>8:
        idx=[i for i in range(1,len(s)-2) if s[i].isalpha() and s[i+1].isalpha() and s[i]!=s[i+1]]
        if idx:
            i=random.choice(idx); return s[:i]+s[i+1]+s[i]+s[i+2:]
    return s
def datefmt(d,kind):
    if kind=="iso": return d.isoformat()
    if kind=="long": return f"{d.day} {MON[d.month-1]} {d.year}"
    if kind=="slash": return f"{d.day:02d}/{d.month:02d}/{d.year}"
def make_booking(ci_amb=False):
    while True:
        ci=dt.date(2027,1,1)+dt.timedelta(days=random.randint(0,300))
        if not ci_amb or (ci.day<=12 and ci.day!=ci.month): break
    n=random.randint(1,12)
    return dict(check_in=ci,check_out=ci+dt.timedelta(days=n),room=random.choice(list(ROOMS)),
                guests=random.choice([1,2,2,2,3,4]),meal=random.choice(list(MEALS)))
def pick_status(field,force=None):
    if force=="all_match": return "match"
    if force=="ci_amb" and field=="check_in": return "ambiguous"
    r=random.random()
    return "match" if r<.52 else "mismatch" if r<.74 else "missing" if r<.90 else "ambiguous"
def reply(b,style,force=None):
    parts={}; truth={}
    for f in ["check_in","check_out","room","guests","meal"]:
        st=pick_status(f,force)
        if f in("check_in","check_out") and st=="ambiguous": pass
        val=b[{"check_in":"check_in","check_out":"check_out","room":"room","guests":"guests","meal":"meal"}[f]]
        ext=None; phrase=None
        if f in("check_in","check_out"):
            d=val; 
            if st=="mismatch": d=d+dt.timedelta(days=random.choice([-2,-1,1,2,3]))
            if st=="ambiguous":
                d2=dt.date(d.year,d.month,d.day)
                # day<=12 and slash format -> day/month not recoverable
                if d.day<=12 and d.day!=d.month:
                    phrase=f"{'arrival' if f=='check_in' else 'departure'} on {d.day:02d}/{d.month:02d}"; ext=None
                else: st="match"
            if phrase is None and st!="missing":
                kind=random.choice(["iso","long","slash"])
                if kind=="slash" and d.day<=12 and d.day!=d.month:
                    kind="long"
                ds=datefmt(d,kind)
                phrase=f"{'check-in' if f=='check_in' else 'check-out'} on {ds}"; ext=d.isoformat()
        elif f=="room":
            if st=="mismatch": nv=random.choice([r for r in ROOMS if r!=val and not (set(r.split())&{'Double','Twin'} and set(val.split())&{'Double','Twin'} and r.split()[0]==val.split()[0])] or [r for r in ROOMS if r!=val]); ext=nv
            else: nv=val; ext=val
            if st=="ambiguous": phrase="a double or twin room, to be assigned on arrival"; ext=None
            elif st!="missing": phrase=random.choice(ROOMS[nv])
        elif f=="guests":
            nv=val
            if st=="mismatch": nv=max(1,val+random.choice([-1,1]))
            if st=="mismatch" and nv==val: nv=val+1
            ext=nv
            if st=="ambiguous": phrase="two adults and possibly a child"; ext=None
            elif st!="missing": phrase=f"{NUM[nv]} guest{'s' if nv>1 else ''}"
        else:
            nv=val
            if st=="mismatch": nv=random.choice([m for m in MEALS if m!=val]); 
            ext=nv
            if st=="ambiguous": phrase="breakfast can be added at an extra charge"; ext=None
            elif st!="missing": phrase=random.choice(MEALS[nv])
        if st=="missing": ext=None; phrase=None
        if phrase: phrase=typo(phrase)
        parts[f]=phrase; truth[f]=dict(status=st,extracted=ext,evidence=phrase)
    order=[f for f in parts if parts[f]]; random.shuffle(order)
    if not order: 
        order=[]; body="Your booking is confirmed."
    elif style=="formal":
        body="Dear Sir or Madam, thank you for your message. We confirm "+", ".join(parts[f] for f in order)+". Kind regards, Reservations."
    else:
        body="Hi! Booked: "+"; ".join(parts[f] for f in order)+". Thanks."
    return body,truth
cases=[]; cid=0
for g in range(1,49):
    force="all_match" if 13<=g<=18 else "ci_amb" if 19<=g<=21 else None
    b=make_booking(ci_amb=(force=="ci_amb"))
    for k in range(2 if g<=12 else 1):
        cid+=1
        style=random.choice(["formal","short"])
        text,truth=reply(b,style,force)
        cases.append(dict(case_id=f"C{cid:03d}",group_id=f"G{g:02d}",style=style,
            booking={**b,"check_in":b["check_in"].isoformat(),"check_out":b["check_out"].isoformat()},
            hotel_reply=text,gold=truth,source="synthetic_script_v2",generated="2026-10-25"))
with open(OUT+"raw_cases.jsonl","w",encoding="utf-8") as f:
    for c in cases: f.write(json.dumps(c,ensure_ascii=False)+"\n")
print(len(cases),"cases")
