import sys
import curses
import random

dirs = (0,1,2,3)
LEFT, UP, RIGHT, DOWN = dirs
N = 4

empty_field = (0,) * (N*N)

def rotate(field, times):
    """Rotate field counter-clockwise by `times` quarters."""
    if not field:
        return field
    elif times >= 2:
        return rotate(tuple(reversed(field)), times - 2)
    elif times == 1:
        indices = (
            3, 7, 11,15,
            2, 6, 10,14,
            1, 5, 9, 13,
            0, 4, 8, 12,
            )
        return tuple(field[i] for i in indices)
    else:
        return field

def move_left(field):
    result = list(empty_field)
    for i in range(0, N*N, N):
        j, k = i, i
        while j < i+N:
            if field[j] != 0:
                result[k] = field[j]
                k += 1
            j += 1
        j, k = i, i
        while j < i+N and result[j] != 0:
            if j+1 < i+N and result[j] == result[j+1]:
                result[k] = result[j]+1
                j += 2
            else:
                result[k] = result[j]
                j += 1
            k += 1
        while k < i+N:
            result[k] = 0
            k += 1
    result = tuple(result)
    if result == field:
        return None
    else:
        return result

def move(field, direction):
    if direction == LEFT:
        return move_left(field)
    else:
        return rotate(move_left(rotate(field, direction)), 4 - direction)

def add_random_tile(field):
    result = list(field)
    i = random.choice([i for i in range(N*N) if field[i] == 0])
    v = random.choice((1,)*9 + (2,))
    result[i] = v
    return tuple(result)

def fitness(field):
    if not field:
        return float('-inf')
    def corner(v, u1, u2):
        if u1 > v < u2:
            return 0
        else:
            return 4**v
    def side(v):
        return 3**v
    def neighbor(u, v):
        if u == v:
            return 3 ** u
        u, v = min(u, v), max(u, v)
        if u + 1 == v and u > 3:
            return 2 ** u
        return 0

    return (sum(2**v for v in field)
        +sum(corner(field[i1 + j1], field[i1 + j2], field[i2 + j1]) for i1, i2 in ((0, 1), (3, 2)) for j1, j2 in ((0, 4), (12, 8)))
        +sum(side(field[i]) for i in (1, 2, 4, 7, 8, 11, 13, 14))
        +sum(neighbor(field[i], field[i+1]) for j in range(0, N*N, N) for i in range(j, j+3))
        +sum(neighbor(field[i], field[i+N]) for j in range(0, N*N - N, N) for i in range(j, j+4))
    )

def future_fitness(field, depth):
    if depth == 0:
        return fitness(field)
    return max(future_fitness(f, depth - 1)
            for f in (move(field, d) for d in dirs)
            if f is not None)

class GameLost(Exception):
    pass

def print_field(field):
    numbers = dict(enumerate((
        '    ',
        '  2 ',
        '  4 ',
        '  8 ',
        ' 16 ',
        ' 32 ',
        ' 64 ',
        '128 ',
        '256 ',
        '512 ',
    )))
    print('\n'.join(''.join(numbers.get(v, '^%s ' % v) for v in field[row:row+N]) for row in range(0, N*N, N)))
    print('sum=%s, fitness=%s' % (sum(0 if v == 0 else 2**v for v in field), fitness(field)))
    print('-'*16)

class Game(object):
    def start(self):
        self._field = add_random_tile(add_random_tile(empty_field))
        #print_field(self._field)
        return self._field

    def move(self, d):
        dir_tr = {UP: 'UP', LEFT: 'LEFT', DOWN: 'DOWN', RIGHT: 'RIGHT'}
        #print(dir_tr[d])
        result = move(self._field, d)
        if result:
            self._field = add_random_tile(result)
            #print_field(self._field)
            return self._field
        else:
            return None

def draw_field(stdscr, field, r, c, caption=''):
    if field is None:
        field = (0,) * (N*N)
    for i, row in enumerate(field[j:j+N] for j in range(0, N*N, N)):
        for j, v in enumerate(row):
            if v == 0:
                s = '    '
            elif v < 10:
                s = '%3d ' % (2 ** v)
            else:
                s = '^%d ' % v
            stdscr.addstr(r + 2 * i, c + 4 * j, s)
    stdscr.addstr(r + 2 * N, c, caption.center(4 * N))

