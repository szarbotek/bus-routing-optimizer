import copy
import math
import random


def map_field(blocks: list) -> list[int]:
    """Flattens a hierarchical structure of blocks and gates into a 1D signal vector."""
    return [sig for b in blocks for g in b for sig in g]


def valid_cuts_fast(lvl: list[int], field: list[int]) -> int:
    """Calculates the total number of wire crossings in O(N * L) time using indexed arrays."""
    max_sig = max(lvl) + 1

    lvl_rank = [0] * max_sig
    for rank, sig in enumerate(lvl):
        lvl_rank[sig] = rank

    last_pos = [-1] * max_sig
    for idx, sig in enumerate(field):
        last_pos[sig] = idx

    all_cuts = 0
    for i, f in enumerate(field):
        rank_f = lvl_rank[f]
        for prev_rank in range(rank_f):
            sig_above = lvl[prev_rank]
            if i < last_pos[sig_above]:
                all_cuts += 1

    return all_cuts


def random_swap_level(lst: list, depth: int) -> list:
    """Randomly swaps two elements at a specified nesting depth."""
    target = lst
    for _ in range(depth):
        candidates = [x for x in target if isinstance(x, list)]
        if not candidates:
            return lst
        target = random.choice(candidates)

    if len(target) >= 2:
        i, j = random.sample(range(len(target)), 2)
        target[i], target[j] = target[j], target[i]

    return lst


def random_swap_hierarchical(blocks: list) -> list:
    """Creates a deep copy of the block structure and performs a random swap at a random depth."""
    new_blocks = copy.deepcopy(blocks)
    depth = random.choice([0, 1, 2])
    return random_swap_level(new_blocks, depth)


def optimize_routing(lvl: list[int], blocks_gate: list, iterations: int = 2000) -> tuple[list[int], list, int]:
    """Minimizes bus wire crossings using Simulated Annealing."""
    initial_field = map_field(blocks_gate)
    active_set = set(initial_field)
    active_lvl = [x for x in lvl if x in active_set]
    unused_lvl = [x for x in lvl if x not in active_set]

    current_lvl = active_lvl[:]
    current_blocks = copy.deepcopy(blocks_gate)
    current_score = valid_cuts_fast(current_lvl, initial_field)

    best_lvl = current_lvl[:]
    best_blocks = copy.deepcopy(current_blocks)
    best_score = current_score

    temp = 10.0
    cooling_rate = 0.995

    for _ in range(iterations):
        if random.random() < 0.5 and len(current_lvl) > 1:
            cand_lvl = current_lvl[:]
            i, j = random.sample(range(len(cand_lvl)), 2)
            cand_lvl[i], cand_lvl[j] = cand_lvl[j], cand_lvl[i]
            cand_blocks = current_blocks
        else:
            cand_lvl = current_lvl
            cand_blocks = random_swap_hierarchical(current_blocks)

        cand_field = map_field(cand_blocks)
        cand_score = valid_cuts_fast(cand_lvl, cand_field)

        delta = cand_score - current_score

        if delta < 0 or random.random() < math.exp(-delta / max(temp, 1e-6)):
            current_lvl = cand_lvl
            current_blocks = cand_blocks
            current_score = cand_score

            if current_score < best_score:
                best_score = current_score
                best_lvl = current_lvl[:]
                best_blocks = copy.deepcopy(current_blocks)

                if best_score == 0:
                    break

        temp *= cooling_rate

    return best_lvl + unused_lvl, best_blocks, best_score


def main() -> None:
    # Bus layers and logic gate block configuration (e.g., 7446 decoder)
    lvl = [1, 2, 3, 4, 5, 6, 7, 8]
    blocks_gate = [
        [
            [4, 8],
            [1, 6],
            [2, 3, 5, 7],
        ],
        [
            [4, 8],
            [2, 3, 6],
            [1, 4, 6],
        ],
        [
            [6, 8],
            [1, 4, 5],
        ],
        [
            [2, 3, 5],
            [1, 3, 6],
            [2, 4, 6],
        ],
        [
            [2],
            [3, 7],
        ],
        [
            [2, 4],
            [4, 5],
            [2, 5, 7],
        ],
        [
            [2, 4, 6],
            [3, 5, 7],
        ],
    ]

    initial_cuts = valid_cuts_fast(lvl, map_field(blocks_gate))
    print(f"Initial wire crossings: {initial_cuts}")

    global_best_cuts = float("inf")
    global_best_lvl = None
    global_best_blocks = None

    for _ in range(100):
        best_lvl, best_blocks, min_cuts = optimize_routing(lvl, blocks_gate, iterations=1000)

        if min_cuts < global_best_cuts:
            global_best_cuts = min_cuts
            global_best_lvl = best_lvl
            global_best_blocks = best_blocks

    print("-" * 40)
    print(f"Best global result: {global_best_cuts} crossings")
    print(f"Optimal layer order (lvl): {global_best_lvl}")
    print(f"Optimal block layout: {global_best_blocks}")


if __name__ == "__main__":
    main()
