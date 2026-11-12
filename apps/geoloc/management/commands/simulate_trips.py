import time
from django.core.management.base import BaseCommand, CommandError
from apps.geoloc.simulation import prepare, advance
from apps.geoloc.models import SimulationRun

class Command(BaseCommand):
    help='Prépare des itinéraires OSRM puis exécute une simulation GPS isolée.'
    def add_arguments(self,p):
        p.add_argument('--prepare',action='store_true')
        p.add_argument('--run-id',type=int)
        p.add_argument('--replay',type=int,help='Nouvelle simulation réutilisant les routes déjà calculées.')
        p.add_argument('--ticks',type=int,default=180)
        p.add_argument('--interval',type=float,default=1)
        p.add_argument('--speed',type=float,default=10)
    def handle(self,*a,**o):
        if o['ticks']<1 or o['interval']<.2 or not 0<o['interval']*o['speed']<=120:raise CommandError('Paramètres de temps invalides.')
        try:
            if sum([bool(o['prepare']),o['run_id'] is not None,o['replay'] is not None])!=1:raise ValueError('Choisir --prepare, --run-id ou --replay.')
            if o['replay'] is not None:
                source=SimulationRun.objects.get(pk=o['replay'])
                run=SimulationRun.objects.create(name=source.name,routes=source.routes)
            else:run=prepare() if o['prepare'] else SimulationRun.objects.get(pk=o['run_id'])
        except Exception as e:raise CommandError(str(e)) from e
        if run.status=='completed':raise CommandError('Simulation terminée : préparer un nouveau trajet.')
        run.status='running';run.save(update_fields=['status','updated_at'])
        self.stdout.write(f'SIMULATION #{run.pk} — aucun compte ni paiement réel modifié.')
        try:
            for i in range(o['ticks']):
                run=advance(run.pk,o['interval']*o['speed'])
                if i%10==0:self.stdout.write(f'{run.elapsed:.0f}s simulées · {run.status}')
                if run.status=='completed':break
                time.sleep(o['interval'])
        except KeyboardInterrupt:
            self.stdout.write('Interruption demandée.')
        finally:
            run.refresh_from_db()
            if run.status=='running':run.status='paused';run.save(update_fields=['status','updated_at'])
            self.stdout.write(f'Fin : {run.status}. Reprise avec --run-id {run.pk}.')
