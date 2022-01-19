#!/usr/bin/python3

# script to generate a given number (index) of DevAddrs for slots 0 to index-1
# Actuator version

import random
import hashlib
import sys
import time
import binascii
import numpy as np

S = 1001
index = int(sys.argv[1]) # max slots
actuators = int(sys.argv[2]) # actuators per instigator
avg_time = 0.0
max_time = 0.0
D = {} # all generated DevAddrs have key = 1
M = {} # all DevEUIs as values

As = [] # slots (indices) that will be used for actuating
for i in range(0, index, actuators+1):
	if (i + actuators + 1 > index):
		continue
	As.append(i)
#print(As)

def gen_devaddr(a):
	a = format(a, "b")
	h = hex(random.getrandbits(25))[2:][:-1]
	h = "".join([a, h])
	while (len(h) < 8):
		h = "".join(["0", h])
	return h

def gen_mac():
	m = hex(random.getrandbits(64))[2:][:-1]
	while (len(m) < 16):
		m = "".join(["0", m])
	return m

def gen_slot(n, mac, mod):
	mac = str(mac)
	while True:
		DevAddr = str(gen_devaddr(mod))
		while (DevAddr in D):
			DevAddr = str(gen_devaddr(mod))
		text = DevAddr
		thash = hashlib.sha256()
		thash.update(text.encode('utf-8'))
		thash = int(binascii.hexlify(thash.digest()), 16)
		slot = thash % S
		if (slot == n):
			break
	return int(DevAddr, 16)

# generate as many DevEUIs as the number of slots
for n in range(index):
	mac = str(gen_mac())
	while (n in M):
		mac = str(gen_mac())
	M[n] = mac

for n in range(0, index, actuators+1):
	#n = random.randint(0, index)
	#print(n)
	if (n % 10 == 0):
		sys.stderr.write(str(n)+"\n")
	start = time.time()
	DevAddr = gen_slot(n, M[n], actuators)
	if (n in As):
		act_test = 1
		mod = actuators
		if (actuators % 2 == 0):
			mod += 1
		have_tried = {}
		while (act_test == 1):
			have_tried[DevAddr] = 1
			act_test = 0
			D_temp = {}
			for j in range(actuators):
				# generate DevAddr for actuating
				#print("Generating actuator's", j+1, "DevAddr")
				mac_ = M[n+j+1]
				DevAddr_ = DevAddr ^ int(mac_[8:], 16)
				#print([mac_, hex(DevAddr_)[2:] ])
				D_temp[DevAddr_] = 1
				# verification here
				#DevA = DevAddr_ ^ int(mac_[:8], 16)
				#print(hex(DevA))
			exist = {}
			for d in D_temp:
				s = (d % mod) + 1
				if (s in exist):
					act_test = 1
					DevAddr = gen_slot(n, M[n], actuators)
					while (DevAddr in have_tried):
						DevAddr = gen_slot(n, M[n], actuators)
					break
				exist[s] = 1
			if (act_test == 0):
				#print("Done for slots", n, "to", n+actuators)
				j = 0
				for d in D_temp:
					#print(d, (d % mod) + 1)
					# verification:
					if (DevAddr != d ^ int(M[n+j+1][8:], 16)):
						print("This shouldn't happen!")
						sys.exit()
					if (d in D):
						print("This shouldn't happen!")
						sys.exit()
					D[d] = 1
					j += 1
	D[DevAddr] = 1
	finish = time.time()
	avg_time += (finish - start)
	if (finish-start > max_time):
		max_time = finish-start

print(avg_time/index, max_time)
