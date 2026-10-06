"""PyPI mirror definitions.

SECURITY NOTE: none of these mirrors are used unless the user has explicitly
opted in via ``AppConfig.allow_mirror_fallback`` (off by default). The
official index almost always works; mirror fallback exists only for users on
networks where pypi.org is blocked or slow, and it is *their* choice to
extend trust to a third-party host, not something GrabIt should decide for
them silently. ``--trusted-host`` disables certificate hostname verification
for that host, which is precisely the kind of thing that should never happen
without the user's knowledge.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class Mirror:
    name: str
    index_url: Optional[str]     # None means "official PyPI, no -i flag needed"
    trusted_host: Optional[str] = None


PYPI_MIRRORS: List[Mirror] = [
    Mirror("Official PyPI", None, None),
    Mirror("Tsinghua TUNA", "https://pypi.tuna.tsinghua.edu.cn/simple", "pypi.tuna.tsinghua.edu.cn"),
    Mirror("Aliyun", "https://mirrors.aliyun.com/pypi/simple/", "mirrors.aliyun.com"),
    Mirror("Tencent Cloud", "https://mirrors.cloud.tencent.com/pypi/simple/", "mirrors.cloud.tencent.com"),
    Mirror("USTC", "https://pypi.mirrors.ustc.edu.cn/simple/", "pypi.mirrors.ustc.edu.cn"),
    Mirror("CTYun", "https://mirrors.ctyun.cn/pypi/simple/", "mirrors.ctyun.cn"),
    Mirror("BFSU", "https://mirrors.bfsu.edu.cn/pypi/simple/", "mirrors.bfsu.edu.cn"),
]
