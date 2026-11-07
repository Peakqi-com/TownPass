"""長輩模式配色驗算：白字或深字的對比度，以及 8 種視覺條件下每兩色的最小色差（CIEDE2000）。

8 種條件＝正常、紅色盲、綠色盲、藍黃色盲（Machado 2009，嚴重度 1.0），各自再加上「水晶體老化」。
水晶體老化是粗略近似（減弱短波長），不是臨床模型；結果用來比較配色的相對好壞。
執行：python3 docs/townpass/elder-palette/check_palette.py
"""
import math, itertools, sys
def hx(h): h=h.lstrip('#'); return [int(h[i:i+2],16)/255 for i in (0,2,4)]
def lin(c): return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
def unlin(c): c=max(0,min(1,c)); return 12.92*c if c<=0.0031308 else 1.055*c**(1/2.4)-0.055
def L(rgb): r,g,b=[lin(c) for c in rgb]; return 0.2126*r+0.7152*g+0.0722*b
def cr(a,b): la,lb=sorted([L(a),L(b)],reverse=True); return (la+0.05)/(lb+0.05)
M={'正常':None,
 '紅色盲 protan':[[0.152286,1.052583,-0.204868],[0.114503,0.786281,0.099216],[-0.003882,-0.048116,1.051998]],
 '綠色盲 deutan':[[0.367322,0.860646,-0.227968],[0.280085,0.672501,0.047413],[-0.011820,0.042940,0.968881]],
 '藍黃色盲 tritan':[[1.255528,-0.076749,-0.178779],[-0.078411,0.930809,0.147602],[0.004733,0.691367,0.303900]]}
def sim(rgb,m,age=False):
    l=[lin(c) for c in rgb]
    if age: l=[l[0]*0.95,l[1]*0.85,l[2]*0.55]   # 粗略模擬水晶體黃化：吸收短波長（近似值，非臨床模型）
    if m: l=[sum(m[i][j]*l[j] for j in range(3)) for i in range(3)]
    return [unlin(c) for c in l]
def lab(rgb):
    r,g,b=[lin(c) for c in rgb]
    X=(0.4124*r+0.3576*g+0.1805*b)/0.95047; Y=0.2126*r+0.7152*g+0.0722*b; Z=(0.0193*r+0.1192*g+0.9505*b)/1.08883
    f=lambda t: t**(1/3) if t>0.008856 else 7.787*t+16/116
    return 116*f(Y)-16, 500*(f(X)-f(Y)), 200*(f(Y)-f(Z))
def de2000(c1,c2):
    L1,a1,b1=c1; L2,a2,b2=c2
    C1=math.hypot(a1,b1); C2=math.hypot(a2,b2); Cb=(C1+C2)/2
    G=0.5*(1-math.sqrt(Cb**7/(Cb**7+25**7))); a1p=(1+G)*a1; a2p=(1+G)*a2
    C1p=math.hypot(a1p,b1); C2p=math.hypot(a2p,b2)
    h1=math.degrees(math.atan2(b1,a1p))%360; h2=math.degrees(math.atan2(b2,a2p))%360
    dL=L2-L1; dC=C2p-C1p
    dh=0 if C1p*C2p==0 else (h2-h1 if abs(h2-h1)<=180 else (h2-h1-360 if h2>h1 else h2-h1+360))
    dH=2*math.sqrt(C1p*C2p)*math.sin(math.radians(dh/2))
    Lb=(L1+L2)/2; Cbp=(C1p+C2p)/2
    hb=(h1+h2)/2 if abs(h1-h2)<=180 else ((h1+h2+360)/2 if h1+h2<360 else (h1+h2-360)/2)
    if C1p*C2p==0: hb=h1+h2
    T=1-0.17*math.cos(math.radians(hb-30))+0.24*math.cos(math.radians(2*hb))+0.32*math.cos(math.radians(3*hb+6))-0.20*math.cos(math.radians(4*hb-63))
    SL=1+0.015*(Lb-50)**2/math.sqrt(20+(Lb-50)**2); SC=1+0.045*Cbp; SH=1+0.015*Cbp*T
    RT=-2*math.sqrt(Cbp**7/(Cbp**7+25**7))*math.sin(math.radians(60*math.exp(-((hb-275)/25)**2)))
    return math.sqrt((dL/SL)**2+(dC/SC)**2+(dH/SH)**2+RT*(dC/SC)*(dH/SH))
def report(name,pal):
    print(f'\n### {name}')
    for k,(bg,fg) in pal.items(): print(f'  {k:6s} 底 {bg} 字 {fg}  對比 {cr(hx(bg),hx(fg)):.2f}:1')
    for mn,m in M.items():
        for age in (False,True):
            cols={k:lab(sim(hx(v[0]),m,age)) for k,v in pal.items()}
            pairs=sorted(((de2000(cols[a],cols[b]),a,b) for a,b in itertools.combinations(cols,2)))
            d,a,b=pairs[0]; tag=mn+(' + 水晶體老化' if age else '')
            print(f'  {tag:22s} 最小色差 ΔE00={d:5.1f}（{a} vs {b}）')

pals={
 '提案簡報原配色（目測取色）':{'1999':('#1E6F6A','#FFFFFF'),'叫車':('#C8641C','#FFFFFF'),'1966':('#B53A4B','#FFFFFF'),'繳費':('#2B4A7A','#FFFFFF'),'敬老卡':('#3E6B3A','#FFFFFF'),'家人':('#5B4A8A','#FFFFFF')},
 '長輩模式配色（採用）':{'叫車':('#FEC84B','#1D2939'),'權益補助':('#17B26A','#1D2939'),'看醫生':('#0E7090','#FFFFFF'),'共餐上課':('#22CCEE','#1D2939'),'聽不清楚':('#6927DA','#FFFFFF'),'家人':('#7A2E0E','#FFFFFF'),'求助':('#D92D20','#FFFFFF')},
}
for n,p in pals.items(): report(n,p)
