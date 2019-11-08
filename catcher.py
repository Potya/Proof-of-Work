import socket
import numpy as np

sock = socket.socket()
sock.connect(('localhost', 9090))

data = (sock.recv(100000))
data = data.decode('utf-8')
key = int(data)
data = (sock.recv(100000))
data = data.decode('utf-8')
agents = int(data)
data = (sock.recv(100000))
data = data.decode('utf-8')
thr = int(data)
data = (sock.recv(100000))
data = data.decode('utf-8')
p = int(data)
print("Finite field", p)
parts = np.zeros((agents))
for i in range(0, agents):
    print(i)
    data = (sock.recv(100000))
    data = data.decode('utf-8')
    print(data)
    tmp = int(data)
    parts[i] = tmp
print(parts)
perm = np.zeros((agents))
for i in range(0, agents):
    perm[i] = i + 1
perm = np.random.permutation(perm)
print(perm)
matr = np.zeros((thr, thr))
for i in range(0, thr):
    for j in range(0, thr):
        matr[i][j] = pow(perm[i], thr - j - 1)
print(matr)
right = np.zeros((thr))
for i in range(0, thr):
    right[i] = parts[int(perm[i]) - 1]
print(right)
res = np.linalg.solve(matr, right)
print(res)
ptr = res[thr - 1]
solved_key = int(round(ptr)) % p
print(solved_key)
str_solved_key = str(solved_key).encode('utf-8')
sock.send(str_solved_key)
sock.close()

