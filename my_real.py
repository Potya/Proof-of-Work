from Crypto.Util import number, randpool
from copy import deepcopy
from Crypto.Cipher import AES
import sys
import time
import socket
import numpy as np

rnd = randpool.RandomPool()


SECOND = 1
MINUTE = 60
HOUR = MINUTE * 60
DAY = HOUR * 24
MONTH = DAY * 31
YEAR = DAY * 365

MOD_BITS = 512 # 2048 # for time-lock puzzle N
AES_BITS = 24   # 192
FLD_BITS = 192 # for finite field p

def calibrate_speed():
    p = number.getPrime(MOD_BITS, rnd.get_bytes)
    q = number.getPrime(MOD_BITS, rnd.get_bytes)
    N = p * q
    bignum = number.getRandomNumber(MOD_BITS, rnd.get_bytes) #big number
    start = time.time()
    trials = 1000
    for i in range(0, trials):
        bignum = pow(bignum, 2, N)
    return int(trials/(time.time() - start))


def makepuzzle(t):
    # Generate 512-bit primes
    p = number.getPrime(MOD_BITS, rnd.get_bytes)
    q = number.getPrime(MOD_BITS, rnd.get_bytes)
    n = p * q
    fi = (p - 1) * (q - 1)

    key = number.getRandomNumber(AES_BITS, rnd.get_bytes)
    a = number.getRandomNumber(MOD_BITS, rnd.get_bytes) % n

    e = pow(2, t, fi)
    b = pow(a, e, n)

    cipher_key = (key + b) % n
    return (key, {'N': n, 'a': a, 'steps': t, 'cipher_key': cipher_key})



def solve_puzzle(p):
    tmp, N, t = p[1]['a'], p[1]['N'], p[1]['steps']
    start = time.time()
    i = 0
    while i < t:
        if (i+1) % SAVE_INTERVAL == 0:
            p2 = deepcopy(p)
            p2[1]['steps'] = i + 1
            p2[1]['a'] = tmp
            save_puzzle(p2)
        tmp = pow(tmp, 2, N)
        i += 1
    #print (sys.stderr)
    return (p[1]['cipher_key'] - tmp) % N


def save_puzzle(p):
    state = str(p)
    filename = 'puzzle_%d-%d.txt' % (p[1]['cipher_key'] % 1000000000000, p[1]['steps']/SAVE_INTERVAL)
    with open(filename, 'w') as f:
        f.write('# Run ./timelock FILENAME > OUTFILE to decode\n')
        putestimation(f, p)
        f.write('\n')
        f.write(state)
    print (sys.stderr, "saved state:", filename)

def eta(remaining, speed):
    seconds = remaining/speed
    if seconds < 100 * SECOND:
        return '%d seconds' % seconds
    elif seconds < 100 * MINUTE:
        return '%d minutes' % (seconds/MINUTE)
    elif seconds < 100 * HOUR:
        return '%d hours' % (seconds/HOUR)
    elif seconds < 60 * DAY:
        return '%d days' % (seconds/DAY)
    elif seconds < 20 * MONTH:
        return '%d months' % (seconds/MONTH)
    else:
        return '%d years' % (seconds/YEAR)

def putestimation(outputstream, puzzle):
    outputstream.write("# Estimated time to solve: %s\n" % eta(puzzle[1]['steps'], SPEED))

def key_split(key, n, k, p):
    a = []
    for i in range(0, k - 1):
        cur_a = number.getRandomNumber(AES_BITS, rnd.get_bytes)
        a.append(cur_a % p)
    a.append(key % p)
    print(a)
    part = []
    for i in range(1, n + 1):
        #arg = number.getRandomNumber(MOD_BITS, rnd.get_bytes)
        arg = i
        f = 0
        for j in range(0, k):
            f = (f + a[j] * pow(arg, k - j - 1)) % p
        part.append(f % p)
    return part



SPEED = calibrate_speed()
print("Current computating speed:", SPEED)
print("Type time interval in seconds")
SAVE_INTERVAL = int(input()) * SECOND * SPEED
#SAVE_INTERVAL = SPEED * 20 * SECOND

tlp = (makepuzzle(SAVE_INTERVAL))
print("key", tlp[0])
print("N", tlp[1]['N'])
print("a", tlp[1]['a'])
print("steps", tlp[1]['steps'])
print("Ck", tlp[1]['cipher_key'])

print()
print("Type number of trusted agents:")
num_agents = int(input())
print("Type threshold number:")
thr = int(input())
print()

p = number.getPrime(FLD_BITS, rnd.get_bytes)
while(p < tlp[0]):
    p = number.getPrime(FLD_BITS, rnd.get_bytes)
print("Finite field:", p)
#parts = key_split(11, 5, 3, 13)
parts = key_split(tlp[0], num_agents, thr, p) # k из Wiki
print(parts)

sock = socket.socket()
sock.bind(('', 9090))
sock.listen(1)
conn, addr = sock.accept()
print("Connected", addr)
str_key = str(tlp[0]).encode('utf-8')
conn.send(str_key)
time.sleep(0.1)
str_agents = str(num_agents).encode('utf-8')
conn.send(str_agents)
time.sleep(0.1)
str_thr = str(thr).encode('utf-8')
conn.send(str_thr)
time.sleep(0.1)
str_p = str(p).encode('utf-8')
conn.send(str_p)
time.sleep(0.1)
for i in range(0, len(parts)):
    print(i)
    tmp = str(parts[i] % p).encode("utf-8")
    print(tmp)
    conn.send(tmp)
    time.sleep(0.1)
print("All sended")
data = (conn.recv(100000))
data = data.decode('utf-8')
p = int(data)
sock.close()
if (tlp[0] == p):
    print('True key')
else:
    print("False key")


time.sleep(2)
print("Ready to solve")
time.sleep(0.1)
start = time.time()
print(solve_puzzle(tlp))
print(- start + time.time())
