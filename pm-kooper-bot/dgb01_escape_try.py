"""Input-sequence tester for the dgb_01 2F-east escape. usage: dgb01_escape_try.py "tok tok ..."  tokens: DIR:k (u/d/l/r/n) or BTN[+BTN]:DIR:k with BTN in A B Z CD CL CR CU S R. Prints every frame and the peak y. Ultra Boots + Goombario/Kooper/Bombette are poked into RAM (no-Parakarry route)."""
import sys
from emu import *
from pm import *
BTN={'A':A,'B':B,'Z':Z,'CD':D_CBUTTON,'CL':L_CBUTTON,'CR':R_CBUTTON,'CU':U_CBUTTON,'S':START,'R':R_TRIG}
DIRS={'u':(0,80),'d':(0,-80),'l':(-80,0),'r':(80,0),'n':(0,0)}
def setup(e):
    e.load('states/dgb01_e4_ctrl.st')   # from dgb01_escape_states.py
    e.w8(PLAYER_DATA,2)
    for p in (1,2,3,8): e.w8(PLAYER_DATA+0x14+8*p,1)
def run(e,seq,verbose=False):
    maxy=-1e9; f=0; log=[]
    for tok in seq.split():
        parts=tok.split(':')
        if parts[0] in DIRS: btn=0; d=parts[0]; k=int(parts[1])
        else:
            btn=0
            for b in parts[0].split('+'): btn|=BTN[b]
            d=parts[1]; k=int(parts[2])
        for i in range(k):
            e.step(btn,*DIRS[d],1); f+=1
            p=player(e); maxy=max(maxy,p['y'])
            if verbose: print(f,tok,round(p['x'],1),round(p['y'],1),round(p['z'],1),p['action'],hex(p['flags']))
    return maxy
if __name__=='__main__':
    e=Emu('pm-jp.z64','/dev/shm/pmbot/esc'); setup(e)
    m=run(e,sys.argv[1],verbose=True)
    print('maxy',m,'end',player(e),where(e))
