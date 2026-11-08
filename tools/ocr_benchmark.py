"""Compute strict CER/WER from human-verified text files, without model inference."""
import argparse
import csv
import json
from pathlib import Path
import sys
import unicodedata

def distance(a, b):
    """Levenshtein distance in linear memory."""
    if len(a)<len(b): a,b=b,a
    prev=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        curr=[i]
        for j,y in enumerate(b,1):
            curr.append(min(curr[-1]+1,prev[j]+1,prev[j-1]+(x!=y)))
        prev=curr
    return prev[-1]

def score(reference,prediction):
    def clean(s):
        return unicodedata.normalize('NFC',s).replace('\r\n','\n').replace('\r','\n').removesuffix('\n')
    a,b=clean(reference),clean(prediction)
    return dict(ref_chars=len(a),char_errors=distance(a,b),
                ref_words=len(a.split()),word_errors=distance(a.split(),b.split()))

def safe_path(base,value):
    if not isinstance(value,str) or not value or Path(value).is_absolute():
        raise ValueError('Input path must be a nonempty relative path')
    root=base.resolve()
    path=(base/value).resolve()
    if not path.is_relative_to(root): raise ValueError('Input path escapes manifest directory')
    if not path.is_file(): raise ValueError('Input file not found: '+value)
    return path

def calculate(manifest_path):
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    if not isinstance(manifest,dict) or manifest.get('schema_version')!=1 or not isinstance(manifest.get('cases'),list) or not manifest['cases']:
        raise ValueError('Expected schema_version=1 and nonempty cases')
    seen,rows=set(),[]
    for e in manifest['cases']:
        if not isinstance(e,dict) or not all(k in e for k in ('id','reference','prediction')):
            raise ValueError('Each case needs id, reference and prediction')
        name=e['id']
        if not isinstance(name,str) or not name.strip() or name in seen:
            raise ValueError('Case IDs must be unique, nonempty strings')
        seen.add(name)
        ref=safe_path(manifest_path.parent,e['reference']).read_text(encoding='utf-8-sig')
        pred=safe_path(manifest_path.parent,e['prediction']).read_text(encoding='utf-8-sig')
        counts=score(ref,pred)
        if not counts['ref_chars'] or not counts['ref_words']:
            raise ValueError('Empty reference transcription: '+name)
        rows.append(dict(id=name,**counts,cer=counts['char_errors']/counts['ref_chars'],
                         wer=counts['word_errors']/counts['ref_words']))
    total={key:sum(r[key] for r in rows) for key in ('ref_chars','char_errors','ref_words','word_errors')}
    return dict(schema_version=1,method='NFC; CRLF to LF; remove one terminal LF; strict case and letters; whitespace-token WER',
                cases=rows,micro=dict(**total,cer=total['char_errors']/total['ref_chars'],
                                     wer=total['word_errors']/total['ref_words']))

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest',type=Path)
    parser.add_argument('--json',dest='json_output',type=Path)
    parser.add_argument('--csv',dest='csv_output',type=Path)
    args=parser.parse_args(argv)
    try:
        result=calculate(args.manifest)
        if args.json_output:
            args.json_output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if args.csv_output:
            with args.csv_output.open('w',encoding='utf-8',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=['id','ref_chars','char_errors','cer','ref_words','word_errors','wer'])
                writer.writeheader();writer.writerows(result['cases'])
        print(json.dumps(result['micro'],ensure_ascii=False,indent=2))
        return 0
    except (ValueError,OSError,UnicodeError) as exc:
        print('Benchmark error: '+str(exc),file=sys.stderr)
        return 1

if __name__=='__main__':
    raise SystemExit(main())
