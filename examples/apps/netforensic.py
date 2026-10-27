
import subprocess, re, time, math, threading, psutil
from vga32.game import GameApp

class NetForensic(GameApp):
    app_id = "apps.netforensic"
    title = "Net Forensic"
    icon = "star"
    category = "Tools"
    width, height = 620, 340
    fps = 2
    pause_unfocused = False
    def start(self):
        self.running=True
        self.devices=[]
        self.known=set()
        self.log=["NetForensic boot"]
        self.scan_interval=120
        self.last_scan=0.0
        self.scanning=False
        self.rx_history=[0]*16
        self.tx_history=[0]*16
        self.last_net_t=time.time()
        self.last_bytes=psutil.net_io_counters()
        self.conns=(0,0,0)
        self.last_conn_t=0.0
        self.t=0.0
        threading.Thread(target=self._scan_worker, daemon=True).start()
    def _scan(self):
        try:
            out=subprocess.check_output(["nmap","-sn","192.168.1.0/24"],text=True,timeout=120,stderr=subprocess.STDOUT)
        except Exception as e:
            self.log.append("scan err: "+str(e)[:40]); self.log=self.log[-12:]
            return
        hosts=[h.strip() for h in re.findall(r"Nmap scan report for (.+)",out)]
        try:
            neigh=subprocess.check_output(["ip","neigh"],text=True,timeout=10)
        except Exception:
            neigh=""
        macmap={}
        for line in neigh.splitlines():
            m=re.match(r"(\d+\.\d+\.\d+\.\d+)\s+dev\s+\S+\s+lladdr\s+([0-9a-f:]{17})",line)
            if m: macmap[m.group(1)]=m.group(2)
        infos=[{"ip":ip,"mac":macmap.get(ip,"unknown")} for ip in hosts]
        new=[ip for ip in hosts if ip not in self.known] if self.known else []
        gone=[ip for ip in self.known if ip not in hosts] if self.known else []
        if new: self.log.append(f"{time.strftime('%H:%M')} NEW: {', '.join(new[:3])}")
        if gone: self.log.append(f"{time.strftime('%H:%M')} down: {', '.join(gone[:3])}")
        if not new and not gone and self.known: self.log.append(f"{time.strftime('%H:%M')} stable ({len(hosts)})")
        if not self.known: self.log.append(f"{time.strftime('%H:%M')} found {len(hosts)} hosts")
        self.log=self.log[-12:]
        self.devices=infos
        self.known=set(hosts)
        self.last_scan=time.time()
        self.scanning=False
    def _scan_worker(self):
        while True:
            self.scanning=True
            self._scan()
            time.sleep(self.scan_interval)
    def update_metrics(self):
        now=time.time()
        cur=psutil.net_io_counters()
        dt=max(0.5,now-self.last_net_t)
        rxr=(cur.bytes_recv-self.last_bytes.bytes_recv)/dt
        txr=(cur.bytes_sent-self.last_bytes.bytes_sent)/dt
        self.rx_rate=rxr; self.tx_rate=txr
        self.last_net_t=now; self.last_bytes=cur
        self.rx_history=(self.rx_history+[rxr/1024.0])[-32:]
        self.tx_history=(self.tx_history+[txr/1024.0])[-32:]
        if now-self.last_conn_t>5:
            try:
                c=psutil.net_connections(kind="inet")
                self.conns=(sum(1 for x in c if x.type==1),sum(1 for x in c if x.type==2),len(c))
            except Exception: pass
            self.last_conn_t=now
    def update(self,dt):
        self.t+=dt
        self.update_metrics()
    def _bar(self,g,x,y,w,h,val,mx,color):
        g.rect(x,y,w,h,"darkgray")
        filled=max(1,min(w,int(w*(val/max(1,mx)))))
        g.rect(x,y,filled,h,color)
    def _chart(self,g,x,y,w,h,vals,color):
        g.rect(x,y,w,h,"black",outline="gray")
        if len(vals)<2: return
        mx=max(max(vals),1)
        for i in range(1,len(vals)):
            x1=x+int((i-1)*w/(len(vals)-1)); y1=y+h-int(vals[i-1]*h/mx)
            x2=x+int(i*w/(len(vals)-1)); y2=y+h-int(vals[i]*h/mx)
            g.line(x1,y1,x2,y2,color,1)
    def render(self,g):
        g.clear("navy")
        g.rect(0,0,g.w,20,"black")
        g.text(6,3,"NetForensic","lime",size="medium",bold=True) if False else g.text(6,3,"NetForensic","lime",size="medium")
        g.text(g.w-100,5,time.strftime("%H:%M:%S"),"cyan",size="small")
        y=22
        g.text(6,y,f"Devices:{len(self.devices)} Scan:{'yes' if self.scanning else 'no'}","white",size="small"); y+=12
        g.text(6,y,f"RX {self.rx_rate/1024:.1f}KB/s TX {self.tx_rate/1024:.1f}KB/s TCP {self.conns[0]} UDP {self.conns[1]} Tot {self.conns[2]}","cyan",size="small"); y+=14
        self._chart(g,6,y,g.w-12,70,self.rx_history,"lime")
        g.text(6,y-2,"RX/TX KB/s","gray",size="small")
        by=y+74
        g.text(6,by,"RX","white",size="small"); self._bar(g,30,by,180,8,self.rx_rate/1024.0,max(1,max(self.rx_history+[1])),"green")
        g.text(6,by+12,"TX","white",size="small"); self._bar(g,30,by+12,180,8,self.tx_rate/1024.0,max(1,max(self.tx_history+[1])),"yellow")
        dy=by+30
        g.text(6,dy,"Devices (IP / MAC)","yellow",size="small"); dy+=11
        for dev in self.devices[:9]:
            g.text(6,dy,f"{dev['ip'][:15]:15} {dev['mac'][:17]}","white",size="small"); dy+=10
            if dy>g.h-90: break
        zx=g.w//2
        g.text(zx,by-10,"Event Log","yellow",size="small")
        ly=by
        for line in self.log[-9:]:
            g.text(zx,ly,line[:48],"green",size="small"); ly+=10
            if ly>g.h-20: break
        g.text(6,g.h-12,"NetForensic by Hermes | live network forensics","gray",size="small")
    def game_state(self):
        return {"devices":len(self.devices),"rx_kb":round(self.rx_rate/1024,2),"tx_kb":round(self.tx_rate/1024,2),"conns":self.conns,"scanning":self.scanning,"log_lines":len(self.log)}
