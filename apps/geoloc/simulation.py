"""Distance-based road simulation. No customer, ride or financial writes."""
import json
import math
import time
from urllib.request import Request, urlopen
from django.conf import settings
from django.db import transaction, OperationalError
from django.utils import timezone
from .models import SimulationRun

SCENARIOS = [
    ('Gombe → Limete', (15.287,-4.302), (15.309,-4.319), (15.338,-4.365)),
    ('Lingwala → Lemba', (15.295,-4.333), (15.317,-4.345), (15.341,-4.402)),
    ('Matete → Ndjili', (15.355,-4.386), (15.369,-4.389), (15.403,-4.407)),
]

def distance(a,b):
    """Great-circle distance, coordinates in GeoJSON longitude/latitude order."""
    lon1,lat1,lon2,lat2=map(math.radians,[*a,*b])
    return 6371000*2*math.asin(min(1,math.sqrt(math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2)))

def road(start,end):
    base=getattr(settings,'SIMULATION_ROUTER_URL','https://router.project-osrm.org').rstrip('/')
    coords=f'{start[0]},{start[1]};{end[0]},{end[1]}'
    req=Request(f'{base}/route/v1/driving/{coords}?overview=full&geometries=geojson&steps=false',headers={'User-Agent':'GO-MBOKA-Recette/1.0'})
    with urlopen(req,timeout=30) as response: data=json.load(response)
    if data.get('code')!='Ok' or not data.get('routes'):raise ValueError('Itinéraire routier introuvable. Aucun tracé artificiel substitué.')
    if any(p['distance']>400 for p in data['waypoints']):raise ValueError('Point trop éloigné du réseau routier.')
    coordinates=data['routes'][0]['geometry']['coordinates']
    if len(coordinates)<2:raise ValueError('Géométrie routière incomplète.')
    lengths=[0.0]
    for a,b in zip(coordinates,coordinates[1:]):lengths.append(lengths[-1]+distance(a,b))
    return {'coordinates':coordinates,'lengths':lengths,'distance':lengths[-1]}

def prepare():
    """Fetch routes once, before creating a run; fail atomically on routing outage."""
    routes=[]
    for i,(label,origin,pickup,dropoff) in enumerate(SCENARIOS):
        approach=road(origin,pickup);trip=road(approach['coordinates'][-1],dropoff)
        if distance(approach['coordinates'][-1],trip['coordinates'][0])>10:raise ValueError('Raccord de prise en charge discontinu.')
        routes.append({'id':i+1,'label':label,'moto':f'Moto SIM-{i+1:02}','client':f'Client SIM-{i+1:02}','approach':approach,'trip':trip,'source':'OSRM / OpenStreetMap','profile':'driving'})
    run=SimulationRun.objects.create(name='Kinshasa — itinéraires routiers',routes=routes)
    run.frame=frame_at(routes,0);run.save(update_fields=['frame','updated_at'])
    return run

def interpolate(route,meters):
    points=route['coordinates'];lengths=route['lengths']
    meters=max(0,min(meters,lengths[-1]))
    for i in range(1,len(points)):
        if lengths[i]>=meters:
            fraction=(meters-lengths[i-1])/max(.00001,lengths[i]-lengths[i-1])
            a,b=points[i-1],points[i]
            return [a[0]+(b[0]-a[0])*fraction,a[1]+(b[1]-a[1])*fraction]
    return points[-1]

def trip_progress(t,total):
    """Cruise 30 km/h, jam at 35% (5 km/h), stop at 65% for 18 seconds."""
    cruise=30/3.6;slow=5/3.6
    phases=[(total*.35/cruise,cruise,'en_course'),(total*.15/slow,slow,'embouteillage'),(total*.15/cruise,cruise,'en_course'),(18,0,'arret'),(total*.35/cruise,cruise,'en_course')]
    meters=0
    for seconds,speed,event in phases:
        if t<seconds:return meters+max(0,t)*speed,speed*3.6,event,False
        meters+=seconds*speed;t-=seconds
    return total,0,'arrivee',True

def frame_at(routes,elapsed):
    vehicles=[];clients=[];complete=True
    for i,r in enumerate(routes):
        t=max(0,elapsed-i*12);approach=r['approach'];trip=r['trip']
        approach_time=approach['distance']/(24/3.6)
        if t<approach_time:
            pos=interpolate(approach,t*24/3.6);client_pos=trip['coordinates'][0];phase='approche';speed=24;done=False
        elif t<approach_time+25:
            pos=trip['coordinates'][0];client_pos=pos;phase='prise_en_charge';speed=0;done=False
        else:
            meters,speed,phase,done=trip_progress(t-approach_time-25,trip['distance'])
            pos=interpolate(trip,meters);client_pos=pos
        complete &= done
        vehicles.append({'id':r['id'],'name':r['moto'],'longitude':pos[0],'latitude':pos[1],'speed_kmh':round(speed,1),'phase':phase,'simulation':True,'route':r['label']})
        clients.append({'id':r['id'],'name':r['client'],'longitude':client_pos[0],'latitude':client_pos[1],'phase':'attente_moto' if phase=='approche' else phase,'simulation':True})
    return {'simulation':True,'elapsed':elapsed,'vehicles':vehicles,'clients':clients,'completed':complete}

@transaction.atomic
def _advance(run_id,seconds):
    if not 0<seconds<=120:raise ValueError('Pas de temps entre 0 et 120 secondes.')
    run=SimulationRun.objects.select_for_update().get(pk=run_id)
    if run.status!='running':return run
    run.elapsed+=seconds;run.frame=frame_at(run.routes,run.elapsed)
    run.history=(run.history+[run.frame])[-2000:]
    if run.frame['completed']:run.status='completed'
    run.save(update_fields=['elapsed','frame','history','status','updated_at'])
    return run

def advance(run_id,seconds):
    # SQLite cannot upgrade a read transaction while another writer commits.
    # Retry the whole rolled-back transaction, never a partially applied tick.
    for attempt in range(6):
        try:
            return _advance(run_id,seconds)
        except OperationalError as error:
            if 'locked' not in str(error).lower() or attempt==5:
                raise
            time.sleep(.05 * 2**attempt)


def snapshot():
    run=SimulationRun.objects.order_by('-pk').first()
    if not run:return None
    return {'id':run.pk,'name':run.name,'status':run.status,'updated_at':run.updated_at,**run.frame,'trails':[{'id':r['id'],'coordinates':[[v['longitude'],v['latitude']] for h in run.history for v in h['vehicles'] if v['id']==r['id']]} for r in run.routes],'routes':[{'id':r['id'],'label':r['label'],'source':r['source'],'approach':r['approach']['coordinates'],'trip':r['trip']['coordinates']} for r in run.routes]}
