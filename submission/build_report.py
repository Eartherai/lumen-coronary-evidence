"""Build the six-page Lumen technical report from saved evidence JSON.

Uses ReportLab vector charts; never reads source patient rows or evaluates models.
Run with the bundled PDF Python runtime or `python3` with reportlab and pypdf.
All evidence paths can be overridden for the frozen release.
"""
import argparse
from datetime import date
from pathlib import Path
import json
import math
import hashlib
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    Image, KeepTogether,
)
from reportlab.graphics.shapes import Drawing, String, Rect, Line
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT.parent / 'research/track-a-feasibility/model'
TARGETS = ['CAD', 'LAD', 'LCX', 'RCA']
NAVY = colors.HexColor('#122638')
TEAL = colors.HexColor('#087e83')
MINT = colors.HexColor('#dff1ee')
ORANGE = colors.HexColor('#b56228')
INK = colors.HexColor('#253747')
GRAY = colors.HexColor('#657785')
LIGHT = colors.HexColor('#eff3f5')
WHITE = colors.white
PAGE_W, PAGE_H = A4
WIDTH = PAGE_W - 88


def existing(*paths):
    for path in paths:
        if path.exists():
            return path
    return paths[0]


def load(path, required=True):
    if path and Path(path).exists():
        return json.loads(Path(path).read_text())
    if required:
        raise FileNotFoundError(path)
    return None


def finite_number(value):
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Expected finite evidence metric')
    return float(value)


def num(value):
    return f'{finite_number(value):.3f}'


def metric(target, key):
    if 'oof' in target:
        return target['oof'][key]
    if 'metrics' in target:
        return target['metrics']
    return target


def final_metrics(data):
    """Accept explicit per-target metrics; refuse unrecognized test evidence."""
    if not data:
        return None
    raw = data.get('targets') or data.get('results') or data.get('metrics')
    if not isinstance(raw, dict) or not all(t in raw for t in TARGETS):
        raise ValueError('Final evaluation needs CAD/LAD/LCX/RCA target metrics')
    output = {}
    for target in TARGETS:
        result = metric(raw[target], 'selected')
        if 'test' in result:
            result = result['test']
        for key in ['roc_auc', 'accuracy', 'precision', 'recall', 'f1', 'brier']:
            finite_number(result[key])
        output[target] = result
    return output


def register_fonts():
    font_root = Path('/Users/earther/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/fonts')
    regular = font_root / 'DejaVuSans.ttf'
    bold = font_root / 'DejaVuSans-Bold.ttf'
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont('Lumen', str(regular)))
        pdfmetrics.registerFont(TTFont('LumenBold', str(bold)))
        pdfmetrics.registerFontFamily('Lumen', normal='Lumen', bold='LumenBold', italic='Lumen', boldItalic='LumenBold')
        return 'Lumen', 'LumenBold'
    return 'Helvetica', 'Helvetica-Bold'


FONT, BOLD = register_fonts()
STYLES = {
    'body': ParagraphStyle('body', fontName=FONT, fontSize=9.8, leading=14.0, textColor=INK, spaceAfter=8),
    'small': ParagraphStyle('small', fontName=FONT, fontSize=8.3, leading=11.4, textColor=GRAY, spaceAfter=6),
    'caption': ParagraphStyle('caption', fontName=FONT, fontSize=8.5, leading=12.0, textColor=GRAY, spaceAfter=10),
    'h1': ParagraphStyle('h1', fontName=BOLD, fontSize=24, leading=29, textColor=NAVY, spaceAfter=12),
    'h2': ParagraphStyle('h2', fontName=BOLD, fontSize=17, leading=22, textColor=NAVY, spaceAfter=11),
    'h3': ParagraphStyle('h3', fontName=BOLD, fontSize=11.2, leading=15, textColor=TEAL, spaceBefore=5, spaceAfter=5),
    'eyebrow': ParagraphStyle('eyebrow', fontName=BOLD, fontSize=8.8, leading=12, textColor=TEAL, spaceAfter=7),
    'table': ParagraphStyle('table', fontName=FONT, fontSize=8.4, leading=11, textColor=INK),
    'thead': ParagraphStyle('thead', fontName=BOLD, fontSize=8.2, leading=11, textColor=WHITE),
    'mono': ParagraphStyle('mono', fontName='Courier', fontSize=8.5, leading=12, textColor=NAVY, spaceAfter=8),
}


def p(text, style='body'):
    return Paragraph(text, STYLES[style])


def box(text, background=MINT, color=INK):
    inner = Paragraph(text, ParagraphStyle('boxbody', parent=STYLES['body'], textColor=color, spaceAfter=0))
    table = Table([[inner]], colWidths=[WIDTH])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), background),
        ('LEFTPADDING', (0, 0), (-1, -1), 12), ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    return table


def table(headers, rows, widths, numeric=False):
    data = [[p(escape(str(x)), 'thead') for x in headers]]
    data += [[p(str(x), 'table') for x in row] for row in rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LINEBELOW', (0, -1), (-1, -1), .6, colors.HexColor('#d4dfe5')),
    ]))
    return t


