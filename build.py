import pathlib, subprocess, struct, json, base64, wave
ROOT=pathlib.Path(r'D:\SteamLibrary\steamapps\common\Need for Speed - ProStreet ENG RU')
OUT=pathlib.Path('outputs/ProStreet Sound Lab');OUT.mkdir(parents=True,exist_ok=True)
EXE=pathlib.Path('work/vgmstream/vgmstream-cli.exe').resolve()
assets={};maps={};inventory=[];banks={};skipped=[]
(OUT/'banks').mkdir(exist_ok=True)
names=json.loads(pathlib.Path('work/bank-names.json').read_text())
friendly={'047':'Porsche Carrera GT · V10','062':'Lamborghini Gallardo · V10','068':'Dodge Viper · A','069':'Dodge Viper · B','109':'Dodge Viper · C','126':'Dodge Viper · E','073':'Corvette Z06','076':'Dodge Hemi','078':'VW R32','051':'BMW M3 · C','077':'Plymouth Cuda','079':'Dodge Polara','081':'Subaru WRX · D','082':'Corvette C5','084':'Toyota MR2','086':'Aston Martin DB9 · B','087':'Jaguar XK','090':'Mazda RX-7 · B','091':'Pagani Zonda','099':'Semi Truck','100':'Dodge Charger','120':'Audi R8','123':'Toyota Supra · B','128':'Mercedes SL65 · B','108':'Acura NSX · A','112':'Acura NSX · B'}
def decode(rel,idx,key):
 p=pathlib.Path('work')/(key+'.wav')
 run=subprocess.run([str(EXE),'-i','-s',str(idx),'-o',str(p),str(ROOT/'SOUND'/rel)],capture_output=True,text=True)
 if run.returncode:raise RuntimeError(run.stdout+run.stderr)
 with wave.open(str(p)) as w:duration=w.getnframes()/w.getframerate()
 assets[key]=base64.b64encode(p.read_bytes()).decode();inventory.append({'key':key,'source':rel,'stream':idx,'duration':duration})
for car in sorted({p.name[4:7] for p in (ROOT/'SOUND/ENGINE').glob('car_*-exhaust.tmx')}):
 pack={}
 for channel in ['exhaust','engine']:
  if not (ROOT/'SOUND'/f'ENGINE/car_{car}-{channel}.tmx').exists():continue
  bank=car if channel=='exhaust' else car+'e'
  rel=f'ENGINE/car_{car}-{channel}.tmx';b=(ROOT/'SOUND'/rel).read_bytes();u=lambda p:struct.unpack_from('<I',b,p)[0]
  if u(32)==0:
   skipped.append({'source':rel,'reason':'zero sound count'});continue
  sound_name=names.get(f'car_{car}-{channel}.tmx',{}).get('name','')
  label=f'{car} · '+friendly.get(car,sound_name or 'банк')+' · '+('выхлоп' if channel=='exhaust' else 'двигатель')
  info={'label':label,'internalName':sound_name,'source':rel,'pack':f'banks/car_{car}.js','steady':[],'up':[],'down':[]}
  for i in range(u(32)):
   p=u(88)+i*36;o=u(p+8)+u(92);key=f'car{bank}_{i+1}';decode(rel,i+1,key);pack[key]=assets.pop(key)
   if b[o:o+4]==b'Gnsu':
    lo,hi=struct.unpack_from('<ff',b,o+8);n=u(o+16);positions=list(struct.unpack_from('<'+str(n+1)+'I',b,o+32))
    maps[key]={'min':lo,'max':hi,'positions':positions,'rate':u(o+28)}
    info['up' if positions[-1]>positions[0] else 'down'].append(key)
   else:
    base=struct.unpack_from('<f',b,p+28)[0]
    info['steady'].append({'key':key,'rpm':base if 300<base<15000 else 1000})
  info['steady'].sort(key=lambda x:x['rpm'])
  info['idle']=info['steady'][0]
  info['up'].sort(key=lambda k:next(x['duration'] for x in inventory if x['key']==k),reverse=True)
  info['full']=info['up'][0] if info['up'] else None;info['half']=info['up'][1] if len(info['up'])>1 else info['full'];info['coast']=info['down'][0] if info['down'] else info['full']
  info['maxRpm']=maps[info['full']]['max'] if info['full'] else max(x['rpm'] for x in info['steady'])*1.05
  banks[bank]=info
 if pack:(OUT/f'banks/car_{car}.js').write_text('Object.assign(ASSETS,'+json.dumps(pack)+');',encoding='utf8')
for i in range(1,21):decode('ENGINE/swtn_car_000.abk',i,f'fx{i}')
for i in [1,12,13,14,15,16,17,18,19]:decode('BLOWER/turbo_01.abk',i,f'turbo{i}')
for label,bank in [('base','gear_med_base'),('sport','gear_med_lev3'),('heavy','gear_big_lev3'),('compact','gear_sml_base')]:
 for i in [1,2]:decode(f'SHIFTING/{bank}.abk',i,f'shift_{label}_{i}')
decode('IG_GLOBAL/car_whine.abk',1,'whine');decode('SKIDS/skids_drift_big_mb.abk',1,'drift');decode('SKIDS/skid_big_mb.abk',1,'burnout')
s=pathlib.Path('work/lab.html').read_text(encoding='utf8').replace('/*ASSETS*/','const ASSETS='+json.dumps(assets)+';const MAPS='+json.dumps(maps)+';const INVENTORY='+json.dumps(inventory)+';const BANKS='+json.dumps(banks)+';')
(OUT/'ProStreet Sound Lab.html').write_text(s,encoding='utf8');(OUT/'sample-inventory.json').write_text(json.dumps({'maps':maps,'samples':inventory,'banks':banks,'skipped':skipped},indent=2),encoding='utf8')
print('Built',len(banks),'source banks;',len(inventory),'streams;',len(assets),'embedded shared FX; main HTML',len(s),'characters; skipped',skipped)
