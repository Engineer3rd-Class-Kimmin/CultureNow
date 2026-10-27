"""Verify evidence for an AI-authored design review, not a product execution benchmark."""
import hashlib,json,platform,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def main():
    cases=json.loads((HERE/'cases.json').read_text(encoding='utf-8'))
    reviewed=[]
    for c in cases:
        evidence=(ROOT/c['evidence_path']).read_text(encoding='utf-8')
        found=c['evidence_quote'] in evidence
        line=evidence[:evidence.index(c['evidence_quote'])].count('\n')+1 if found else None
        reviewed.append({**c,'evidence_found':found,'evidence_line':line})
    survey=[]
    for count,expected in [(20,74.1),(20,74.1),(19,70.4),(22,81.5)]:
        actual=round(count/27*100,1)
        survey.append(dict(count=count,denominator=27,expected_percent=expected,recomputed_percent=actual,status='PASS' if actual==expected else 'FAIL'))
    report=dict(scope='AI design review + survey arithmetic; no implemented engine, API benchmark, user experiment, or independent expert review',executed_at=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['docs/ARCHITECTURE.md','docs/VALIDATION.md','evaluation/design-v1/cases.json','evaluation/design-v1/run.py']},design_counts={v:sum(c['verdict']==v for c in reviewed) for v in ('SUPPORTED','PARTIAL','GAP')},evidence_verified=sum(c['evidence_found'] for c in reviewed),cases=reviewed,survey_arithmetic=survey)
    (HERE/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    lines=['# 기획 시나리오 평가 결과','',f"18개 설계 시나리오: {report['design_counts']}",'',
      '실행한 제품은 없다. Codex가 각 입력 상황과 기대 처리를 설계 문서에 대조하여 SUPPORTED(명시), PARTIAL(일부 명시), GAP(규칙 누락)으로 판정했다. 자동 실행기는 근거 인용의 존재와 설문 비율 산술만 다시 확인한다. 이 결과를 엔진 정확도나 실제 사용자 검증으로 해석할 수 없다.','',
      '| ID | 상황 | 설계 판정 | 근거 | 이유 |','|---|---|---|---|---|']
    for c in reviewed:lines.append(f"| {c['id']} | {c['title']} | {c['verdict']} | [문서 {c['evidence_line']}행](../../{c['evidence_path']}#L{c['evidence_line']}) | {c['reason']} |")
    lines+=['','설문 집계 산술: 20/27=74.1%, 20/27=74.1%, 19/27=70.4%, 22/27=81.5% (4/4 일치). 개별 응답 원자료를 재조사하거나 응답의 진실성을 확인한 것은 아니다.','',
      '우선 보완할 설계는 체류 완료 시각, 자정 경계, 왕복 조건, 출처 충돌, 데이터 유효기간, 동률 기준이다. 이 평가로 해당 기능을 구현했다고 주장하지 않는다.','',
      '재현: 저장소 루트에서 `python evaluation/design-v1/run.py`. Python 표준 라이브러리만 필요하다. 근거 인용이 사라지거나 산술이 틀리면 종료 코드 1. 종료 코드 0은 검토 근거 재확인 성공이며 제품 성능 합격을 뜻하지 않는다.','',
      '평가셋·설계 판정·실행기: Codex(ai-assisted). 기존 설계 문서를 본 후 작성한 개발 검토이며 독립 블라인드 평가가 아니다. 사람 검토는 대기 중이다. 판정 변경 시 이유와 문서 버전을 함께 남겨야 한다.']
    (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(design_counts=report['design_counts'],evidence_verified=report['evidence_verified'],survey_passed=sum(c['status']=='PASS' for c in survey))))
    return int(any(not c['evidence_found'] for c in reviewed) or any(c['status']!='PASS' for c in survey))
if __name__=='__main__':sys.exit(main())
