
from vga32.game import GameApp
import math

LEVELS = [
 [
 "################################",
 "#..........#....K..............#",
 "#.########.#.###############...#",
 "#.#......#.#.#.............#...#",
 "#.#.####.#.#.#.###########.#...#",
 "#.#.#..#.#.#.#.#.........#.#...#",
 "#.#.#.##.#.#.#.#.#######.#.#...#",
 "#.#.#....#.#.#.#.#.....#.#.#...#",
 "#.#.######.#.#.#.#####.#.#.#...#",
 "#.#........#.#.#.....#.#.#.#...#",
 "#.##########.#.#######.#.#.#...#",
 "#............#.........#.#.#...#",
 "############.#.#########.#.#...#",
 "#............#...........#.#...#",
 "#.############.###########.#...#",
 "#.#......................#.#...#",
 "#.#.####################.#.#...#",
 "#.#.#..................#.#.#...#",
 "#.#.#.################.#.#.#...#",
 "#.#.#.#..............#.#.#.#...#",
 "#.#.#.#.############.#.#.#.#...#",
 "#.#.#.#.#..........#.#.#.#.#...#",
 "#.#.#.#.#.########.#.#.#.#.#...#",
 "#.#.#.#.#.#......#.#.#.#.#.#...#",
 "#.#.#.#.#.#.####.#.#.#.#.#.#...#",
 "#.#.#.#.#.#.#..#.#.#.#.#.#.#...#",
 "#.#.#.#.#.#.####.#.#.#.#.#.#...#",
 "#.#.#.#.#.#......#.#.#.#.#.#...#",
 "#.#.#.#.#.########.#.#.#.#.#...#",
 "#.#.#.#.#..........#.#.#.#.#...#",
 "#.#.#.#.############.#.#.#.#...#",
 "#.#.#.#..............#.#.#.#...#",
 "#.#.#.################.#.#.#...#",
 "#.#.#..................#.#.#...#",
 "#.#.####################.#.#...#",
 "#.#......................#.#...#",
 "#.########################.#...#",
 "#........................#.#...#",
 "#.########################.#...#",
 "#............#...........#.....#",
 "############.#.###########.#####",
 "#............#.................#",
 "#.###########################.#",
 "#...........................#.#",
 "#.#########################.#.#",
 "#...........................#.#",
 "########.###################.#.#",
 "#........#..A..H............#.#",
 "#.########..D...#############.#",
 "#..........X..................#",
 "################################"
 ],
]

