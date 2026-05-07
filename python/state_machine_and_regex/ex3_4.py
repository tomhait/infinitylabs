import re

TRANSITION_TABLE = {
    ('START', '0'): 'ZERO',
    ('START', '1'): 'DEAD',
    ('DEAD', '0'): 'DEAD',
    ('DEAD', '1'): 'DEAD',
    ('ZERO', '0'): 'ACCEPT',
    ('ZERO', '1'): 'ZERO',
    ('ACCEPT', '0'): 'ACCEPT',
    ('ACCEPT', '1'): 'ZERO'
}
def acceptor(bin_str: str):
    current_state = 'START'
    for c in bin_str:
        current_state = TRANSITION_TABLE[(current_state,c)]
        if current_state == 'DEAD':
            break
    if current_state == 'ACCEPT':
        return True
    return False

def acceptor_re(bin_str: str):
    return bool(re.search(r'^0[01]*0$', bin_str))

if __name__=='__main__':
    f = acceptor
    print(f'00: {f('00')}')
    print(f'01110: {f('01110')}')
    print(f'0101010: {f('0101010')}')
    print(f'0: {f('0')}')
    print(f'01: {f('01')}')
    print(f'10001: {f('10001')}')
    print(f'101010: {f('101010')}')

    f = acceptor_re
    print("\nAcceptor using regex")
    print(f'00: {f('00')}')
    print(f'01110: {f('01110')}')
    print(f'0101010: {f('0101010')}')
    print(f'0: {f('0')}')
    print(f'01: {f('01')}')
    print(f'10001: {f('10001')}')
    print(f'101010: {f('101010')}')