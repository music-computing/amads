"""
Generic finite graphs, with cycle enumeration and p-number classification.

This generalisation design follows Boland and Hughston (2026)
who use the same cycle-counting apparatus for several different chord graphs:
the tonnetz as a Levi graph (the title of Section 2),
and the rather different Archimedean tonnetz (see Section 5), among others.

Only the Euler tonnetz graph comes from crossing edges of a `Tonnetz`.
The Archimedean tonnetz graph is built directly from a transform that
involves 2-tone change across the twenty-four major and minor triads.
As Boland and Hughston note, the Archimedean has "girth" four, so it is not even a Levi graph.
This module holds the shared cycle-counting machinery used by both graphs,
independent of where their vertices and edges come from.

See module notes at `tonnetze/base.py`.

<small>**Author**: Mark Gotham</small>
"""

from typing import (
    Callable,
    Dict,
    FrozenSet,
    Hashable,
    Iterable,
    List,
    Set,
    Tuple,
)

__author__ = "Mark Gotham"


Vertex = Hashable


class CycleGraph:
    """
    A finite simple graph, with cycle enumeration.

    Parameters
    ----------
    vertices : Iterable[Vertex]
        The graph's vertices.
    adjacency : Dict[Vertex, FrozenSet[Vertex]]
        Maps each vertex to the set of vertices to which it is joined.
        Must be symmetric: i.e., `v in adjacency[w]` iff `w in adjacency[v]`.

    Examples
    --------
    A 4-cycle.
    0-1-2-3- (wrap back to 0).

    >>> adjacency = {
    ...     0: frozenset({1, 3}), 1: frozenset({0, 2}),
    ...     2: frozenset({1, 3}), 3: frozenset({0, 2}),
    ... }
    >>> graph = CycleGraph([0, 1, 2, 3], adjacency)
    >>> graph.girth
    4
    >>> len(graph.cycles_of_length(4))
    1
    """

    def __init__(
        self,
        vertices: Iterable[Vertex],
        adjacency: Dict[Vertex, FrozenSet[Vertex]],
    ):
        self.vertices: Tuple[Vertex, ...] = tuple(vertices)
        self._adjacency: Dict[Vertex, FrozenSet[Vertex]] = adjacency

    def degree(self, vertex: Vertex) -> int:
        """
        Returns the number of edges meeting the given `vertex`.
        """
        return len(self._adjacency[vertex])

    def is_simple(self) -> bool:
        """
        Checks that no vertex is its own neighbour.
        A finite simple graph also has no repeated edges by construction here,
        since each vertex's neighbours are a set.
        """
        return all(
            v not in neighbors for v, neighbors in self._adjacency.items()
        )

    def connected_components(self) -> Tuple[FrozenSet[Vertex], ...]:
        """
        Finds the graph's connected components.

        Examples
        --------
        >>> adjacency = {0: frozenset({1}), 1: frozenset({0}), 2: frozenset()}
        >>> graph = CycleGraph([0, 1, 2], adjacency)
        >>> sorted(graph.connected_components(), key=len)
        [frozenset({2}), frozenset({0, 1})]
        """
        unvisited: Set[Vertex] = set(self.vertices)
        components: List[FrozenSet[Vertex]] = []
        while unvisited:
            start = next(iter(unvisited))
            component: Set[Vertex] = {start}
            frontier = [start]
            while frontier:
                current = frontier.pop()
                for neighbor in self._adjacency[current]:
                    if neighbor not in component:
                        component.add(neighbor)
                        frontier.append(neighbor)
            components.append(frozenset(component))
            unvisited -= component
        return tuple(components)

    def cycles_of_length(self, length: int) -> Tuple[Tuple[Vertex, ...], ...]:
        """
        Finds every simple cycle of the given length.

        A simple cycle here is a closed walk of distinct vertices.
        This is given as a tuple
        starting from its lexicographically "smallest" vertex (by string form)
        and continuing in whichever direction gives the lexicographically smaller sequence,
        so that a cycle and its reverse are not counted twice.

        This is a brute-force search, suitable for the small, low-degree graphs of Boland and Hughston (2026).
        It is not intended for large or dense graphs.

        For several lengths at once,
        use `cycles_up_to_length` which shares the search across lengths and is much faster.
        """
        return self.cycles_up_to_length(length).get(length, ())

    def cycles_up_to_length(
        self, max_length: int
    ) -> Dict[int, Tuple[Tuple[Vertex, ...], ...]]:
        """
        Finds every simple cycle of every length from 3 up to `max_length`.

        This shares a single depth-first search across all the lengths requested.
        Rather than repeating the search once per length
        (as repeated calls to `cycles_of_length` would)
        this method checks for a closed cycle at every depth reached along the way.

        This matters because the search tree's cost is dominated by its deepest calls,
        so this is close to the cost of one call to `cycles_of_length(max_length)`,
        not the sum of many.
        """
        found: Dict[int, Set[Tuple[Vertex, ...]]] = {}
        for start in self.vertices:
            self._extend_cycles(start, (start,), max_length, found)
        return {
            length: tuple(sorted(cycles, key=str))
            for length, cycles in found.items()
        }

    def _extend_cycles(
        self,
        start: Vertex,
        path: Tuple[Vertex, ...],
        max_length: int,
        found: Dict[int, Set[Tuple[Vertex, ...]]],
    ) -> None:
        """
        Depth-first search extending `path`.
        This method records a closed cycle at every depth along the way at which
        `path` closes back to `start`, up to the limit set by `max_length`.

        Completed cycles are added to `found` in canonical form.
        """
        current = path[-1]
        if len(path) >= 3 and start in self._adjacency[current]:
            found.setdefault(len(path), set()).add(self._canonical(path))
        if len(path) == max_length:
            return
        for neighbor in self._adjacency[current]:
            if neighbor in path:
                continue
            self._extend_cycles(start, path + (neighbor,), max_length, found)

    @staticmethod
    def _canonical(cycle: Tuple[Vertex, ...]) -> Tuple[Vertex, ...]:
        """
        Rotates a cycle (and reverses if needed)
        so that equivalent cycles map to the same tuple,
        whatever their starting point or direction.
        """
        n = len(cycle)
        best = None
        for start in range(n):
            forward = tuple(cycle[(start + i) % n] for i in range(n))
            backward = tuple(reversed(forward))
            for candidate in (forward, backward):
                key = tuple(map(str, candidate))
                if best is None or key < tuple(map(str, best)):
                    best = candidate
        return best

    @property
    def girth(self) -> int:
        """
        Returns the length of the shortest cycle.

        Checks lengths 3, 4, 5, ..., up to the order of the graph.

        Bipartite subclasses override this to check only even lengths.
        """
        for length in range(3, len(self.vertices) + 1):
            if self.cycles_of_length(length):
                return length
        raise ValueError("No cycle found: the graph may be a forest.")

    @staticmethod
    def p_number(
        cycle: Tuple[Vertex, ...],
        is_parallel_edge: Callable[[Vertex, Vertex], bool],
    ) -> int:
        """
        Counts a cycle's P edges,
        following Boland and Hughston's p-number
        (see Section 4 and the Appendix).

        Parameters
        ----------
        cycle : Tuple[Vertex, ...]
            A cycle, as returned by `cycles_of_length` or `cycles_up_to_length`.
        is_parallel_edge : Callable[[Vertex, Vertex], bool]
            Classifies an edge between two adjacent vertices as a P (parallel) transform or not.
        """
        n = len(cycle)
        return sum(
            is_parallel_edge(cycle[i], cycle[(i + 1) % n]) for i in range(n)
        )

    def cycle_table(
        self,
        lengths: Iterable[int],
        is_parallel_edge: Callable[[Vertex, Vertex], bool],
    ) -> Dict[int, Dict[int, int]]:
        """
        Builds a cycle-count table, following Boland and Hughston's Appendix.

        For each cycle length, count the number of cycles of that length having each possible p-number.

        Parameters
        ----------
        lengths : Iterable[int]
            The cycle lengths to tabulate, such as `range(6, 13, 2)`.
        is_parallel_edge : Callable[[Vertex, Vertex], bool]
            As in `p_number`.

        Returns
        -------
        Dict[int, Dict[int, int]]
            Maps each cycle length to a mapping from p-number to count.
            This matches the Appendix table's rows and columns.
        """
        lengths = tuple(lengths)
        all_cycles = self.cycles_up_to_length(max(lengths))
        table: Dict[int, Dict[int, int]] = {}
        for length in lengths:
            counts: Dict[int, int] = {}
            for cycle in all_cycles.get(length, ()):
                p = self.p_number(cycle, is_parallel_edge)
                counts[p] = counts.get(p, 0) + 1
            table[length] = counts
        return table


