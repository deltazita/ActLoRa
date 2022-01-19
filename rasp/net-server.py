#!/usr/bin/python3

import socket
import threading
import random
import hashlib
import binascii
import os
import sys
from Crypto.Cipher import AES

S = 1001
bind_ip = '192.168.0.254'
bind_port = 8000

AK = ["3878214125442A472D4B615064536756","7234753778217A25432A462D4A614E64","576D5A7134743777217A24432646294A","655368566D5971337436773979244226",
"4B6150645367566B5970337336763979","2A462D4A614E645267556B5870327335","7A24432646294A404E635266556A586E","36763979244226452948404D63516654",
"703373367638792F423F4528482B4D62","556B58703273357638782F413F442847","635266556A586E327235753878214125","48404D635166546A576E5A7234753777",
"3F4528482B4D6251655468576D5A7134","782F413F4428472B4B6250655368566D","35753778214125442A472D4B61506453","6E5A7234753777217A25432A462D4A61",
"5468576D5A7134743677397A24432646","6250655368566D597133743676397924","472D4B6150645367566B597033733676","25432A462D4A614E645267556B587032",
"77397A24432646294A404E635266556A","337336763979244226452948404D6351","6B59703373357638792F423F4528482B","5267556B58703273357538782F413F44",
"404E635266556A586E32723475377821","452948404D635166546A576E5A723474","2F423F4528482B4D6251655468576D5A","7538782F413F4428472B4B6250655368",
"5A7234753778214125442A472D4B6150","6A576E5A7134743777217A25432A462D","51655468576D5A7133743677397A2443","2B4B6250655368566D59713373367639",
"442A472D4B6150645367566B59703373","217A25432A462D4A614E645267556B58","743677397A24432646294A404E635266","5970337336763979244226452948404D"]

instigators = [11]
acts_of_inst = {11: [12]}
M = {11: "70B3D5499B6E0541", 12: "70B3D5499D7A2CDF"} # key = id, value = deveui
D = {} # key = DevAddr, value = id

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((bind_ip, bind_port))
server.listen(5)  # max backlog of connections

print("Listening on:", bind_ip, bind_port)


def gen_devaddr(a):
	a = format(a, 'b') # convert num of actuators to binary
	h = format(random.getrandbits(25), 'b')
	while (len(h) < 25):
		h = "".join(["0", h])
	h = "".join([a, h]) # join num of actuators with the random number
	h = hex(int(h, 2))[2:]
	while (len(h) < 8):
		h = "".join(["0", h])
	return h

#print(gen_devaddr(2))
#sys.exit()

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

def handle_client_connection(client_socket):
	request = client_socket.recv(1024)
	request = request.decode('utf-8')
	#request = client_socket # this line is only for testing
	print ("Received: ", request)
	(id, index, mac, JoinNonce, JoinEUI, DevNonce) = str(request).split(":")
	id = int(id)
	index = int(index)
	# compute a DevAddr
	DevAddr = ""
	is_inst = 0
	is_act = 0
	actuators = 0
	act_slots = []
	if id in instigators:
		actuators = len(acts_of_inst[id])
		is_inst = 1
	else:
		for i in acts_of_inst:
			if id in acts_of_inst[i]:
				is_act = 1
				has_inst = 0
				for addr in D:
					if (D[addr] == id):
						has_inst = 1
						DevAddr = addr
				if (has_inst == 0):
					print("Actuator without instigator!")
					sys.exit()
				continue
	if (is_act == 0):
		DevAddr = gen_slot(index, M[id], actuators)
	if (is_inst == 1):
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
				mac_ = M[acts_of_inst[id][j]]
				DevAddr_ = DevAddr ^ int(mac_[8:], 16)
				#print([mac_, hex(DevAddr_)[2:] ])
				D_temp[DevAddr_] = 1
				# verification here
				#DevA = DevAddr_ ^ int(mac_[:8], 16)
				#print(hex(DevA))
			exist = {}
			for d in D_temp:
				#print(d)
				s = (d % mod) + 1
				if (s in exist):
					act_test = 1
					DevAddr = gen_slot(index, M[id], actuators)
					while (DevAddr in have_tried):
						DevAddr = gen_slot(index, M[id], actuators)
					break
				exist[s] = 1
			if (act_test == 0):
				#print("Done for slots", index, "to", index+actuators)
				j = 0
				for d in D_temp:
					#print(d, (d % mod) + 1)
					# verification:
					if (DevAddr != d ^ int(M[acts_of_inst[id][j]][8:], 16)):
						print("This shouldn't happen!")
						sys.exit()
					if (d in D):
						print("This shouldn't happen!")
						sys.exit()
					D[d] = acts_of_inst[id][j]
					j += 1
		act_slots = list(exist.keys())
	D[DevAddr] = id
	DevAddr = hex(DevAddr)[2:]
	# verification of actuators bits in DevAddr
	#d = str(format(int(DevAddr, 16), 'b'))
	#while (len(d) < 32):
		#d = "".join(["0", d])
	#d = str(d)[4:][:-25]
	#d = int(d, 2)
	#print(d) # <-- it must print num of actuators
	# compute the AppSKey
	AppKey = AK[id-11]
	text = "".join( [AppKey[:2], JoinNonce, JoinEUI, DevNonce] )
	while (len(text) < 32):
		text = "".join([text,"0"])
	encryptor = AES.new(AppKey, AES.MODE_ECB)
	AppSKey = encryptor.encrypt(binascii.unhexlify(text.encode('utf-8')))
	acts = ""
	if (is_inst == 1):
		acts = str(acts_of_inst[id])[1:][:-1].replace(" ", "")
	msg = str(id)+":"+acts+":"+str(act_slots)[1:][:-1].replace(" ", "")+":"+str(DevAddr)+":"
	print("Responded: "+msg+"AppSKey")
	client_socket.send( bytes(msg.encode('utf-8'))+AppSKey ) # AppSKey is already in bytes
	client_socket.close()

while True:
    client_sock, address = server.accept()
    print ("Accepted connection from: ", address[0], address[1])
    client_handler = threading.Thread(
        target=handle_client_connection,
        args=(client_sock,)
    )
    client_handler.start()

# testing
#req = "11:0:70B3D5499B6E0541:1:3efd4267ef71836a:1"
#handle_client_connection(req)
#print(D)
#req = "12:0:70B3D5499D7A2CDF:1:3efd4267ef71836a:1"
#handle_client_connection(req)
#print(D)