class QuakeLevelAdv(GameApp):
    app_id = "games.quakeadv"
    title = "Quake Level Adv"
    icon = "star"
    category = "Games"
    width, height = 320, 200
    fps = 12

    def start(self):
        self.level_index = 0
        self.load_level(0)

    def load_level(self, i):
        self.level_index = i
        self.grid = [list(r) for r in LEVELS[i]]
        self.mh = len(self.grid)
        self.mw = max(len(r) for r in self.grid)
        self.grid = [r + ["#"]*(self.mw-len(r)) for r in self.grid]
        self.doors = {}
        self.px, self.py = 1.5, 1.5
        self.ang = 0.0
        self.health = 100
        self.ammo = 50
        self.score = 0
        self.keys = 0
        self.won = False
        self.over = False
        self.time = 0.0
        # find spawn
        for y,row in enumerate(self.grid):
            for x,ch in enumerate(row):
                if ch == "S":
                    self.px,self.py = x+0.5,y+0.5
                    self.grid[y][x]="."
        # fallback spawn near top-left empty
        if self.cell(1,1) != ".":
            for y,row in enumerate(self.grid):
                for x,ch in enumerate(row):
                    if ch in ".G":
                        self.px,self.py=x+0.5,y+0.5
                        break

    def cell(self,x,y):
        if x<0 or y<0 or x>=self.mw or y>=self.mh:
            return "#"
        ch=self.grid[int(y)][int(x)]
        if ch=="D" and self.doors.get((int(x),int(y)), False):
            return "."
        return ch

    def is_wall(self,ch):
        return ch not in ("."," ","G","A","H","K","X")

    def update(self,dt):
        if self.pressed("r"):
            self.load_level(self.level_index)
            return
        if self.over or self.won:
            return
        self.time += dt
        rot=1.8*dt
        if self.held("left") or self.held("a"): self.ang -= rot
        if self.held("right") or self.held("d"): self.ang += rot
        sp=2.4*dt
        nx,ny=self.px,self.py
        if self.held("up") or self.held("w"):
            nx += math.cos(self.ang)*sp
            ny += math.sin(self.ang)*sp
        if self.held("down") or self.held("s"):
            nx -= math.cos(self.ang)*sp
            ny -= math.sin(self.ang)*sp
        if not self.is_wall(self.cell(nx,self.py)): self.px=nx
        if not self.is_wall(self.cell(self.px,ny)): self.py=ny
        ch=self.cell(self.px,self.py)
        ix,iy=int(self.px),int(self.py)
        if ch=="G":
            self.won=True; self.score+=1000
        if ch=="K":
            self.keys+=1; self.score+=50
            self.grid[iy][ix]="."
            self.health=min(100,self.health+10)
        if ch=="A":
            self.ammo=min(99,self.ammo+10)
            self.grid[iy][ix]="."
        if ch=="H":
            self.health=min(100,self.health+25)
            self.grid[iy][ix]="."
        if self.held("e"):
            # open nearby door
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    x,y=ix+dx,iy+dy
                    if 0<=x<self.mw and 0<=y<self.mh and self.grid[y][x]=="D":
                        self.doors[(x,y)]=True
        # occasionally lose health if standing? no

    def wall_color(self,ch,side,perp,tex_x):
        if ch=="B": base=(70,100,220)
        elif ch=="R": base=(200,80,80)
        elif ch=="G": base=(80,200,80)
        elif ch=="Y": base=(200,200,80)
        elif ch=="D": base=(200,140,60)
        else: base=(170,170,170)
        shade=max(0,min(255,int(255*(1-perp/12.0))))
        col=[int(c*shade/255) for c in base]
        if side==1:
            col=[int(c*0.7) for c in col]
        # texture band
        band=(int(tex_x*8)+int(perp*2))%4
        if band==0:
            col=[min(255,c+25) for c in col]
        elif band==3:
            col=[max(0,c-25) for c in col]
        return tuple(col)

    def render(self,g):
        W,H=self.width,self.height
        g.clear((10,10,25))
        g.rect(0,0,W,H//2,(25,25,45))
        g.rect(0,H//2,W,H//2,(35,35,35))
        for x in range(0,W,2):
            cam=2.0*x/W-1.0
            rdx=math.cos(self.ang)-math.sin(self.ang)*cam*0.66
            rdy=math.sin(self.ang)+math.cos(self.ang)*cam*0.66
            mx,my=int(self.px),int(self.py)
            dx=1 if rdx>0 else -1 if rdx<0 else 0
            dy=1 if rdy>0 else -1 if rdy<0 else 0
            side_dist_x=((mx+(1 if dx>0 else 0))-self.px)/rdx if rdx!=0 else 1e9
            side_dist_y=((my+(1 if dy>0 else 0))-self.py)/rdy if rdy!=0 else 1e9
            delta_x=abs(1.0/rdx) if rdx!=0 else 1e9
            delta_y=abs(1.0/rdy) if rdy!=0 else 1e9
            hit=False; side=0; char="#"
            mx0,my0=mx,my
            for _ in range(32):
                if side_dist_x<side_dist_y:
                    side_dist_x+=delta_x; mx+=dx; side=0
                else:
                    side_dist_y+=delta_y; my+=dy; side=1
                ch=self.cell(mx,my)
                if self.is_wall(ch):
                    hit=True; char=ch; break
            if not hit:
                continue
            perp=(side_dist_x-delta_x) if side==0 else (side_dist_y-delta_y)
            if perp<0.001: perp=0.001
            line_h=int(H/perp)
            y0=(H-line_h)//2
            y0=max(0,min(H-line_h,y0))
            # wall texture coordinate
            if side==0:
                wall_x=self.py+perp*rdy
            else:
                wall_x=self.px+perp*rdx
            frac=wall_x-math.floor(wall_x)
            col=self.wall_color(char,side,perp,frac)
            g.rect(x,y0,2,line_h,col)
            # texture pips
            if line_h>16 and int(wall_x*4)%2==0:
                g.rect(x,y0+line_h//2,2,2,(0,0,0))
        # minimap
        mw,mh=2,2
        ox,oy=4,4
        g.rect(ox,oy,self.mw*mw+2,self.mh*mh+2,"black",outline="white")
        for y in range(self.mh):
            row=self.grid[y]
            for x in range(self.mw):
                ch=row[x]
                if ch=="#": g.rect(ox+1+x*mw,oy+1+y*mh,mw-1,mh-1,"gray")
                elif ch in ("B","R","G","Y"): g.rect(ox+1+x*mw,oy+1+y*mh,mw-1,mh-1,ch.lower() if False else "yellow")
                elif ch in ("G","A","H","K","X","D"): 
                    color={"G":"lime","A":"yellow","H":"red","K":"cyan","X":"green","D":"orange"}.get(ch,"white")
                    g.rect(ox+1+x*mw,oy+1+y*mh,mw-1,mh-1,color)
        px=ox+1+int(self.px*mw); py=oy+1+int(self.py*mh)
        g.rect(px-1,py-1,3,3,"cyan")
        # HUD
        g.text(4,4,f"HP {self.health} Ammo {self.ammo} Keys {self.keys} Score {self.score}","white",size="small")
        parts=[]
        if self.won: parts.append("LEVEL CLEAR!")
        if self.keys==0: parts.append("Find key (cyan) to open door")
        g.text(4,16," ".join(parts),"yellow",size="small")
        g.text(4,self.height-12,"WASD move  R restart  E door","white",size="small")
        if self.won:
            g.text(self.width//2,self.height//2,"LEVEL CLEAR","lime",size="medium",center=True)

    def game_state(self):
        return {"pos":[round(self.px,2),round(self.py,2)],"hp":self.health,"ammo":self.ammo,"keys":self.keys,"score":self.score,"won":self.won}

