import os
import re

# 8 位日期型数字：19xxxxxx / 20xxxxxx
_DATE_RE = re.compile(r'^(19|20)\d{6}$')
# 需要忽略的干扰词
_NOISE_TOKENS = ('water', 'diiodo', 'h2o', 'ch2i2')


def extract_core_id(filename):
    """
    提取文件名核心识别码：
      1. 有数字 → 取最长的连续数字（跳过 8 位日期）
      2. 无数字 → 取字母，去掉常见干扰词及尾部单独的 'i'
    """
    name = os.path.splitext(filename)[0].strip()
    nums = re.findall(r'\d+', name)
    if nums:
        candidates = [n for n in nums if not _DATE_RE.match(n)]
        if candidates:
            return max(candidates, key=len)
        return nums[-1]

    letters = re.findall(r'[a-zA-Z]+', name)
    pure = ''.join(letters).lower()
    for token in _NOISE_TOKENS:
        pure = pure.replace(token, '')
    pure = re.sub(r'i+$', '', pure)
    return pure.strip() or name.lower()