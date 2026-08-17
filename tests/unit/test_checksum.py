import hashlib
from app.package.checksum import build_checksums, sha256_bytes


def test_sha256_bytes() -> None:
    content = b"deepseek-geo"

    expected = hashlib.sha256(content).hexdigest()
    assert sha256_bytes(content) == expected


def test_build_checksums() -> None:
    files = {
        'manifest.json': b'{"a":1}',
        'tasks.jsonl': b'{"task_id":"Q001}\n'
    }

    result = build_checksums(files)

    assert result["manifest.json"] == hashlib.sha256(
        files['manifest.json']
    ).hexdigest()

    assert result["tasks.jsonl"] == hashlib.sha256(
        files['tasks.jsonl']
    ).hexdigest()
