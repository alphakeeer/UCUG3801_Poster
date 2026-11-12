"""Archive registered education sources without changing the existing research library."""

import concurrent.futures
import csv
import hashlib
import json
import re
import subprocess
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

from collect_research import ROOT, USER_AGENT, download, extract_pdf, inspect_html

LIBRARY = ROOT / '03_背景/教育专题'
RAW = LIBRARY / '原始文件'
TEXT = LIBRARY / '正文'


def fetch_bytes(source):
    if source.get('existing_file'):
        path = ROOT / source['existing_file']
        return path.read_bytes(), source['url'], 'existing_repository_file'
    if source.get('large_file'):
        destination = RAW / f"{source['source_id']}.download"
        result = subprocess.run([
            'curl', '--location', '--fail', '--silent', '--show-error',
            '--connect-timeout', '15', '--max-time', '180', '--user-agent', USER_AGENT,
            '--output', str(destination), '--write-out', '%{url_effective}', source['url'],
        ], capture_output=True, text=True, timeout=190)
        if result.returncode:
            destination.unlink(missing_ok=True)
            raise RuntimeError(result.stderr.strip())
        data = destination.read_bytes()
        destination.unlink()
        return data, result.stdout.strip(), 'curl_large_file'
    return download(source['url'])


def acquire(source):
    record = dict(source)
    record.update(status='failed', research_date='2026-11-10',
                  checked_at_utc=datetime.now(timezone.utc).isoformat())
    try:
        data, final_url, method = fetch_bytes(source)
        requested_suffix = Path(urllib.parse.urlparse(final_url).path).suffix.lower()
        if source.get('format') == 'json':
            suffix = '.json'
        elif data.startswith(b'%PDF'):
            suffix = '.pdf'
        elif requested_suffix in ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.json', '.js']:
            suffix = requested_suffix
        else:
            suffix = '.html'
        if suffix == '.pdf' and not data.startswith(b'%PDF'):
            raise ValueError('PDF address returned a non-PDF response')
        if suffix in ['.jpg', '.jpeg', '.png']:
            from PIL import Image
            import io
            with Image.open(io.BytesIO(data)) as preview:
                record['image_dimensions'] = list(preview.size)
                preview.verify()
        title = re.sub(r'[^\w\u4e00-\u9fff.-]', '_', source['title'])[:65]
        path = RAW / f"{source['source_id']}_{title}{suffix}"
        if source.get('existing_file'):
            path = ROOT / source['existing_file']
        text, metadata = '', {'text_status': 'binary_original'}
        if suffix == '.html':
            text, metadata = inspect_html(data, final_url)
            metadata['text_status'] = 'ok'
        if not source.get('existing_file'):
            path.write_bytes(data)
        if suffix == '.pdf':
            text, metadata = extract_pdf(path)
        if suffix in ['.js', '.json']:
            text = data.decode('utf-8-sig')
            if suffix == '.json':
                json.loads(text)
            metadata['text_status'] = 'ok'
        text_path = TEXT / f"{source['source_id']}.txt"
        if text:
            prefix = (f"来源 {source['source_id']} {source['title']}\n"
                      f"原网址 {source['url']}\n研究日期 2026-11-10\n\n")
            text_path.write_text(prefix + text + '\n')
        record.update(metadata)
        record.update(status='reused' if source.get('existing_file') else 'downloaded',
                      acquisition=method, final_url=final_url,
                      local_file=str(path.relative_to(ROOT)),
                      text_file=str(text_path.relative_to(ROOT)) if text else '',
                      bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                      extracted_characters=len(text))
    except Exception as error:
        record['error'] = str(error)
    print(record['source_id'], record['status'], record.get('bytes',0), flush=True)
    return record


def save(records):
    records = sorted(records, key=lambda record: record['source_id'])
    (LIBRARY / '下载清单.json').write_text(json.dumps(records, ensure_ascii=False, indent=2)+'\n')
    columns = ['source_id','title','kind','scope','status','document_date','web_publication_date',
               'local_file','text_file','page_count','text_status','bytes','sha256','url',
               'checked_at_utc','scope_note','error']
    with (LIBRARY / '下载清单.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        writer = csv.DictWriter(handle,fieldnames=columns,extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)


def main():
    RAW.mkdir(parents=True,exist_ok=True)
    TEXT.mkdir(parents=True,exist_ok=True)
    sources = json.loads((LIBRARY / '来源清单.json').read_text())
    path = LIBRARY / '下载清单.json'
    previous = json.loads(path.read_text()) if path.exists() else []
    by_id = {record['source_id']:record for record in previous}
    results, pending = [], []
    for source in sources:
        old = by_id.get(source['source_id'])
        path = ROOT / old.get('local_file','missing') if old else None
        if old and old['status']!='failed' and old['url']==source['url'] and path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==old['sha256']:
            results.append({**old,**source})
        elif old and old['status']=='failed' and source.get('skip_retry'):
            results.append(old)
        else:
            pending.append(source)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(acquire, source) for source in pending]
        for job in concurrent.futures.as_completed(jobs):
            record = job.result()
            results.append(record)
            with (LIBRARY / '下载尝试.jsonl').open('a') as handle:
                handle.write(json.dumps(record,ensure_ascii=False)+'\n')
            save(results)
    save(results)
    print('Acquired',sum(record['status']!='failed' for record in results),'of',len(results),flush=True)


if __name__ == '__main__':
    main()