class BipartiteGraph(CycleGraph):
    """
    A `CycleGraph` split into two parts,
    with every edge joining one part to the other.

    Parameters
    ----------
    vertices : Iterable[Vertex]
        As in `CycleGraph`.
    adjacency : Dict[Vertex, FrozenSet[Vertex]]
        As in `CycleGraph`.
    bipartition : Callable[[Vertex], bool]
        Splits the vertices into two parts.

    Attributes
    ----------
    part_true : FrozenSet[Vertex]
        The vertices for which `bipartition` is `True`.
    part_false : FrozenSet[Vertex]
        The vertices for which `bipartition` is `False`.

    Examples
    --------
    >>> adjacency = {
    ...     0: frozenset({1, 3}), 1: frozenset({0, 2}),
    ...     2: frozenset({1, 3}), 3: frozenset({0, 2}),
    ... }
    >>> graph = BipartiteGraph([0, 1, 2, 3], adjacency, lambda v: v % 2 == 0)
    >>> graph.is_bipartite()
    True
    >>> graph.is_regular_within_parts()
    True
    """

    def __init__(
        self,
        vertices: Iterable[Vertex],
        adjacency: Dict[Vertex, FrozenSet[Vertex]],
        bipartition: Callable[[Vertex], bool],
    ):
        super().__init__(vertices, adjacency)
        self.part_true: FrozenSet[Vertex] = frozenset(
            v for v in self.vertices if bipartition(v)
        )
        self.part_false: FrozenSet[Vertex] = frozenset(
            v for v in self.vertices if not bipartition(v)
        )

    def is_bipartite(self) -> bool:
        """
        Checks that every edge joins a vertex in `part_true` to one in `part_false`.
        """
        for vertex, neighbors in self._adjacency.items():
            same_part = (
                self.part_true if vertex in self.part_true else self.part_false
            )
            if neighbors & same_part:
                return False
        return True

    def is_regular_within_parts(self) -> bool:
        """
        Checks that every vertex within `part_true` has the same degree.
        and likewise for `part_false`.
        """
        true_degrees = {self.degree(v) for v in self.part_true}
        false_degrees = {self.degree(v) for v in self.part_false}
        return len(true_degrees) <= 1 and len(false_degrees) <= 1

    @property
    def girth(self) -> int:
        """
        Returns the length of the shortest cycle.

        A bipartite graph has only even cycles,
        so this checks lengths 4, 6, 8, ..., up to the order of the graph.
        """
        for length in range(4, len(self.vertices) + 1, 2):
            if self.cycles_of_length(length):
                return length
        raise ValueError("No cycle found: the graph may be a forest.")


if __name__ == "__main__":
    import doctest

    doctest.testmod()
