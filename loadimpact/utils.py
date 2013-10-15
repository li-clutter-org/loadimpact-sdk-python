# coding=utf-8

__all__ = ['UTC']

from datetime import timedelta, tzinfo


_ZERO = timedelta(0)


def is_dict_different(d1, d2, epsilon=0.00000000001):
    s1 = set(d1.keys())
    s2 = set(d2.keys())
    intersect = s1.intersection(s2)
    added = s1 - intersect
    removed = s2 - intersect
    changed = []
    for o in intersect:
        if isinstance(s2, float) and abs(s2[o] - s1[o]) > epsilon:
            changed.append(o)
        elif s2[o] != s1[o]:
            changed.append(o)
    return (0 < len(added) or 0 < len(removed) or 0 < len(set(changed)))


class UTC(tzinfo):
    def utcoffset(self, dt):
        return _ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return _ZERO
