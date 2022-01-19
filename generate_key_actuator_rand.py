#!/usr/bin/python3

# script to generate DevAddrs for a random slot and a given number of actuators per instigator
# Actuator version

import random
import hashlib
import sys
import time
import binascii
import numpy as np

S = 1001
iterations = int(sys.argv[1]) # number of tries
actuators = int(sys.argv[2]) # actuators per instigator
index = S-1;
avg_time = 0.0
max_time = 0.0

def gen_devaddr(a):
	a = format(a, 'b')
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

for x in range(0, iterations):
	D = {} # all generated DevAddrs have key = 1
	M = {} # all DevEUIs as values
	mac = str(gen_mac())
	M[actuators] = mac
	n = random.randint(0, index)
	print(x, "slot:", n)
	for j in range(actuators):
		mac_ = str(gen_mac())
		while (j in M):
			mac_ = str(gen_mac())
		M[j] = mac_
	start = time.time()
	DevAddr = gen_slot(n, mac, actuators)
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
			mac_ = M[j]
			DevAddr_ = DevAddr ^ int(mac_[8:], 16)
			#print([mac_, hex(DevAddr_)[2:] ])
			D_temp[DevAddr_] = 1
			# verification here
			#DevA = DevAddr_ ^ int(mac_[:8], 16)
			#print(hex(DevA))
		exist = {}
		j = 0
		for d in D_temp:
			s = (d % mod) + 1
			#print(DevAddr, int(M[j][8:], 16), d, s)
			if (s in exist):
				act_test = 1
				DevAddr = gen_slot(n, mac, actuators)
				while (DevAddr in have_tried):
					DevAddr = gen_slot(n, mac, actuators)
				break
			exist[s] = 1
			j+=1
		if (act_test == 0):
			#print("Instigator's DevAddr:", DevAddr)
			j = 0
			for d in D_temp:
				#print(d, (d % mod) + 1, d ^ int(M[j][:8], 16))
				# verification:
				if (DevAddr != d ^ int(M[j][8:], 16)):
					print("This shouldn't happen!")
					sys.exit()
				if (d in D):
					print("This shouldn't happen!")
					sys.exit()
				D[d] = 1
				j+=1
	D[DevAddr] = 1
	finish = time.time()
	avg_time += (finish - start)
	if (finish-start > max_time):
		max_time = finish-start

print(avg_time/index, max_time)
