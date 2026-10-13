"""Copy development-only model artifacts into the app, never the final holdout."""
import argparse
from pathlib import Path
import shutil
import json

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, default=root/'training/results-v2')
args = parser.parse_args()
source = args.source.resolve()
benchmark = json.loads((source/'benchmark.json').read_text())
cases = json.loads((source/'cases.json').read_text())
assert not benchmark['protocol']['holdout_scored']
assert not cases['holdout_included']
(root/'artifacts').mkdir(exist_ok=True)
for name in ['models.json','cases.json','input_schema.json','benchmark.json']:
    shutil.copyfile(source/name, root/'artifacts'/name)
shutil.copyfile(root/'training/predict.py', root/'inference.py')
availability=root/'training/results-availability'
if (availability/'models.json').exists():
    for original,name in [('models.json','availability-models.json'),('cases.json','availability-cases.json'),('profiles.json','availability-profiles.json'),('benchmark.json','availability-benchmark.json')]:
        shutil.copyfile(availability/original,root/'artifacts'/name)
final = root/'training/results-final-development/models.json'
if final.exists():
    shutil.copyfile(final, root/'artifacts/final_models.json')
evaluation=root/'training/results-final-development/final_evaluation.json'
if evaluation.exists():
    shutil.copyfile(evaluation,root/'artifacts/final_evaluation.json')
print('Validated model artifacts copied. Restart the server to use them.')
