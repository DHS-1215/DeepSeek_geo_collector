import hashlib


def sha256_bytes(content: bytes) -> str:
    """计算 bytes 内容的 SHA-256 十六进制摘要"""
    return hashlib.sha256(content).hexdigest()


def build_checksums(
        files: dict[str, bytes],
) -> dict[str, str]:
    """为 package数据文件生成 SHA-256."""

    return {
        filename: sha256_bytes(content)
        for filename, content in files.items()
    }