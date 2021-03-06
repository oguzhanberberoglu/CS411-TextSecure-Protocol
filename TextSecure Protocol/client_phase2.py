# -*- coding: utf-8 -*-
"""Client_phase2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1lUA4-HCyFjhkVKCFz6wuVVEdiX0UEie4
"""
"""
!pip install ecpy
!pip install sympy
!pip install pyprimes
!pip install pycryptodome
"""
import json
import re
from Crypto.Util.Padding import unpad
from Crypto.Util.Padding import pad
from Crypto import Random
from Crypto.Cipher import AES
import requests
from Crypto.Hash import SHA3_256
import math
import timeit
import random
import sympy
import warnings
from random import randint, seed
import sys
from ecpy.curves import Curve, Point
from Crypto.Hash import HMAC, SHA256
API_URL = 'http://cryptlygos.pythonanywhere.com'

stuID = 24001  # 24198,19872, 23574, 25655

seed(13)
E = Curve.get_curve('secp256k1')
n = E.order
p = E.field
P = E.generator
a = E.a
b = E.b
print("Base point:\n", P)
print("p :", p)
print("a :", a)
print("b :", b)
print("n :", n)
print("P :", P)

# server's long term key
QSer_long = Point(0xc1bc6c9063b6985fe4b93be9b8f9d9149c353ae83c34a434ac91c85f61ddd1e9,
                  0x931bd623cf52ee6009ed3f50f6b4f92c564431306d284be7e97af8e443e69a8c, E)
print("QSer_long :", QSer_long)

# create a long term key
sL = randint(2, n-1)
lkey = sL * P
print("sA :", sL)
print("LKEY :", lkey)
print('LKEY.X: ', lkey.x)
print('LKEY.Y: ', lkey.y)

k = randint(1, n-2)
print("k: ", k)
R = k * P
print("R: ", R)
print("Rx: ", R.x)
r = R.x % n
print("r: ", r)
h_ = SHA3_256.new(str.encode(str(stuID)) +
                  r.to_bytes((r.bit_length()+7)//8, byteorder='big'))
h = int.from_bytes(h_.digest(), byteorder='big') % n
print("h: ", h)
s = (sL * h + k) % n
print("s: ", s)

# Register Long Term Key
try:
    mes = {'ID': stuID, 'H': h, 'S': s, 'LKEY.X': lkey.x, 'LKEY.Y': lkey.y}
    response = requests.put('{}/{}'.format(API_URL, "RegLongRqst"), json=mes)
    print(response.json())
    code = input()

    mes = {'ID': stuID, 'CODE': code}
    response = requests.put('{}/{}'.format(API_URL, "RegLong"), json=mes)
    print(response.json())
except Exception as e:
    print(e)

ekeyList = {}
print("Registering ephermeral keys...\n")
for i in range(10):
    print("Processing ephemeral key with ID ", i)
    si = randint(2, n-1)
    ekey = si * P
    ekeyList[i] = [si, ekey.x, ekey.y]
    concatQxy = str(ekey.x) + str(ekey.y)

    ki = randint(1, n-2)
    Ri = ki * P
    ri = Ri.x % n
    h_ = SHA3_256.new(str.encode(str(concatQxy)) +
                      ri.to_bytes((ri.bit_length()+7)//8, byteorder='big'))
    hi = int.from_bytes(h_.digest(), byteorder='big') % n
    si = (sL * hi + ki) % n
    try:
        mes = {'ID': stuID, 'KEYID': i, 'QAI.X': ekey.x,
               'QAI.Y': ekey.y, 'Si': si, 'Hi': hi}
        response = requests.put('{}/{}'.format(API_URL, "SendKey"), json=mes)
        print(response.json())
        print()
    except Exception as e:
        print(e)

for j in range(len(ekeyList)):
    try:
        mes = {'ID_A': stuID, 'S': s, 'H': h}
        response = requests.get('{}/{}'.format(API_URL, "ReqMsg"), json=mes)
        print(response.json())
        response = response.json()
        IDB = response["IDB"]
        keyid = response["KEYID"]
        msg = response["MSG"]
        QBJx = response["QBJ.X"]
        QBJy = response["QBJ.Y"]
        Qb = Point(QBJx, QBJy, E)
        sAi = ekeyList[int(keyid)][0]
        QAx = ekeyList[int(keyid)][1]
        QAy = ekeyList[int(keyid)][2]
        Qa = Point(QAx, QAy, E)
        T = sAi * Qb
        U = str(T.x) + str(T.y) + "NoNeedToRunAndHide"
        Kenc = SHA3_256.new(U.encode()).digest()
        Kmac = SHA3_256.new(Kenc).digest()
        mes = msg.to_bytes((msg.bit_length() + 7) // 8, 'big')
        H = HMAC.new(Kmac, digestmod=SHA256)
        H.update(mes[8:-32])
        try:
            H.verify(mes[-32:])
            print("The message '%s' is authentic" % msg)
            cipher = AES.new(Kenc, AES.MODE_CTR, nonce=mes[0:8])
            mes_ = mes[8:-32]
            dtext_mes = cipher.decrypt(mes[8:-32])
            dtext = dtext_mes.decode('UTF-8')
            print("Decrypted text: ", dtext)
        except ValueError:
            print("The message or the key is wrong")
        mesCh = {'ID_A': stuID, 'DECMSG': dtext}
        response_ = requests.put(
            '{}/{}'.format(API_URL, "Checker"), json=mesCh)
        print(response_.json())
        print()
    except Exception as e:
        print(e)

"""###delete ephemeral keys
try:
  mes = {'ID': stuID, 'S': s, 'H': h}
  response = requests.get('{}/{}'.format(API_URL, "RstEKey"), json = mes)
  print(response.json())
except Exception as e:
  print(e)

###########DELETE LONG TERM KEY
# If you lost your long term key, you can reset it yourself with below code.

# First you need to send a request to delete it.
try:
  mes = {'ID': stuID}
  response = requests.get('{}/{}'.format(API_URL, "RstLongRqst"), json = mes)
  print(response.json())
  #Then server will send a verification code to your email. 
  # Send this code to server using below code
  code = input()
  mes = {'ID': stuID, 'CODE': code}
  response = requests.get('{}/{}'.format(API_URL, "RstLong"), json = mes)
  #Now your long term key is deleted. You can register again. 
  print(response.json())
except Exception as e:
  print(e)
"""
