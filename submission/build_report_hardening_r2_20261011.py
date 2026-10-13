"""Create a new six-page Lumen report with source-bound second-round UI hardening evidence.

Uses the canonical saved-evidence report builder without changing it. No model
is fitted, no source patient rows are read and no final holdout is rescored.
"""
from argparse import Namespace
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/pdf/lumen-report-hardening-r2-2026-10-11.pdf'
MANIFEST=OUT.with_suffix('.provenance.json')
EARLIER_UI_RECEIPT=ROOT/'research/runtime-hardening-2026-10-11/browser-verification.json'
UI_RECEIPT=ROOT/'research/runtime-hardening-r2-2026-10-11/browser-verification.json'


def record(path):
    path=Path(path)
    return {'path':str(path.resolve()),'bytes':path.stat().st_size,
        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    if OUT.exists() or MANIFEST.exists():raise FileExistsError('Preserve prior PDF editions')
    ui=json.loads(UI_RECEIPT.read_text())
    if (ui['clinical_models_changed'] or ui['final_evaluation_rescored'] or ui['human_usability_study']
            or not ui['temporary_network_blocking_cleared'] or ui['physical_devices']!=1
            or not ui['checks'] or any(row['result']!='passed' for row in ui['checks'])):
        raise ValueError('Require this successful, bounded AI-operated UI check receipt')
    expected_checks={'stale_prediction_failure_after_new_case_commit',
        'stale_prediction_failure_during_newer_case_load'}
    if (ui.get('status')!='passed' or {row['name'] for row in ui['checks']}!=expected_checks
            or not ui.get('sources_unchanged_since_first_held_prediction')
            or not ui.get('fault_harness_stopped')):
        raise ValueError('Require the actual two delayed-failure browser checks and stopped fault harness')
    by_name={row['name']:row for row in ui['checks']}
    first=by_name['stale_prediction_failure_after_new_case_commit']
    second=by_name['stale_prediction_failure_during_newer_case_load']
    if (first['observed_case']!='UCI411-128' or not first['error_hidden'] or first['prediction_disabled']
            or second['after_case_loaded']!='UCI411-050' or not second['during_load_prediction_disabled']
            or not second['during_load_loading_notice_visible'] or not second['after_loading_notice_hidden']
            or second['after_prediction_disabled'] or not second['after_error_hidden']):
        raise ValueError('Delayed-failure observations do not support the bounded report claims')
    ui_record=record(UI_RECEIPT)
    earlier_ui=json.loads(EARLIER_UI_RECEIPT.read_text())
    if (len(earlier_ui['checks'])!=5 or any(row['result']!='passed' for row in earlier_ui['checks'])
            or earlier_ui['human_usability_study'] or earlier_ui['clinical_models_changed']
            or earlier_ui['final_evaluation_rescored']):
        raise ValueError('Require preserved dated five-check earlier browser receipt')
    earlier_ui_record=record(EARLIER_UI_RECEIPT)
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
            text=('<b>AI software checks, 11 October.</b> The fresh six-task review found stale case context and false alarms described as misses; corrections were browser-checked. Five earlier case/profile failure, retry and keyboard checks passed on 11 October. Two synthetic delayed HTTP503 checks confirmed old prediction errors cannot replace a newer case or release prediction controls during its load; the new case then completes normally. Five review tasks completed; the sixth evidenced rotation, zoom and target mapping with an unretained focus/isolation screenshot. These bounded AI-operated checks do not measure human comprehension or usability.')
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
    if record(UI_RECEIPT)!=ui_record or record(EARLIER_UI_RECEIPT)!=earlier_ui_record:
        raise ValueError('UI receipt changed during authoring')
    for key,path in frozen_paths.items():
        if record(path)!=frozen[key]:raise ValueError('Frozen scientific artifact changed during authoring')
    for path,saved in ui_sources.items():
        if record(ROOT/path)!=saved:raise ValueError('Current UI source changed during report authoring')
    proof=json.loads(MANIFEST.read_text())
    proof['schema']='lumen-six-page-ui-hardening-report-r2-v1'
    proof['sources']['ui_hardening_r2_receipt']=ui_record
    proof['sources']['earlier_dated_ui_hardening_receipt']=earlier_ui_record
    proof['sources']['hardening_report_wrapper']=record(__file__)
    proof['ui_hardening_source_bindings']=ui_sources
    proof['frozen_artifacts_unchanged_during_report_build']=frozen
    proof['earlier_dated_fault_and_keyboard_checks_included']=5
    proof['current_r2_browser_checks_included']=len(ui['checks'])
    proof['earlier_source_binding_scope']='Historical tested R1 version; not asserted to match current R2 app source'
    proof['new_scientific_claims']=False
    proof['human_usability_measured']=False
    proof['visual_review']='pending'
    MANIFEST.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({'output':record(OUT),'pages':proof['pages'],'earlier_dated_ui_hardening_checks':5,'r2_browser_checks':len(ui['checks'])},indent=2))


if __name__=='__main__':main()
