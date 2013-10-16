# coding=utf-8

"""
Copyright 2013 Load Impact

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

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
        if isinstance(d2[o], float):
            if abs(d2[o] - d1[o]) > epsilon:
                changed.append(o)
        elif d2[o] != d1[o]:
            changed.append(o)
    return (0 < len(added) or 0 < len(removed) or 0 < len(set(changed)))


class UTC(tzinfo):
    def utcoffset(self, dt):
        return _ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return _ZERO
