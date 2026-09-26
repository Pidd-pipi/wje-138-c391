"""序列化器共享小工具。"""
import re


def camel_to_snake(name):
    """planDepartAt -> plan_depart_at；snake_case 原样返回。"""
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
