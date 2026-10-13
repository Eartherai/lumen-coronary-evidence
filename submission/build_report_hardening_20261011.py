"""Create a new six-page Lumen report with source-bound UI hardening evidence.

Uses the canonical saved-evidence report builder without changing it. No model
is fitted, no source patient rows are read and no final holdout is rescored.
"""
from argparse import Namespace
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/pdf/lumen-report-hardening-2026-10-11.pdf'
MANIFEST=OUT.with_suffix('.provenance.json')
UI_RECEIPT=ROOT/'research/runtime-hardening-2026-10-11/browser-verification.json'


def record(path):
    path=Path(path)
    return {'path':str(path.resolve()),'bytes':path.stat().st_size,
        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    if OUT.exists() or MANIFEST.exists():raise FileExistsError('Preserve prior PDF editions')
    ui=json.loads(UI_RECEIPT.read_text())
    if (ui['clinical_models_changed'] or ui['final_evaluation_rescored'] or ui['human_usability_study']
            or not ui['temporary_network_blocking_cleared'] or ui['physical_devices']!=1
            or len(ui['checks'])!=5 or any(row['result']!='passed' for row in ui['checks'])):
        raise ValueError('Require this successful, bounded AI-operated UI check receipt')
    ui_record=record(UI_RECEIPT)
    ui_sources={path:record(ROOT/path) for path in ui['source_bindings_recorded_after_checks']}
    for path, saved in ui['source_bindings_recorded_after_checks'].items():
        if ui_sources[path]['sha256']!=saved['sha256'] or ui_sources[path]['bytes']!=saved['bytes']:
            raise ValueError('Current UI source differs from the tested hardening version')
    frozen_paths={
        'final_evaluation':ROOT/'artifacts/final_evaluation.json',
        'final_models':ROOT/'artifacts/final_models.json',
        'final_protocol':ROOT/'submission/final-protocol-freeze.json',
    }
    frozen={key:record(path) for key,path in frozen_paths.items()}
    spec=importlib.util.spec_from_file_location('lumen_saved_report_builder',ROOT/'submission/build_report.py')
    builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    original_p=builder.p
    replaced=[]
    def p(text,style='body'):
        if text.startswith('<b>Independent AI review, 11 October.</b>'):
            text=('<b>Independent AI checks, 11 October.</b> A fresh review found stale prior-case context and false alarms described as misses; both were corrected and browser-checked. Follow-up injected case/profile load failures restored the prior loaded state, healthy retry worked, and keyboard prediction/matrix selection retained button focus. Five fresh-review tasks completed; the sixth evidenced rotation, zoom and target mapping, with an unretained focus/isolation screenshot. These are AI software checks, not measured human comprehension or usability.')
            replaced.append('independent_ai_checks')
        return original_p(text,style)
    builder.p=p
    args=Namespace(
        v1=ROOT/'training/results/benchmark.json',
        v2=ROOT/'training/results-v2/benchmark.json',
        v3=ROOT/'training/results-v3/benchmark.json',
        availability=ROOT/'training/results-availability/benchmark.json',
        final=frozen_paths['final_evaluation'],
        shap=ROOT/'training/results-availability/shap-verification.json',
        cohort=ROOT/'artifacts/cohort-audit.json',
        cohort_shap=ROOT/'public/assets/cohort-audit-verification.json',
        ai_review=ROOT/'research/independent-ai-review-2026-10-11/ai-review.json',
        runtime=[ROOT/'research/runtime-2026-10-11/chromium-idle.json',ROOT/'research/runtime-2026-10-11/chromium-actions.json'],
        external_compatibility=ROOT/'research/lumen-external-cohort-2026-10-11/angiocad-compatibility-audit.json',
        post_fix_check=ROOT/'research/runtime-2026-10-11/review-fix-ui-receipt.json',
        screenshot=None,output=OUT,manifest=MANIFEST,
    )
    builder.build(args)
    if replaced!=['independent_ai_checks']:raise ValueError('Expected report section was not updated exactly once')
    if record(UI_RECEIPT)!=ui_record:raise ValueError('UI receipt changed during authoring')
    for key,path in frozen_paths.items():
        if record(path)!=frozen[key]:raise ValueError('Frozen scientific artifact changed during authoring')
    proof=json.loads(MANIFEST.read_text())
    proof['schema']='lumen-six-page-ui-hardening-report-v1'
    proof['sources']['ui_hardening_receipt']=ui_record
    proof['sources']['hardening_report_wrapper']=record(__file__)
    proof['ui_hardening_source_bindings']=ui_sources
    proof['frozen_artifacts_unchanged_during_report_build']=frozen
    proof['fault_and_keyboard_checks_included']=5
    proof['human_usability_measured']=False
    proof['visual_review']='pending'
    MANIFEST.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({'output':record(OUT),'pages':proof['pages'],'ui_hardening_checks':5},indent=2))


if __name__=='__main__':main()
