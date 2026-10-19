"""Copy and verify canonical images; remove old copies only with --cleanup.

The audit and byte-for-byte backups live outside the published datasets.
Only image references may change in JSONL records.
"""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / 'workspace/reports/image_storage_migration'
REPORT = AUDIT / 'report.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)
    elif isinstance(value, dict):
        for child in value.values():
            yield from strings(child)


def refs(record):
    result = list(record.get('question', {}).get('images', []))
    for value in strings(record):
        result.extend(re.findall(r'!\[[^\]]*\]\(([^)]+)\)', value))
    return result


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def rewritten(value, replacements):
    if isinstance(value, str):
        for old, new in sorted(replacements.items(), key=lambda pair: -len(pair[0])):
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [rewritten(x, replacements) for x in value]
    if isinstance(value, dict):
        return {k: rewritten(v, replacements) for k, v in value.items()}
    return value


def write_report(report):
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def verify(report):
    paths = set()
    for item in report['images']:
        target = ROOT / item['new']
        assert target.is_file() and sha(target) == item['sha256'], item
        paths.add(target.resolve())
    assert len(paths) == 311
    for item in report['jsonl']:
        path = ROOT / item['path']
        original = rows(AUDIT / 'backup' / item['path'])
        actual = rows(path)
        assert rewritten(original, item['replacements']) == actual, item['path']
        assert len(original) == len(actual) == item['count']
        for record in actual:
            for ref in refs(record):
                assert ref.startswith('data/images/'), (record.get('id'), ref)
                assert (ROOT / ref).resolve() in paths, ref
    main = {r['id']: r for name in ('benchmark', 'training') for r in rows(ROOT / f'datasets/main/{name}.jsonl')}
    for folder in ('objective_70', 'subjective_50'):
        assert all(main[r['id']] == r for r in rows(ROOT / f'datasets/{folder}/questions.jsonl'))
    for item in report['archived_images']:
        assert sha(ROOT / item['archive']) == item['sha256']


def prepare():
    if REPORT.exists():
        raise FileExistsError('Migration audit already exists; use --verify or --cleanup')
    all_jsonl = sorted((ROOT / 'datasets').rglob('*.jsonl'))
    used = set()
    for path in all_jsonl:
        for record in rows(path):
            for ref in refs(record):
                candidates = (ROOT / ref, path.parent / ref)
                source = next((p.resolve() for p in candidates if p.is_file()), None)
                if source is None:
                    raise FileNotFoundError((path, ref))
                used.add(source)
    report = {'status': 'copying', 'images': [], 'archived_images': [], 'jsonl': [], 'changed_files': []}
    for source in sorted(used):
        rel = source.relative_to(ROOT).as_posix()
        if rel.startswith('data/images/questions/'):
            target = 'data/images/gaokao/' + rel.removeprefix('data/images/questions/')
        else:
            part = source.relative_to(ROOT / 'datasets').parts[0]
            assert part in ('kaoyan', 'MIT', 'U-MATH')
            target = f'data/images/{part}/{source.name}'
        report['images'].append({'old': rel, 'new': target, 'sha256': sha(source)})
    assert len(report['images']) == 311
    AUDIT.mkdir(parents=True)
    for item in report['images']:
        dest = ROOT / item['new']
        if dest.exists() and sha(dest) != item['sha256']:
            raise FileExistsError(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / item['old'], dest)
        assert sha(dest) == item['sha256']
    for source in sorted((ROOT / 'datasets/kaoyan/assets').rglob('*')):
        if source.is_file() and source.resolve() not in used:
            dest = ROOT / 'workspace/review/image_storage_unused/kaoyan' / source.name
            if dest.exists() and sha(dest) != sha(source):
                raise FileExistsError(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            report['archived_images'].append({'old': source.relative_to(ROOT).as_posix(),
                                              'archive': dest.relative_to(ROOT).as_posix(), 'sha256': sha(source)})
    assert len(report['archived_images']) == 13
    files = sorted(p for p in (ROOT / 'datasets').rglob('*') if p.is_file() and p.suffix in ('.json', '.jsonl', '.md', '.txt'))
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        replacements = {}
        for item in report['images']:
            replacements[item['old']] = item['new']
            source = ROOT / item['old']
            if source.is_relative_to(path.parent):
                replacements[source.relative_to(path.parent).as_posix()] = item['new']
        original = path.read_bytes()
        text = original.decode('utf-8-sig')
        new = rewritten(text, replacements)
        backup = AUDIT / 'backup' / relative
        if new != text or path.suffix == '.jsonl':
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(original)
        if path.suffix == '.jsonl':
            report['jsonl'].append({'path': relative, 'count': len(rows(path)), 'replacements': {
                a: b for a, b in replacements.items() if a in text}})
            assert rewritten(rows(path), replacements) == [json.loads(s) for s in new.splitlines() if s.strip()]
        if new != text:
            path.write_bytes(new.encode('utf-8'))
            report['changed_files'].append(relative)
    report['status'] = 'copied_and_references_updated'
    write_report(report)
    verify(report)
    print(json.dumps({'images_verified': 311, 'unused_archived': 13, 'jsonl_counts_unchanged': True,
                      'only_image_references_changed': True, 'old_images_retained': True}))


def cleanup(report):
    verify(report)
    allowed = [ROOT / 'data/images/questions', *[ROOT / f'datasets/{name}/assets' for name in ('kaoyan', 'MIT', 'U-MATH')]]
    expected = {item['old']: item['sha256'] for item in report['images'] + report['archived_images']}
    # Validate every final absolute path and its content before deleting anything.
    actual = [p.resolve() for folder in allowed for p in folder.rglob('*') if p.is_file()]
    for path in actual:
        assert any(path.is_relative_to(folder.resolve()) for folder in allowed)
        rel = path.relative_to(ROOT).as_posix()
        assert rel in expected and sha(path) == expected[rel], path
    for path in actual:
        path.unlink()
    for folder in allowed:
        for path in sorted(folder.rglob('*'), key=lambda p: len(p.parts), reverse=True):
            if path.is_dir():
                path.rmdir()
        if folder.exists():
            folder.rmdir()
    verify(report)
    report['status'] = 'completed'
    write_report(report)
    print('Completed: 311 images verified; 13 unused images archived; old image directories removed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cleanup', action='store_true')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.cleanup or args.verify:
        report = json.loads(REPORT.read_text(encoding='utf-8'))
        if args.cleanup:
            cleanup(report)
        else:
            verify(report)
            print('Migration verification passed.')
    else:
        prepare()