def metric_table(values, include_ci=False):
    if include_ci:
        headers = ['Target', 'AUC', '95% AUC interval', 'Acc.', 'Prec.', 'Recall', 'F1', 'Brier']
        widths = [42, 42, 104, 49, 54, 54, 52, WIDTH - 397]
        rows = []
        for t in TARGETS:
            m = values[t]
            interval = m.get('roc_auc_95_ci_conditional') or m.get('roc_auc_95_ci')
            ci = f'{num(interval[0])} - {num(interval[1])}' if interval else 'Not saved'
            rows.append([t, num(m['roc_auc']), ci, *[num(m[x]) for x in ['accuracy','precision','recall','f1','brier']]])
    else:
        headers = ['Target', 'AUC', 'Acc.', 'Prec.', 'Recall', 'F1', 'Brier']
        widths = [55] + [(WIDTH - 55) / 6] * 6
        rows = [[t, *[num(values[t][x]) for x in ['roc_auc','accuracy','precision','recall','f1','brier']]] for t in TARGETS]
    return table(headers, rows, widths)


def workflow(completed=False):
    d = Drawing(WIDTH, 90)
    labels = [('303 records', 'Source hash checked'), ('242 development', 'Nested model selection'), ('61 final holdout', 'Scored once after freeze' if completed else 'Reserved until freeze')]
    w = (WIDTH - 34) / 3
    for i, (a, b) in enumerate(labels):
        x = i * (w + 17)
        d.add(Rect(x, 22, w, 56, rx=5, fillColor=LIGHT if i != 1 else MINT, strokeColor=None))
        d.add(String(x + 11, 56, a, fontName=BOLD, fontSize=11, fillColor=NAVY))
        d.add(String(x + 11, 38, b, fontName=FONT, fontSize=8.1, fillColor=GRAY))
    d.add(String(0, 6, 'All four target columns are excluded from every input pipeline.', fontName=FONT, fontSize=8.8, fillColor=TEAL))
    return d


def tradeoff_chart(v1, v2):
    d = Drawing(WIDTH, 144)
    chart = HorizontalBarChart()
    chart.x = 105; chart.y = 19; chart.width = WIDTH - 133; chart.height = 104
    chart.data = [
        tuple(v1[t]['oof']['logistic'][m] for t, m in [('RCA','precision'),('RCA','recall'),('LCX','precision'),('LCX','recall')]),
        tuple(v2[t]['oof']['selected'][m] for t, m in [('RCA','precision'),('RCA','recall'),('LCX','precision'),('LCX','recall')]),
    ]
    chart.categoryAxis.categoryNames = ['RCA precision', 'RCA recall', 'LCX precision', 'LCX recall']
    chart.categoryAxis.labels.fontName = FONT; chart.categoryAxis.labels.fontSize = 8.2
    chart.valueAxis.valueMin = 0; chart.valueAxis.valueMax = 1; chart.valueAxis.valueStep = .25
    chart.valueAxis.labels.fontName = FONT; chart.valueAxis.labels.fontSize = 8
    chart.valueAxis.strokeColor = colors.HexColor('#b9c7cf')
    chart.bars[0].fillColor = colors.HexColor('#8097a8')
    chart.bars[1].fillColor = TEAL
    chart.bars.strokeColor = None
    chart.barSpacing = 1; chart.groupSpacing = 5
    d.add(chart)
    for x, label, color in [(110, 'V1: fixed 0.5', colors.HexColor('#8097a8')), (276, 'V2: inner F1 threshold', TEAL)]:
        d.add(Rect(x, 132, 8, 8, fillColor=color, strokeColor=None))
        d.add(String(x+13, 132, label, fontName=FONT, fontSize=8.2, fillColor=GRAY))
    return d


def availability_chart(data):
    profiles = list(data['profiles'].values())
    d = Drawing(WIDTH, 169)
    plot = LinePlot()
    plot.x = 43; plot.y = 37; plot.width = WIDTH - 60; plot.height = 108
    plot.data = [
        [(i+1, metric(profile['targets'][t], 'selected')['roc_auc']) for i, profile in enumerate(profiles)]
        for t in TARGETS
    ]
    palette = [TEAL, colors.HexColor('#3266a0'), ORANGE, colors.HexColor('#84649f')]
    plot.xValueAxis.valueMin = 1; plot.xValueAxis.valueMax = len(profiles)
    plot.xValueAxis.valueSteps = list(range(1,len(profiles)+1))
    plot.xValueAxis.labelTextFormat = lambda value: ''
    plot.yValueAxis.valueMin = .5; plot.yValueAxis.valueMax = 1.0; plot.yValueAxis.valueStep = .1
    for axis in [plot.xValueAxis,plot.yValueAxis]:
        axis.labels.fontName = FONT; axis.labels.fontSize = 8
        axis.strokeColor = colors.HexColor('#b9c7cf')
    for i, color in enumerate(palette):
        plot.lines[i].strokeColor = color; plot.lines[i].strokeWidth = 2
    d.add(plot)
    for i,t in enumerate(TARGETS):
        x = 44 + i*91
        d.add(Line(x,158,x+14,158,strokeColor=palette[i],strokeWidth=2))
        d.add(String(x+19,154,t,fontName=BOLD,fontSize=8.4,fillColor=palette[i]))
    d.add(String(0,154,'AUC',fontName=FONT,fontSize=8.5,fillColor=GRAY))
    labels = ['History','+ exam','+ ECG','+ lab','+ echo']
    for i in range(len(profiles)):
        x = 43 + i*(WIDTH-60)/max(1,len(profiles)-1)
        d.add(String(x,23,labels[i] if i<len(labels) else str(i+1),textAnchor='middle',fontName=FONT,fontSize=8.1,fillColor=GRAY))
    return d


