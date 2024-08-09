from intervaltree import IntervalTree

from rtfs.utils import TextRange

epsilon = 0.1


class Scope:
    def __init__(self, range: TextRange, node_id: str):
        self.start, self.end = range.line_range()

        self.node_id = node_id


class IntervalGraph:
    def __init__(self, range: TextRange, root_id: str):
        self._interval_tree = IntervalTree()
        self.add_scope(range, root_id)

    def add_scope(self, range: TextRange, node_id: str):
        scope = Scope(range, node_id)
        start, end = range.line_range()
        if start == end:
            end += epsilon

        self._interval_tree[start:end] = scope
        return scope

    def all_intervals(self):
        return self._interval_tree.items()

    def contains(self, range: TextRange, overlap=False):
        start, end = range.line_range()
        intervals = self.all_intervals()

        # need to do this or else it throws an error if start == end
        # its fine, since min(end-start) = 1 anyways
        if start == end:
            end += epsilon

        if overlap:
            intervals = self._interval_tree[start:end]
            # print("Overlapping: ", intervals)
            if not intervals:
                return None
        else:
            intervals = [
                interval
                for interval in self._interval_tree[start:end]
                if interval.begin <= start and end <= interval.end
            ]

        if not intervals:
            return None

        smallest_scope = min(intervals, key=lambda x: x.end - x.begin)
        return smallest_scope.data.node_id
