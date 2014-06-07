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
    v = random.choice((1,1,1,1,2))
    result[i] = v
    return tuple(result)

def main():
    field = add_random_tile(add_random_tile(empty_field))
    while True:
        print('\n'.join('\t'.join('' if v == 0 else str(2 ** v) for v in field[row:row+N]) for row in range(0, N*N, N)))
        d = input().strip()
        dir_tr = dict(zip('wasd', (UP, LEFT, DOWN, RIGHT)))
        result = move(field, dir_tr[d])
        if result:
            field = add_random_tile(result)

if __name__ == '__main__':
    main()
