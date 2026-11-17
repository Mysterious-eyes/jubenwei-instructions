"""Shared portable orchestration; snapshot directories are read-only inputs."""
import hashlib,json,os,subprocess,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
RELEASE=HERE.parents[1]
GENERATORS=HERE/'generators'

def resolve(path):
    path=Path(path)
    return path.resolve() if path.is_absolute() else (RELEASE/path).resolve()

def sha256(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_json(path,data):
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def new_output(path):
    path=resolve(path)
    if path.is_relative_to(RELEASE) and not path.is_relative_to(RELEASE/'reproduced'):
        raise ValueError('Inside the release, output must be under reproduced/. Archived data/code cannot be overwritten.')
    if path.exists():raise ValueError(f'Output already exists; choose a new directory: {path}')
    path.mkdir(parents=True)
    return path

def generate_tasks(source,task_dir,report_path,reference=None):
    source=Path(source).resolve();task_dir=Path(task_dir).resolve();report_path=Path(report_path).resolve()
    task_dir.mkdir(parents=True,exist_ok=False)
    environment=os.environ.copy()
    environment.update(JUBENWEI_BUILD_SOURCE=str(source),JUBENWEI_BUILD_OUTPUT=str(task_dir),JUBENWEI_BUILD_REPORT=str(report_path),PYTHONIOENCODING='utf-8')
    if reference is not None:environment['JUBENWEI_BUILD_REFERENCE']=str(Path(reference).resolve())
    else:environment.pop('JUBENWEI_BUILD_REFERENCE',None)
    result=subprocess.run([sys.executable,'-B','-X','utf8',str(GENERATORS/'run_all.py')],cwd=GENERATORS,env=environment,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding='utf-8')
    (report_path.parent/'generation_stdout.txt').write_text(result.stdout,encoding='utf-8')
    (report_path.parent/'generation_stderr.txt').write_text(result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError('Task generation failed; inspect generation_stdout.txt and generation_stderr.txt in the independent output directory.')
    report=json.loads(report_path.read_text(encoding='utf-8'))
    print('Generated and validated '+str(len(report['datasets']))+' tasks.',flush=True)
    return report
