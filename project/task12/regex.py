from typing import Callable, Dict, Optional

from pyformlang.finite_automaton import EpsilonNFA, Symbol
from pyformlang.regular_expression import Regex
from pyformlang.rsa import Box, RecursiveAutomaton


def minimize_nfa(func: Callable[..., EpsilonNFA]) -> Callable[..., EpsilonNFA]:
    """Decorator to minimize the resulting NFA of a function."""

    def wrapper(*args, **kwargs) -> EpsilonNFA:
        nfa = func(*args, **kwargs)
        return nfa.minimize()

    return wrapper


def nfa_from_char(char: str) -> EpsilonNFA:
    """Creates an NFA that recognizes a single character."""
    assert len(char) == 1, f"Expected a single character, got: '{char}'."
    return Regex(char).to_epsilon_nfa()


def nfa_from_var(var_name: str) -> EpsilonNFA:
    """Creates an NFA for a variable name treated as a regular expression."""
    return Regex(var_name.upper()).to_epsilon_nfa()


def create_empty_nfa() -> EpsilonNFA:
    """Creates an empty NFA that recognizes the empty set."""
    return Regex("$").to_epsilon_nfa()


@minimize_nfa
def intersect(nfa1: EpsilonNFA, nfa2: EpsilonNFA) -> EpsilonNFA:
    """Intersects two NFAs."""
    return nfa1.get_intersection(nfa2)


@minimize_nfa
def concatenate(nfa1: EpsilonNFA, nfa2: EpsilonNFA) -> EpsilonNFA:
    """Concatenates two NFAs."""
    return nfa1.concatenate(nfa2)


@minimize_nfa
def union(nfa1: EpsilonNFA, nfa2: EpsilonNFA) -> EpsilonNFA:
    """Unions two NFAs."""
    return nfa1.union(nfa2)


@minimize_nfa
def repeat(nfa: EpsilonNFA, times: int) -> EpsilonNFA:
    """Repeats an NFA a specific number of times."""
    if times == 0:
        return create_empty_nfa()

    result_nfa = nfa
    for _ in range(times - 1):
        result_nfa = concatenate(result_nfa, nfa)

    return result_nfa


@minimize_nfa
def kleene(nfa: EpsilonNFA) -> EpsilonNFA:
    """Applies the Kleene star operation to an NFA."""
    return nfa.kleene_star()


@minimize_nfa
def repeat_range(
    nfa: EpsilonNFA, left_border: int, right_border: Optional[int]
) -> EpsilonNFA:
    """Repeats an NFA within a specified range."""
    if left_border == 0 and right_border is None:  # Kleene star for ^ [0..]
        return kleene(nfa)

    if right_border is None:  # Repeat indefinitely from left_border
        return concatenate(repeat(nfa, left_border), kleene(nfa))

    if left_border == right_border:  # Exact repetition
        return repeat(nfa, left_border)

    result_nfa = repeat(nfa, left_border)
    for times in range(left_border + 1, right_border + 1):
        result_nfa = union(result_nfa, repeat(nfa, times))

    return result_nfa


@minimize_nfa
def group(nfa: EpsilonNFA) -> EpsilonNFA:
    """Groups an NFA within parentheses."""
    return Regex(f"({nfa.to_regex()})").to_epsilon_nfa()


START_TERMINAL_NAME = "START"


def build_rsm(nfa: EpsilonNFA, subs_dict: Dict[str, EpsilonNFA]) -> RecursiveAutomaton:
    """Builds a Recursive State Machine (RSM) from NFAs."""
    boxes = [
        Box(var_nfa, Symbol(var_name.upper()))
        for var_name, var_nfa in subs_dict.items()
    ]
    boxes.append(Box(nfa, Symbol(START_TERMINAL_NAME)))

    return RecursiveAutomaton(initial_label=Symbol(START_TERMINAL_NAME), boxes=boxes)
