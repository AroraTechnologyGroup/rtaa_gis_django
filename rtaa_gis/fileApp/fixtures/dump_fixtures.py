import os
import subprocess
from subprocess import PIPE
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def dump(model):
    kwargs = dict()
    kwargs['cwd'] = BASE_DIR
    kwargs['stdout'] = PIPE
    kwargs['stderr'] = PIPE
    proc = subprocess.Popen("python manage.py dumpdata fileApp.{0} --indent 4 --output fileApp/fixtures/json/{1}.json".format(model, model.lower()),
                            **kwargs)
    std_out, std_err = proc.communicate()
    if std_out:
        print(std_out)
    if std_err:
        print(std_err)

    spec = os.path.join(BASE_DIR, "fileApp/fixtures/json/{}.json".format(model.lower()))
    if os.path.exists(spec):
        fixt = json.loads(open(spec, 'r').read())
        output = json.dumps(fixt)
        out_file = spec
        new_fixt = open(out_file, 'w')
        new_fixt.write(output)
        new_fixt.close()

models = ['EngineeringFileModel', 'GridCell', 'EngineeringAssignment']
for x in models:
    dump(x)