def architecture():
    d=Drawing(WIDTH,84)
    blocks=[('Browser','3D meshes + inputs'),('Python API','Schema + case routing'),('JSON artifacts','Score + explanation')]
    w=(WIDTH-38)/3
    for i,(a,b) in enumerate(blocks):
        x=i*(w+19)
        d.add(Rect(x,27,w,46,rx=4,fillColor=MINT if i==2 else LIGHT,strokeColor=None))
        d.add(String(x+10,55,a,fontName=BOLD,fontSize=10,fillColor=NAVY))
        d.add(String(x+10,38,b,fontName=FONT,fontSize=7.9,fillColor=GRAY))
        if i<2:
            d.add(Line(x+w+3,49,x+w+15,49,strokeColor=TEAL,strokeWidth=1.5))
    d.add(String(0,8,'Truth reveal is a separate API path. Edited inputs have no observed edited outcome.',fontName=FONT,fontSize=8.5,fillColor=GRAY))
    return d


def audit_summary(cohort):
    """Describe existing recorded flags; do not fit or score another cohort."""
    if not cohort:
        return None
    if cohort['n_development'] != 242 or cohort['holdout_included'] or len(cohort['cases']) != 242:
        raise ValueError('Report audit requires the complete development-only cohort')
    summaries = {}
    for target in TARGETS:
        agreeing = wrong = false_positive = false_negative = 0
        for case in cohort['cases']:
            flags = [case['profile_predictions'][profile][target]['predicted_label'] for profile in cohort['profile_order']]
            same = len(set(flags)) == 1
            agreeing += same
            if same and flags[0] != case['truth'][target]:
                wrong += 1
                false_positive += flags[0] == 1
                false_negative += flags[0] == 0
        summaries[target] = {'agreeing': agreeing, 'wrong': wrong, 'fp': false_positive, 'fn': false_negative}
    expected = {'CAD': (182, 12), 'LAD': (161, 33), 'LCX': (172, 60), 'RCA': (164, 58)}
    if {target: (row['agreeing'], row['wrong']) for target, row in summaries.items()} != expected:
        raise ValueError('Audit counts differ from the preserved development agreement probe')
    return summaries


def audit_overview():
    """A labeled static scientific diagram, not a claimed browser capture."""
    d = Drawing(WIDTH, 194)
    columns = [('242 records', 'Every development row', 'No curated success selection'),
               ('20 model views', '5 profiles x 4 targets', 'Exclude the entire outer fold'),
               ('One audit trail', 'Find, inspect, reveal', 'Recorded outcomes disclosed')]
    w = (WIDTH - 24) / 3
    for i, (heading, first, second) in enumerate(columns):
        x = i * (w + 12)
        d.add(Rect(x, 88, w, 94, rx=6, fillColor=MINT if i == 1 else LIGHT, strokeColor=None))
        d.add(String(x + 10, 151, heading, fontName=BOLD, fontSize=12, fillColor=NAVY))
        d.add(String(x + 10, 130, first, fontName=FONT, fontSize=8.2, fillColor=INK))
        d.add(String(x + 10, 111, second, fontName=FONT, fontSize=7.2, fillColor=GRAY))
    d.add(Rect(0, 19, WIDTH, 52, rx=5, fillColor=colors.HexColor('#fff0e5'), strokeColor=None))
    d.add(String(12, 50, 'Five profiles can agree and still be wrong.', fontName=BOLD, fontSize=11, fillColor=ORANGE))
    d.add(String(12, 32, 'LCX: 60 incorrect flags among 172 agreeing development records. Agreement is not confidence.',
                 fontName=FONT, fontSize=8, fillColor=INK))
    return d


def runtime_summary(samples):
    """Summarize saved opt-in software captures; never operate a browser."""
    if not samples:
        return None
    for sample in samples:
        if (sample['schema'] != 'lumen-local-runtime-sample-v1'
                or sample['status'] != 'measured' or sample['hidden_transitions']):
            raise ValueError('Report runtime evidence must be a completed foreground software sample')
    action_sample = samples[-1]
    operations = action_sample['operations']
    completed = [operation for operation in operations
                 if operation.get('status', 'completed') == 'completed'
                 and operation.get('dom_updated_ms') is not None]
    if not completed:
        raise ValueError('Report needs at least one observed completed action')
    dom = [finite_number(operation['dom_updated_ms']) for operation in completed]
    next_render = [finite_number(operation['next_render_callback_ms']) for operation in completed
                   if operation.get('next_render_callback_ms') is not None]
    rates = [finite_number(sample['frame_summary']['frame_callbacks_per_second']) for sample in samples]
    maxima = [finite_number(sample['frame_summary']['interval_ms']['maximum']) for sample in samples]
    environment = action_sample['environment_start']
    viewport = environment['viewport']
    return {'rates': rates, 'max_interval': max(maxima), 'n_completed': len(completed),
            'n_attempted_exported': len(operations), 'dom_min': min(dom), 'dom_max': max(dom),
            'next_render_min': min(next_render) if next_render else None,
            'next_render_max': max(next_render) if next_render else None,
            'width': viewport['width'], 'height': viewport['height'],
            'dpr': finite_number(environment['device_pixel_ratio']),
            'renderer': environment['renderer'],
            'durations_seconds': [finite_number(sample['requested_duration_ms']) / 1000 for sample in samples]}


