"""Verify evidence for an AI-authored design review, not a product execution benchmark."""
import hashlib,json,platform,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def evaluate_cases(cases, root):
    reviewed=[]
    for c in cases:
        evidence=(root/c['evidence_path']).read_text(encoding='utf-8')
        found=bool(c['evidence_quote'].strip()) and c['evidence_quote'] in evidence
        line=evidence[:evidence.index(c['evidence_quote'])].count('\n')+1 if found else None
        status='PASS' if c['verdict']=='SUPPORTED' and found else 'FAIL'
        reviewed.append({**c,'evidence_found':found,'evidence_line':line,'status':status})
    return reviewed

def main():
    cases=json.loads((HERE/'cases.json').read_text(encoding='utf-8'))
    baseline=json.loads((HERE/'baseline/cases.json').read_text(encoding='utf-8'))
    contract=lambda rows: [{k:c[k] for k in ['id','title','input','expected']} for c in rows]
    if contract(cases) != contract(baseline):
        raise RuntimeError('Original 18 scenario inputs and expected behavior must remain unchanged')
    if len({c['id'] for c in cases}) != len(cases):
        raise RuntimeError('Duplicate case IDs')
    reviewed=evaluate_cases(cases,ROOT)
    survey=[]
    for count,expected in [(20,74.1),(20,74.1),(19,70.4),(22,81.5)]:
        actual=round(count/27*100,1)
        survey.append(dict(count=count,denominator=27,expected_percent=expected,recomputed_percent=actual,status='PASS' if actual==expected else 'FAIL'))
    report=dict(scope='AI design review + survey arithmetic; no implemented engine, API benchmark, user experiment, or independent expert review',executed_at=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['docs/ARCHITECTURE.md','docs/VALIDATION.md','evaluation/design-v1/cases.json','evaluation/design-v1/run.py']},design_counts={v:sum(c['verdict']==v for c in reviewed) for v in ('SUPPORTED','PARTIAL','GAP')},evidence_verified=sum(c['evidence_found'] for c in reviewed),cases=reviewed,survey_arithmetic=survey)
    report.update(original_scenarios_unchanged=True,total=len(reviewed),passed=sum(c['status']=='PASS' for c in reviewed),failed=sum(c['status']=='FAIL' for c in reviewed))
    (HERE/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    lines=['# 기획 시나리오 평가 결과','',f"18개 설계 시나리오: {report['design_counts']}; PASS {report['passed']}, FAIL {report['failed']}",'',
      '기존 18개 입력과 기대 처리는 유지하고 아키텍처의 여섯 누락·부분 규칙을 보완한 뒤 Codex가 각 시나리오를 다시 대조했다. SUPPORTED는 설계에 명시되었다는 검토 판정이다. 자동 실행기는 해당 판정·근거 인용과 설문 집계 산술을 확인하며 PARTIAL·GAP·누락 인용이 하나라도 있으면 실패한다. 실제 제품은 실행하지 않았다. 이 결과를 엔진 정확도나 사용자 검증으로 해석할 수 없다.','',
      '| ID | 상황 | 설계 판정 | 근거 | 이유 |','|---|---|---|---|---|']
    for c in reviewed:lines.append(f"| {c['id']} | {c['title']} | {c['verdict']} | [문서 {c['evidence_line']}행](../../{c['evidence_path']}#L{c['evidence_line']}) | {c['reason']} |")
    lines+=['','설문 집계 산술: 20/27=74.1%, 20/27=74.1%, 19/27=70.4%, 22/27=81.5% (4/4 일치). 개별 응답 원자료를 재조사하거나 응답의 진실성을 확인한 것은 아니다.','',
      '체류 완료 시각, 자정 경계, 왕복 조건, 출처 충돌, 데이터 유효기간, 동률 기준을 구체적인 식·우선순위·예시로 문서에 추가했다. 유효기간과 동률 임계값은 새 설계 기본값이며 현장 실험으로 확인된 값이 아니다. 이 평가로 해당 기능을 구현했다고 주장하지 않는다.','',
      '이전 12개 명시·3개 부분·3개 누락의 판정과 결과는 [baseline](baseline/RESULTS.md)에 보존했다. 이전 실행기의 종료 코드 0은 인용·산술 확인만 의미했고 설계 전체 합격은 아니었다. 이번부터 모든 설계 판정이 SUPPORTED인지도 검사한다.','',
      '재현: 저장소 루트에서 `python evaluation/design-v1/run.py`. Python 표준 라이브러리만 필요하다. 부분·누락 판정, 인용 누락, 산술 오류 중 하나라도 있으면 종료 코드 1. 종료 코드 0은 기록된 설계 검토와 근거의 완결성 확인이며 제품 성능 합격이 아니다. `python -m unittest discover -s evaluation/design-v1 -p "test_*.py"`로 실패 검출도 확인한다.','',
      '평가셋·설계 판정·실행기: Codex(ai-assisted). 기존 설계 문서를 본 후 작성한 개발 검토이며 독립 블라인드 평가가 아니다. 사람 검토는 대기 중이다. 판정 변경 시 이유와 문서 버전을 함께 남겨야 한다.']
    (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(design_counts=report['design_counts'],evidence_verified=report['evidence_verified'],survey_passed=sum(c['status']=='PASS' for c in survey))))
    return int(report['failed'] > 0 or any(c['status']!='PASS' for c in survey))
if __name__=='__main__':sys.exit(main())