R = 2 * (N + 1)
C = 4 * N + 2

def manual():
    stdscr = curses.initscr()
    try:
        curses.cbreak()
        curses.noecho()
        stdscr.vline(0, C-1, '|', 3*R)
        stdscr.vline(0, 2*C-1, '|', 3*R)
        stdscr.hline(R-1, 0, '-', 3*C)
        stdscr.hline(2*R-1, 0, '-', 3*C)
        game = Game()
        field = game.start()
        while True:
            key_to_dir = dict(zip('wasd', (UP, LEFT, DOWN, RIGHT)))
            dir_to_key = {k: v for v, k in key_to_dir.items()}
            base_fitness = fitness(field)
            draw_field(stdscr, field, 1*R, 1*C, caption=str(base_fitness))
            future = {d: move(field, d) for d in dirs}
            future_fitness = {d: fitness(f) if f else float('-inf') for d, f in future.items()}
            for d, i, j in ((UP, 0, 1), (LEFT, 1, 0), (RIGHT, 1, 2), (DOWN, 2, 1)):
                draw_field(stdscr, future[d], i*R, j*C, '%+g' % (future_fitness[d] - base_fitness))
            d = stdscr.getkey()
            max_fitness = sorted(future_fitness.items(), key=lambda o: -o[1])[0]
            if d == 'q':
                break
            elif d == ' ':
                field = game.move(max_fitness[0]) or field
            else:
                try:
                    d = key_to_dir[d]
                    if future_fitness[d] < max_fitness[1]:
                        with open('odd_moves.txt', 'a') as fp:
                            fp.write('%r\n' % [field, d, max_fitness[0], list(future_fitness.items())])
                    field = game.move(d) or field
                except KeyError:
                    pass
    finally:
        curses.endwin()

def run_ai():
    game = Game()
    field = game.start()
    while True:
        neighbors = tuple((d, move(field, d)) for d in dirs)
        neighbor_fitness = sorted(
                tuple((n, d, future_fitness(n, 0)) for d, n in neighbors if n is not None),
                key=lambda a: -a[2])
        if not neighbor_fitness:
            return field
        field = game.move(neighbor_fitness[0][1])

def ai():
    field = run_ai()
    print_field(field)

def aistats():
    next_report = 8
    stats = [0]*20
    while True:
        best = max(run_ai())
        stats[best] += 1
        if sum(stats) == next_report:
            print('{%s}' % ', '.join('%d: %d' % (2**i, v) for i, v in enumerate(stats) if v != 0))
            next_report += min(32, next_report)

def odd_moves():
    dir_tr = {UP: 'UP', LEFT: 'LEFT', DOWN: 'DOWN', RIGHT: 'RIGHT'}
    lines = []
    with open('odd_moves.txt') as fp:
        for line in fp:
            field, human, old_ai, old_future_fitness = eval(line, {'inf': float('inf')})
            future = {d: move(field, d) for d in dirs}
            future_fitness = {d: fitness(f) if f else float('-inf') for d, f in future.items()}
            ai = max(future_fitness.items(), key=lambda o: o[1])[0]
            lines.append((field, human, ai, future_fitness))
    lines = sorted(lines, key=lambda o: o[3][o[2]] - o[3][o[1]])
    for line in lines:
        field, human, ai, future_fitness = line
        if future_fitness[ai] <= future_fitness[human]:
            continue
        print_field(field)
        print("Human chose %s (%s), but I would have chosen %s (%s)" % (dir_tr[human], future_fitness[human], dir_tr[ai], future_fitness[ai]))

if __name__ == '__main__':
    try:
        mode = sys.argv[1]
    except IndexError:
        mode = 'help'
    if mode == 'manual':
        manual()
    elif mode == 'ai':
        ai()
    elif mode == 'aistats':
        aistats()
    elif mode == 'odd_moves':
        odd_moves()
    else:
        print("Please specify a mode: manual, ai or odd_moves")