def build(args):
    v1=load(args.v1); v2=load(args.v2); v3=load(args.v3,False)
    available=load(args.availability,False); final=load(args.final,False); shap_check=load(args.shap,False)
    cohort=load(args.cohort,False); cohort_shap=load(args.cohort_shap,False); cohort_counts=audit_summary(cohort)
    ai_review=load(args.ai_review,False)
    post_fix=load(args.post_fix_check,False)
    external_compatibility=load(args.external_compatibility,False)
    runtime_paths=[path for path in args.runtime if Path(path).exists()]
    runtime=runtime_summary([load(path) for path in runtime_paths]) if runtime_paths else None
    if ai_review and (ai_review['reviewer_kind'] != 'ai' or ai_review['human_signoff_completed']
                      or ai_review['human_task_timing_recorded']):
        raise ValueError('This edition expects a separate AI review, not a human usability claim')
    if ai_review and (not post_fix or len(post_fix['checks']) != 2
                      or any(check['result'] != 'passed' for check in post_fix['checks'])):
        raise ValueError('AI-review correction claims require the successful separate UI receipt')
    if cohort_shap and (cohort_shap['status'] != 'passed' or cohort_shap['n_explanations_verified'] != 4840
                        or cohort_shap['n_models_verified'] != 100):
        raise ValueError('Complete development audit needs its successful 4840-output actual-SHAP certificate')
    test=final_metrics(final)
    evidence={t:metric(v2['targets'][t],'selected') for t in TARGETS}
    protocol=v2['protocol']; audit=v2['development_audit']
    status='FINAL EVALUATION PENDING' if test is None else 'FINAL HOLDOUT EVALUATED'
    story=[]

    # Page 1: implemented product, its defensible contribution and evidence status.
    story += [p('TRACK A  /  TECHNICAL REPORT','eyebrow'),
              p('Lumen<br/>Coronary Evidence Explorer','h1'),
              p('Connect each coronary prediction to named anatomy and exact model reasoning. Challenge the demonstration with the complete development cohort, including false positives, missed disease and incorrect flags that persist across five input profiles.'),
              box('<b>'+status+'</b><br/>'+('This edition reports development evidence. The frozen final holdout is not reported as an evaluated test.' if test is None else 'Development and final test evidence are reported separately. All claims remain limited to the evaluated source dataset.')),
              Spacer(1,12)]
    shot=Path(args.screenshot) if args.screenshot else None
    if shot and shot.exists():
        image=Image(str(shot)); ratio=image.imageHeight/image.imageWidth
        image.drawWidth=WIDTH;image.drawHeight=min(320,WIDTH*ratio)
        # Preserve the screenshot aspect ratio; scale both dimensions if capped.
        if WIDTH*ratio>320:image.drawWidth=320/ratio
        image.hAlign='LEFT';story += [image,Spacer(1,5),p('Figure 1. Actual running prototype. Generic BodyParts3D anatomy links named coronary targets to case inputs and explanations. The screenshot documents implemented interactions, not clinical validation.','caption')]
    elif cohort:
        story += [audit_overview(), p('Figure 1. Development audit design and its recorded counterexample. This is a static evidence diagram, not a browser screenshot. Every model view uses an excluding-fold model.','caption')]
    story += [table(['Clinical targets','Data partition','Deployment compute'],
                    [['CAD + LAD + LCX + RCA','242 development<br/>61 final holdout','CPU experiments + inference<br/>Portable browser runtime']],
                    [WIDTH/3]*3),Spacer(1,10),
              p('<b>Contribution.</b> A reproducible audit connects all 242 development records to their excluding-fold models, five-profile comparisons, generic named arteries and exact explanations. Outcome-aware filters expose failures beyond the eight introductory examples. Source-bound receipts support inspection; this is an engineering contribution, not a claim of a new diagnostic algorithm.'),
              p('Educational research prototype. Not validated for clinical use or a substitute for diagnostic imaging. Probabilities do not describe stenosis severity or patient-specific plaque locations.','small'),PageBreak()]

    # Page 2: data and leakage prevention.
    story += [p('01  /  DATA AND VALIDATION','eyebrow'),p('Keep outcomes out of the inputs','h2'),
              workflow(bool(test)),
              p('<b>Source and targets.</b> The UCI extension of Z-Alizadeh Sani contains 303 records [1]. Cath supplies the overall CAD label; LAD, LCX and RCA supply vessel status. All four angiography columns are excluded from every task, leaving 55 predictors. Source hashes and frozen row identities are saved.'),
              p('<b>Preprocessing.</b> Numeric median imputation and scaling, plus categorical imputation and one-hot encoding, are refitted within each training partition. Inference preserves the fitted values and reports unseen categories. Original source spelling is retained in the encoder.'),
              table(['Input group','Count','Operational availability meaning'],[
                  ['History','17','Demographics and recorded history indicators'],
                  ['Examination','14','Recorded symptoms and examination findings'],
                  ['ECG','7','Recorded ECG indicators'],
                  ['Laboratory','14','Laboratory measurements, source encodings retained'],
                  ['Echo','3','EF-TTE, Region RWMA and VHD'],
              ],[100,48,WIDTH-148]),Spacer(1,10),
              p('The five availability groups are an explicit experiment definition informed by the source categories. Laboratory and echo are split operationally; the dataset does not establish a temporal care pathway. Verified units are used only where supported by source evidence [1,2].','small'),
              p('<b>Nested selection (V2).</b> Five shared CAD-stratified outer folds evaluate the entire selection procedure. Three target-stratified inner folds select C (0.01, 0.1, 1, 10), unweighted/balanced logistic fitting, and optional sigmoid calibration by pooled inner log loss. Calibrated candidates use further cross-fitted training scores; outer validation records are excluded from fitting and calibration [4,5].'),
              p('<b>Operating rule.</b> The selected candidate maximizes inner out-of-fold F1 over thresholds 0.05-0.95 at 0.01 steps. Ties favor proximity to 0.5, then the higher point. Outer classification metrics use the threshold fitted without each validation record. AUC and Brier use probabilities, independent of this classification threshold [6].'),
              box(f'<b>Development audit:</b> {audit["missing_cells"]} missing cells; {audit["duplicate_input_rows"]} duplicated input rows; {audit["cad_vs_any_vessel_label_disagreements"]} CAD/vessel label discrepancy preserved. V2 followed inspection of V1 development results, so development evidence includes experiment-selection uncertainty.'),PageBreak()]

    # Page 3: all tasks plus visible operating-point tradeoff.
    story += [p('02  /  PREDICTIVE EVIDENCE','eyebrow'),p('Detection improves with a cost','h2'),
              p('V2 pooled development out-of-fold results, n=242. Each record is predicted by an excluding outer model. Intervals bootstrap fixed OOF predictions (1,000 resamples); they omit refitting and experiment-selection uncertainty.'),
              metric_table(evidence,True),Spacer(1,10),
              p('Figure 2. Lower fitted operating thresholds increase LCX/RCA recall while reducing precision. This is a classification tradeoff; vessel discrimination does not improve over the initial baseline.','caption'),
              tradeoff_chart(v1['targets'],v2['targets']),Spacer(1,7),
              table(['V2 selected rule','True positive','False negative','False positive','True negative'],
                    [[t,*[evidence[t]['confusion_matrix_tn_fp_fn_tp'][i] for i in [3,2,1,0]]] for t in ['LCX','RCA']],
                    [105]+[(WIDTH-105)/4]*4),Spacer(1,10),
              p('The initial fixed-0.5 V1 baseline had LCX/RCA recall 0.228/0.236 and precision 0.636/0.724. V2 raises recall to 0.815/0.809 while precision falls to 0.478/0.483. The additional false positives remain visible, rather than being hidden behind a higher F1.'),
              p('<b>Probability quality.</b> Brier and log loss are reported alongside ranking and classification metrics. A sigmoid step does not establish calibrated probabilities in a new population; Brier mixes reliability and discrimination, and the saved reliability bins are small [5].'),
              box('These are development results, not external validation or medical operating thresholds. The four independent models do not impose a coherent joint CAD/vessel distribution.'),PageBreak()]

    # Page 4: available-input comparisons and complete outcome-aware audit.
    story += [p('03  /  INPUT PROFILES AND COHORT AUDIT','eyebrow'),p('Agreement must survive a failure audit','h2')]
    if available:
        story += [p('Five cumulative input profiles are fitted separately under the same frozen development identities and outer folds. The full-input profile reuses V2. This evaluates model evidence with available groups; it does not estimate medical test utility, cost or causal benefit.'),
                  availability_chart(available),p('Figure 3. Development ROC-AUC by cumulative input profile. Each profile has its own nested fitting, calibration selection and threshold rule; groups are not merely nulled in the full-input model.','caption')]
    else:
        story += [box('Availability evaluation is pending. The planned comparison covers 17 history inputs, then examination (31), ECG (38), laboratory (52), and echo (55). No availability result is claimed in this edition.'),Spacer(1,12)]
    if cohort_counts:
        story += [p('All 242 records, including stable incorrect flags','h3'),
                  table(['Target','Five profiles agree / 242','Incorrect among agreeing','FP / FN'],
                        [[target, row['agreeing'], row['wrong'], f'{row["fp"]} / {row["fn"]}'] for target, row in cohort_counts.items()],
                        [53,153,187,WIDTH-393]),Spacer(1,8),
                  p('Each flag uses its model\'s already fitted research threshold. Agreement selects a subset; it does not improve a retained prediction. LCX remains wrong on 60/172 agreeing records, and RCA on 58/164. These overlapping models are not independent witnesses.','small'),
                  p('The audit filters by target, outcome, profile agreement, outer fold and a shared fixed/research decision rule. Every selected record opens the anatomy and exact score. Recorded outcomes define filters: this is descriptive development review, not a blind or prospective test.','small')]
    story += [p('Bounded model comparisons remain exploratory','h3'),
              p('V1 and V3 retained prior/tree baselines. A later 200-fit nested CatBoost CPU probe took 190.33s and 423MB peak RAM: LAD AUC improved from 0.814 to 0.829, while CAD/RCA weakened and LCX was unchanged. These mixed development results did not replace the frozen V2 procedure or reopen final evaluation.','small')]
    timings = [f'V1 {v1["runtime_seconds"]:.1f}s', f'V2 {v2["runtime_seconds"]:.1f}s']
    if v3: timings.append(f'V3 {v3["runtime_seconds"]:.1f}s')
    if available: timings.append(f'availability {available["runtime_seconds"]:.1f}s')
    story += [p('Measured elapsed time in the local CPU runs: '+', '.join(timings)+'. V2 timing includes bounded search, export checks, conditional bootstraps and artifact creation. No GPU was used.','small'),
              p('Model-family and input-profile decisions '+('were frozen before final holdout scoring. Final outcomes were not used to retune the submitted procedure.' if test else 'must be frozen before final holdout scoring. Choosing the best outer score per target and calling it untouched evaluation would overstate the evidence.'),'small'),PageBreak()]

    # Page 5: actual engineering and faithful score mapping.
    story += [p('04  /  ANATOMY AND INTEGRATION','eyebrow'),p('One mapping from score to vessel','h2'),
              architecture(),
              p('<b>Reference geometry.</b> Official BodyParts3D memberships define heart FMA7088, LAD FMA3862, LCX FMA3895 and RCA FMA50039 [3]. Source OBJ parts are merged, triangulated and transformed into selectable Three.js groups [7]. Provenance retains hashes, memberships and modifications.'),
              p('<b>Visual semantics.</b> The target selects matching geometry, probability and explanation. Overview, opposite view, mesh-bound focus and isolation complement rotate/zoom and the surface toggle. Isolation restores the chosen surface state. Probability colors the whole vessel; no patient geometry or lesion coordinates are inferred.'),
              p('Grouped interventional linear SHAP (log-odds)' if shap_check or cohort_shap else 'Exact explanation of the exported model','h3'),
              p('For encoded values z, training means mu, coefficients beta and intercept b:'),
              box('reference = b + sum(beta[j] * mu[j])<br/>contribution[j] = beta[j] * (z[j] - mu[j])<br/>score = reference + sum(contribution[j])<br/>probability = sigmoid(score)'),Spacer(1,9),
              p('Encoded terms are grouped into raw inputs; calibration slope/offset enter coefficients/intercept. The waterfall shows reference, six largest terms, residual and final score. Sigmoid applies at the endpoint; sigmoid(reference) is not mean predicted probability.'),
              p(('Actual SHAP LinearExplainer with an Independent masker verifies the decomposition [9] using all encoded training-fold rows. Masks break feature dependencies and may form invalid one-hot states. Terms are interventional model log-odds, not conditional explanations or percentage-point probability changes.' if shap_check or cohort_shap else 'These are exact centered log-odds terms, not conditional SHAP estimates or percentage-point probability changes.')),
              p('Correlation-aware explanations can assign different credit. Terms show model associations; input edits explore fitted-model sensitivity, not treatment effects or clinical interventions.'),
              p('Verification and interaction','h3'),
              p('The compact export matched all 4,840 saved development probabilities exactly. It retains eight introductory cases plus the complete development audit. Contributions are calculated lazily from the same 100 profile/target/fold models; labels never enter inference.','small'),
              p((f'The separate complete-cohort actual-SHAP certificate passed {cohort_shap["n_explanations_verified"]:,} explanations across {cohort_shap["n_models_verified"]} models; maximum grouped-term error {cohort_shap["max_grouped_shap_error"]:.2e} and reconstructed score error {cohort_shap["max_reconstruction_error"]:.2e}, tolerance 1e-12. Its Independent background excludes the record, the entire outer fold and every final holdout row. ' if cohort_shap else '')+'The original 160-explanation certificate remains scoped to the eight-case roster. These checks verify the specified decomposition, not clinical explanation utility.','small'),
              p('Audit selections open the anatomy, score waterfall and five-profile matrix. Outcome-aware selection is disclosed; label reveal is separate from inference. Edits disable matching outcome comparison; unlabelled inputs use frozen full-development models.','small')]
    if ai_review:
        story += [p('<b>Independent AI review, 11 October.</b> Five tasks completed; the sixth demonstrated rotation, zoom, target/score mapping and interpretation, with an unretained focus/isolation screenshot. Two P2 baseline defects were fixed: stale prior-case notice and false alarms described as misses. Subsequent Chromium checks confirmed both corrections. This is AI software review, not measured human comprehension or usability.','small')]
    story += [PageBreak()]

    # Page 6: dynamically supplied final evidence, limits, reproducibility and credits.
    story += [p('05  /  FINAL EVIDENCE AND REPRODUCIBILITY','eyebrow'),p('Evidence boundaries and release record','h2')]
    if test:
        story += [p(f'Final holdout: n={final["n_holdout"]}. The primary full-input procedure was frozen before scoring once. No holdout fitting, calibration, threshold or profile selection was performed.'),metric_table(test,True),Spacer(1,7)]
        metadata=final.get('protocol',{})
        counts='; '.join(f'{t} {final["targets"][t]["n_positive"]}/{final["targets"][t]["n_negative"]}' for t in TARGETS)
        thresholds=', '.join(f'{t} {final["targets"][t]["operating_threshold"]:.2f}' for t in TARGETS)
        story += [p('Positive/negative counts: '+counts+'. Fitted thresholds: '+thresholds+'. Conditional intervals use 1,000 fixed-prediction patient resamples; no refitting uncertainty.','small')]
        confusion=' '.join(f'<b>{t}:</b> '+', '.join(f'{test[t]["confusion_counts"][k]} {label}' for k,label in [('tp','TP'),('fn','FN'),('fp','FP'),('tn','TN')])+'.' for t in ['LCX','RCA'])
        story += [box(confusion),Spacer(1,7)]
    else:
        story += [box('<b>Final evaluation pending.</b> The 61-record final holdout has no reported predictions or scores in this edition. A single frozen-protocol test and its complete evidence must replace this status before the report is treated as final.'),Spacer(1,9)]
    story += [p('Limits','h3'),
              p('Small dataset; no external or prospective validation. '+('A bounded cohort search admitted no full-55-input source: public AngioCAD lacks the examination and ECG groups [10]. ' if external_compatibility else '')+'LCX/RCA have limited discrimination and a large false-positive cost. Intervals omit refitting uncertainty. Independent targets can disagree. Generic anatomy cannot locate plaque; edits lack outcome labels.','small'),
              p('Reproduce and verify','h3'),
              p('Run <font face="Courier">npm ci</font>, <font face="Courier">python3 server.py</font>; open <font face="Courier">http://127.0.0.1:8766/</font>. Python standard library or the static browser performs inference. Ordinary WebGL renders anatomy. <font face="Courier">docs/cohort-audit.md</font> gives audit and pinned CPU verification commands.','small')]
    if runtime:
        rates='/'.join(f'{rate:.1f}' for rate in runtime['rates'])
        durations='/'.join(f'{duration:g}' for duration in runtime['durations_seconds'])
        story += [p(f'<b>Measured local runtime, 11 October.</b> Saved pre-watchdog Chromium captures on this M5, {runtime["width"]} x {runtime["height"]}, DPR {runtime["dpr"]:g}; idle/action {durations}s: {rates} foreground render callbacks/s. {runtime["n_completed"]} completed actions: {runtime["dom_min"]:.1f}-{runtime["dom_max"]:.1f}ms to DOM update; longest callback interval {runtime["max_interval"]:.1f}ms. These narrow main-thread render-submission samples exclude GPU completion, physical-display latency, hosted speed, human usability and second-device evidence. Safari rendering has not passed.','small')]
    story += [
              p('Credits and AI assistance','h3'),
              p('UCI 411: Alizadehsani, R., Roshanzamir, M., &amp; Sani, Z. (2013), CC BY 4.0 [1]. BodyParts3D, © The Database Center for Life Science, CC Attribution 4.0 International [3]. Geometry was merged, triangulated, translated and rotated. Three.js is MIT licensed [7].','small'),
              p('OpenAI Codex assisted with research, code, experiments, debugging, AI review and documents. The human submitter owns verification and judging explanations; human review/signoff remain pending. AI assistance is declared here/README and must appear in Devpost Built With [8].','small'),
              p('Primary references','h3'),
              p('[1] UCI extension of Z-Alizadeh Sani. DOI: <link href="https://doi.org/10.24432/C5461K" color="#087e83">10.24432/C5461K</link>.<br/>'
                '[2] Alizadehsani et al. Laboratory and echocardiography features (2013). DOI: <link href="https://doi.org/10.5812/cardiovascmed.10888" color="#087e83">10.5812/cardiovascmed.10888</link>.<br/>'
                '[3] <link href="https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html" color="#087e83">BodyParts3D archive: license and source download</link>.<br/>'
                '[4] <link href="https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html" color="#087e83">scikit-learn: nested cross-validation</link>.<br/>'
                '[5] <link href="https://scikit-learn.org/stable/modules/calibration.html" color="#087e83">scikit-learn: probability calibration</link>.<br/>'
                '[6] <link href="https://scikit-learn.org/stable/modules/classification_threshold.html" color="#087e83">scikit-learn: tuning the decision threshold</link>.<br/>'
                '[7] <link href="https://threejs.org/docs/" color="#087e83">Three.js documentation</link>.<br/>'
                '[8] <link href="https://multimodal-ai-hackathon-2026-7.devpost.com/rules" color="#087e83">Multimodal AI Hackathon 2026: rules</link>; supplied Track A and submission guidelines.<br/>'
                '[9] <link href="https://shap.readthedocs.io/en/latest/generated/shap.LinearExplainer.html" color="#087e83">SHAP LinearExplainer: interventional linear attribution</link>.'
                +('<br/>[10] AngioCAD primary paper: <link href="https://doi.org/10.1016/j.cmpb.2026.109368" color="#087e83">10.1016/j.cmpb.2026.109368</link>; <link href="https://zenodo.org/records/15826856" color="#087e83">official feature workbook</link>.' if external_compatibility else ''),'small')]

    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    def decorate(canvas,doc):
        canvas.saveState()
        canvas.setFillColor(TEAL);canvas.rect(0,PAGE_H-7,PAGE_W,7,fill=1,stroke=0)
        canvas.setFont(BOLD,8);canvas.setFillColor(NAVY);canvas.drawString(44,PAGE_H-29,'LUMEN / CORONARY EVIDENCE EXPLORER')
        canvas.setFont(FONT,7.4);canvas.setFillColor(ORANGE if test is None else TEAL);canvas.drawRightString(PAGE_W-44,PAGE_H-29,status)
        canvas.setStrokeColor(colors.HexColor('#d9e2e7'));canvas.line(44,43,PAGE_W-44,43)
        canvas.setFont(FONT,7.5);canvas.setFillColor(GRAY);canvas.drawString(44,29,'Educational research prototype | '+date.today().isoformat())
        canvas.drawRightString(PAGE_W-44,29,str(doc.page)+' / 6')
        canvas.restoreState()
    doc=SimpleDocTemplate(str(out),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=56,bottomMargin=59,
                          title='Lumen - Coronary Evidence Explorer',author='Lumen project',subject='Track A technical report; saved development and final evaluation evidence')
    doc.build(story,onFirstPage=decorate,onLaterPages=decorate)
    reader=PdfReader(str(out))
    if len(reader.pages)!=6:
        raise ValueError(f'Report overflow: expected 6 pages, got {len(reader.pages)}. Fix layout before delivery.')
    texts=[page.extract_text() or '' for page in reader.pages]
    if any('\ufffd' in text for text in texts):raise ValueError('Replacement glyph in report text')
    if test is None and not all(status in text for text in texts):raise ValueError('Draft final-evaluation status missing')
    source_paths = {key: Path(getattr(args,key)) for key in ['v1','v2','v3','availability','final','shap','cohort','cohort_shap']
                    if getattr(args,key,None) and Path(getattr(args,key)).exists()}
    source_paths['report_source'] = Path(__file__).resolve()
    catboost_path=ROOT/'training/catboost-probe-2026-10-10/benchmark.json'
    if catboost_path.exists():source_paths['later_catboost_development_probe']=catboost_path
    for key in ['ai_review','external_compatibility','post_fix_check']:
        path=getattr(args,key,None)
        if path and Path(path).exists():source_paths[key]=Path(path)
    for index,path in enumerate(runtime_paths):source_paths[f'runtime_capture_{index+1}']=Path(path)
    manifest = {'pages': len(reader.pages), 'report_sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
                'report_bytes': out.stat().st_size, 'n_audit_development_records': 242 if cohort else 0,
                'n_introductory_cases': 8, 'n_final_holdout_records': final['n_holdout'] if final else 0,
                'final_holdout_rescored': False, 'models_refitted': False,
                'ai_software_review_included': bool(ai_review), 'human_usability_measured': False,
                'runtime_captures_included': len(runtime_paths), 'runtime_scope': 'dated pre-watchdog software samples' if runtime else None,
                'external_full_model_validation_included': False, 'second_physical_device_tested': False,
                'sources': {key: {'path': str(path.resolve()), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                            for key,path in source_paths.items()}, 'visual_review': 'pending'}
    manifest_path=Path(args.manifest) if args.manifest else out.with_name('lumen-report-manifest.json')
    manifest_path.parent.mkdir(parents=True,exist_ok=True)
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'output':str(out.resolve()),'pages':len(reader.pages),'final_evaluation_included':bool(test),
                      'availability_included':bool(available),'v2_development_records':protocol['n_development']},indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--v1',type=Path,default=existing(ROOT/'training/results/benchmark.json',RESEARCH/'results/benchmark.json'))
    ap.add_argument('--v2',type=Path,default=existing(ROOT/'training/results-v2/benchmark.json',RESEARCH/'results-v2/benchmark.json'))
    ap.add_argument('--v3',type=Path,default=existing(ROOT/'training/results-v3/benchmark.json',RESEARCH/'results-v3/benchmark.json'))
    ap.add_argument('--availability',type=Path,default=existing(ROOT/'training/results-availability/benchmark.json',RESEARCH/'results-availability/benchmark.json'))
    ap.add_argument('--final',type=Path,default=existing(ROOT/'artifacts/final_evaluation.json',ROOT/'training/results-final-evaluation/final_evaluation.json'))
    ap.add_argument('--shap',type=Path,default=existing(ROOT/'training/results-availability/shap-verification.json',RESEARCH/'results-availability/shap-verification.json'))
    ap.add_argument('--cohort',type=Path,default=ROOT/'artifacts/cohort-audit.json')
    ap.add_argument('--cohort-shap',type=Path,default=ROOT/'public/assets/cohort-audit-verification.json')
    ap.add_argument('--ai-review',type=Path,default=ROOT/'research/independent-ai-review-2026-10-11/ai-review.json')
    ap.add_argument('--runtime',type=Path,nargs='*',default=[ROOT/'research/runtime-2026-10-11/chromium-idle.json',ROOT/'research/runtime-2026-10-11/chromium-actions.json'])
    ap.add_argument('--external-compatibility',type=Path,default=ROOT/'research/lumen-external-cohort-2026-10-11/angiocad-compatibility-audit.json')
    ap.add_argument('--post-fix-check',type=Path,default=ROOT/'research/runtime-2026-10-11/review-fix-ui-receipt.json',help='Receipt binding separately verified current UI corrections')
    ap.add_argument('--screenshot',type=Path,default=None,help='Optional actual browser screenshot; no screenshot is invented by this build')
    ap.add_argument('--output',type=Path,default=ROOT/'output/pdf/lumen-report.pdf')
    ap.add_argument('--manifest',type=Path,default=None,help='Optional report manifest destination')
    build(ap.parse_args())
