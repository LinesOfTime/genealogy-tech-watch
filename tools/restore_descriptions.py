"""Restore missing purpose descriptions from retained editorial material only."""
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import re

from apply_changes import encoded, sync_payloads, write_plan, digest_bytes

PREFIX = 'По редакционным материалам (без независимой проверки): '
VERSION = 'editorial-purpose-v1'
UNCERTAINTY = re.compile(r'кандидат\w*|возмож\w*|может\b|могут\b|потенциальн\w*|вероятн\w*|предполож\w*', re.I)


def meaningful(value):
    return isinstance(value, str) and bool(value.strip()) and not re.search(
        r'не установлен|не определ[её]н|не указан', value, re.I)


def select_purpose(research):
    summary = research.get('editorial_summary')
    if meaningful(summary):
        return summary.strip(), 'editorial_summary', summary, []
    excerpt = research.get('guide_excerpt', '')
    lines = [line for line in excerpt.splitlines() if re.match(r'^\s*Назначение:', line)] if isinstance(excerpt, str) else []
    if len(lines) > 1:
        return None, None, None, ['Несколько строк «Назначение:»; требуется ручной выбор']
    if lines:
        value = lines[0].split(':', 1)[1].strip()
        if meaningful(value):
            return value, 'guide_excerpt', lines[0], []
    return None, None, None, ['В editorial_summary и строке «Назначение:» нет содержательного описания']


def restore(catalog, research):
    result = copy.deepcopy(catalog)
    rows = []
    for card in result:
        old_meta = card.get('description_provenance')
        targeted = isinstance(card.get('description'), str) and 'не установлен' in card['description'].lower()
        if not targeted and not (isinstance(old_meta, dict) and old_meta.get('migration') == VERSION):
            continue
        key = card['name'].lower()
        r = research.get(key, {})
        text, field, raw, reasons = select_purpose(r)
        markers = list(dict.fromkeys(m.group(0) for m in UNCERTAINTY.finditer(text or '')))
        limitation_lines = [line for line in r.get('guide_excerpt', '').splitlines() if line.startswith('Ограничения:')]
        review_reasons = reasons + ['Редакционный пересказ не сверялся с первоисточником в этом исправлении']
        if markers:
            review_reasons.append('Сохранена гипотетическая формулировка: ' + ', '.join(markers))
        provisional = bool(markers)
        original = old_meta['original_description'] if old_meta else card['description']
        source = None
        if text:
            source = dict(file='docs/research.json', key=key, field=field,
                          original_text=raw, sha256=hashlib.sha256(r[field].encode('utf-8')).hexdigest())
            new_description = PREFIX + text
            if old_meta and card['description'] != new_description:
                raise ValueError('Restored description was edited; manual review required: ' + key)
            meta = dict(migration=VERSION, original_description=original,
                        interpretation='Описание назначения; тип проекта не выводился из назначения',
                        evidence_status='editorial_only_not_independently_verified',
                        source=source, uncertainty_markers=markers,
                        additional_verification_required=True)
            if old_meta and old_meta != meta:
                raise ValueError('Existing provenance differs; manual review required: ' + key)
            card['description'] = new_description
            card['description_provenance'] = meta
        elif old_meta:
            raise ValueError('Restored description lost its source: ' + key)
        rows.append(dict(name=card['name'], url=card.get('url'), original_description=original,
                         description=card['description'], restored=bool(text),
                         result='restored_provisional' if text and provisional else 'restored_editorial' if text else 'unresolved',
                         source=source, uncertainty_markers=markers,
                         additional_verification_required=True, review_reasons=review_reasons,
                         source_limitations=limitation_lines,
                         project_type_preserved=r.get('project_type')))
    report = dict(scope='Only descriptions containing «Не установлен», or records restored by this migration',
                  independent_research_performed=False, summary=dict(total=len(rows),
                    restored=sum(row['restored'] for row in rows),
                    unresolved=sum(not row['restored'] for row in rows),
                    provisional=sum(row['result']=='restored_provisional' for row in rows),
                    requiring_additional_verification=len(rows),
                    sources=dict(Counter(row['source']['field'] for row in rows if row['source']))),records=rows)
    return result, report


def markdown(report):
    s=report['summary']
    lines=['# Восстановление описаний назначения', '',
           f"Проверено: {s['total']}. Восстановлено: {s['restored']}; осталось неопределённым: {s['unresolved']}. "
           f"С оговорками: {s['provisional']}. Все {s['requiring_additional_verification']} требуют дальнейшей проверки первоисточников.", '',
           'Использованы только существующие редакционные материалы. Это восстановление назначения, '
           'а не независимое подтверждение функций. Тип проекта, лицензии, приоритеты, исследования и дайджест не изменены.', '',
           'Порядок: содержательный editorial_summary, затем единственная строка «Назначение:» '
           'из guide_excerpt. Заглушки и несколько строк не используются. Исходное описание, '
           'поле-источник, исходный текст и SHA-256 полного поля сохранены в description_provenance.', '',
           'Кандидат / возможно / может / потенциально / вероятно сохраняются дословно. '
           'Даже восстановленные описания не означают, что назначение установлено по первоисточнику.', '']
    for row in report['records']:
        lines += ['## '+row['name'], '', '**Результат:** '+row['result'], '',
                  '**Прежнее описание:** '+row['original_description'], '',
                  '**Описание:** '+row['description'], '',
                  '**Источник:** '+(f"docs/research.json → {row['source']['key']} → {row['source']['field']}" if row['source'] else 'Содержательный источник не найден'), '',
                  '**Проверить:** '+'; '.join(row['review_reasons']), '']
        if row['source_limitations']:
            lines += ['**Ограничения исходного текста:** '+' '.join(row['source_limitations']), '']
    return '\n'.join(lines).rstrip()+'\n'


def plan(root):
    root=Path(root)
    catalog=json.loads((root/'catalog.json').read_text(encoding='utf-8'))
    research=json.loads((root/'docs/research.json').read_text(encoding='utf-8'))
    updated,report=restore(catalog,research)
    # Only the requested catalogue copies and seed; digest remains byte-for-byte untouched.
    synced=sync_payloads(root,catalog=updated)
    files={n:synced[n] for n in ('catalog.json','docs/catalog.json','docs/index.html')}
    files['reports/description-restoration.json']=encoded(report)
    files['reports/description-restoration.md']=markdown(report).encode('utf-8')
    before={n:(root/n).read_bytes() if (root/n).exists() else None for n in files}
    files={n:b for n,b in files.items() if b!=before[n]}
    manifest={n:[digest_bytes(before[n]) if before[n] is not None else None,digest_bytes(b)] for n,b in sorted(files.items())}
    return dict(files=files,before=before,plan_hash=digest_bytes(encoded(manifest))),report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--expect-plan')
    args=parser.parse_args()
    proposal,report=plan(args.root)
    if args.write:
        write_plan(args.root,proposal,args.expect_plan)
    print(json.dumps(dict(summary=report['summary'],files=list(proposal['files']),plan_hash=proposal['plan_hash']),ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
