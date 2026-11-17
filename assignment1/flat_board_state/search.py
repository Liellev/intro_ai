import heapq

from search_node import search_node
from flat_board_state import flat_board_state

count_generated = 0
count_expanded = 0

def get_state_key(vn):
    board = vn.state.get_state_board()

    key = []

    for row in board:
        key.append(tuple(row))

    return tuple(key)


def create_open_set():
    return {
        "heap": [],
        "nodes": {},
        "counter": 0
    }


def create_closed_set():
    return {}
    



def add_to_open(vn, open_set):
    key = get_state_key(vn)

    counter = open_set["counter"]
    open_set["counter"] += 1

    heapq.heappush(
        open_set["heap"],
        (vn.f, vn.h, counter, key, vn)
    )

    open_set["nodes"][key] = vn


def open_not_empty(open_set):
    return len(open_set["nodes"]) > 0



def get_best(open_set):

    while len(open_set["heap"]) > 0:

        f, h, counter, key, vn = heapq.heappop(
            open_set["heap"]
        )

        current_node = open_set["nodes"].get(key)

        if current_node is vn:
            del open_set["nodes"][key]
            return vn

    raise IndexError("OPEN is empty")



def add_to_closed(vn, closed_set):
    key = get_state_key(vn)
    closed_set[key] = vn

#returns False if curr_neighbor state not in open_set or has a lower g from the node in open_set
#remove the node with the higher g from open_set (if exists)
def duplicate_in_open(vn, open_set):
    key = get_state_key(vn)

    existing_node = open_set["nodes"].get(key)

    if existing_node is None:
        return False

    if existing_node.g <= vn.g:
        return True

    # Existing path is worse: remove its active entry
    del open_set["nodes"][key]

    return False

#returns False if curr_neighbor state not in closed_set or has a lower g from the node in closed_set
#remove the node with the higher g from closed_set (if exists)
def duplicate_in_closed(vn, closed_set):
    key = get_state_key(vn)

    existing_node = closed_set.get(key)

    if existing_node is None:
        return False

    if existing_node.g <= vn.g:
        return True

    # Better path found: reopen this state
    del closed_set[key]

    return False


# helps to debug sometimes..
def print_path(path):
    for i in range(len(path)-1):
        print(f"[{path[i].state.get_state_str()}]", end=", ")
    print(path[-1].state.get_state_str())

def get_gen_exp_count():
    global count_generated
    global count_expanded
    return count_generated, count_expanded

def search(start_state, heuristic):
    global count_generated
    global count_expanded
    count_generated = 0
    count_expanded = 0
    open_set = create_open_set()
    closed_set = create_closed_set()
    start_node = search_node(start_state, 0, heuristic(start_state))
    add_to_open(start_node, open_set)

    while open_not_empty(open_set):

        current = get_best(open_set)

        if flat_board_state.is_goal_state(current.state):
            path = []
            while current:
                path.append(current)
                current = current.prev
            path.reverse()
            return path

        add_to_closed(current, closed_set)
        count_expanded += 1

        for neighbor, edge_cost in current.get_neighbors():
            curr_neighbor = search_node(neighbor, current.g + edge_cost, heuristic(neighbor), current)
            if not duplicate_in_open(curr_neighbor, open_set) and not duplicate_in_closed(curr_neighbor, closed_set):
                add_to_open(curr_neighbor, open_set)
                count_generated += 1

    return None




