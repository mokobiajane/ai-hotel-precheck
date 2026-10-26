import json, csv, random, math, datetime as dt
from collections import Counter, defaultdict
import os
OUT=os.path.dirname(os.path.abspath(__file__))+os.sep
cases=[json.loads(l) for l in open(OUT+"raw_cases.jsonl",encoding="utf-8")]
F=["check_in","check_out","room","guests","meal"]
rep={}
rep["n_cases"]=len(cases); rep["n_groups"]=len({c["group_id"] for c in cases}); rep["n_labels"]=len(cases)*5
# status distribution per field
sd={f:Counter(c["gold"][f]["status"] for c in cases) for f in F}
rep["status_by_field"]={f:dict(v) for f,v in sd.items()}
tot=Counter(); [tot.update(v) for v in sd.values()]; rep["status_total"]=dict(tot)
# missing (no value in reply) by field and by style
nul=defaultdict(lambda:[0,0])
for c in cases:
    for f in F:
        nul[(c["style"],f)][1]+=1
        if c["gold"][f]["extracted"] is None: nul[(c["style"],f)][0]+=1
rep["null_by_style"]={f"{s}|{f}":v for (s,f),v in nul.items()}
byst={}
for s in ["formal","short"]:
    a=sum(v[0] for (ss,f),v in nul.items() if ss==s); b=sum(v[1] for (ss,f),v in nul.items() if ss==s); byst[s]=(a,b,round(a/b,3))
rep["null_by_style_total"]=byst
a=sum(v[0] for v in nul.values()); b=sum(v[1] for v in nul.values()); rep["null_overall"]=(a,b,round(a/b,3))
# label consistency
bad=[]
for c in cases:
    for f in F:
        g=c["gold"][f]
        if g["status"]=="missing" and (g["extracted"] or g["evidence"]): bad.append((c["case_id"],f,"missing with value"))
        if g["status"]in("match","mismatch") and g["extracted"] is None: bad.append((c["case_id"],f,"no value"))
        if g["evidence"] and g["evidence"] not in c["hotel_reply"]: bad.append((c["case_id"],f,"evidence not in text"))
        if g["status"]=="match":
            bv=c["booking"][f if f!="room" else "room"]
            if str(g["extracted"])!=str(bv): bad.append((c["case_id"],f,"match but values differ"))
        if g["status"]=="mismatch":
            bv=c["booking"][f]
            if str(g["extracted"])==str(bv): bad.append((c["case_id"],f,"mismatch but values equal"))
rep["label_errors"]=bad
# logic: dates
lg=[]
for c in cases:
    ci=c["gold"]["check_in"]["extracted"] or c["booking"]["check_in"]
    co=c["gold"]["check_out"]["extracted"] or c["booking"]["check_out"]
    if co<=ci: lg.append(c["case_id"])
    if c["booking"]["guests"]<=0: lg.append(c["case_id"])
rep["logic_violations"]=lg
# outliers: stay length, guests
st=[(dt.date.fromisoformat(c["booking"]["check_out"])-dt.date.fromisoformat(c["booking"]["check_in"])).days for c in cases]
rep["stay_days"]=dict(min=min(st),max=max(st),mean=round(sum(st)/len(st),2))
rep["guests"]=dict(Counter(c["booking"]["guests"] for c in cases))
rep["text_len"]=dict(min=min(len(c["hotel_reply"]) for c in cases),max=max(len(c["hotel_reply"]) for c in cases))
# duplicates
txt=Counter(c["hotel_reply"] for c in cases); rep["exact_dup_texts"]=sum(v-1 for v in txt.values() if v>1)
def toks(s): return set(s.lower().replace(","," ").replace(";"," ").replace("."," ").split())
near=0; pairs=[]
cl=cases
for i in range(len(cl)):
    for j in range(i+1,len(cl)):
        A,B=toks(cl[i]["hotel_reply"]),toks(cl[j]["hotel_reply"])
        s=len(A&B)/len(A|B)
        if s>=0.8: near+=1; pairs.append((cl[i]["case_id"],cl[j]["case_id"],round(s,2),cl[i]["group_id"]==cl[j]["group_id"]))
rep["near_dup_pairs_jaccard>=0.8"]=near; rep["near_dup_detail"]=pairs[:10]
# same-booking pairs
rep["groups_with_2_replies"]=sum(1 for g,v in Counter(c["group_id"] for c in cases).items() if v==2)
# split by group
random.seed(7)
gids=sorted({c["group_id"] for c in cases}); random.shuffle(gids)
n=len(gids); tr=set(gids[:int(.6*n)]); va=set(gids[int(.6*n):int(.8*n)]); te=set(gids[int(.8*n):])
sp={c["case_id"]:("train" if c["group_id"] in tr else "val" if c["group_id"] in va else "test") for c in cases}
rep["split_cases"]=dict(Counter(sp.values()))
assert not (tr&va or tr&te or va&te)
# statuses per split
ss=defaultdict(Counter)
for c in cases:
    for f in F: ss[sp[c["case_id"]]][c["gold"][f]["status"]]+=1
rep["status_by_split"]={k:dict(v) for k,v in ss.items()}
# ambiguity by field in test
amb=defaultdict(int)
for c in cases:
    if sp[c["case_id"]]=="test":
        for f in F:
            if c["gold"][f]["status"]=="ambiguous": amb[f]+=1
rep["test_ambiguous_by_field"]=dict(amb)
# cases with all 5 matching (no draft needed)
rep["all_match_cases"]=sum(1 for c in cases if all(c["gold"][f]["status"]=="match" for f in F))
rep["cases_without_any_problem_field"]=rep["all_match_cases"]
rep["cases_with_typo_candidates"]="n/a"
# write prepared csv
with open(OUT+"prepared_labels.csv","w",newline="",encoding="utf-8") as fh:
    w=csv.writer(fh); w.writerow(["case_id","group_id","split","field","booking_value","extracted_value","status","evidence"])
    for c in cases:
        for f in F:
            g=c["gold"][f]; w.writerow([c["case_id"],c["group_id"],sp[c["case_id"]],f,c["booking"][f],g["extracted"],g["status"],g["evidence"]])
json.dump(rep,open(OUT+"quality_report.json","w"),ensure_ascii=False,indent=1,default=str)
print(json.dumps(rep,ensure_ascii=False,indent=1,default=str))
