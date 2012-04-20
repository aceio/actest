#!/usr/bin/python
# -*- coding: utf-8 -*-
# scapy library will be used for packet processing

import os
import sys
import time
import struct
import socket

from scapy.all import *

# SMALL LINK PROTOCOL (SML)
# Ethernet Layer 2 protocol using VLAN Priority to establish realtime
# communication. 
SML_ETH_TYPE = 0x81AA

# VLAN Priority:
#
# BE: Best Effort 
# BK: Background
# - : Spare
# EE: Excellent Effort
# CL: Controlled Load
# VI: Video < 100 ms
# VO: Voice < 10 ms
# NC: Network Control
SML_VLAN_PRIO = {'BE': 0, 'BK': 1, '-': 2, 'EE': 3, 'CL': 4, 'VI': 5, 'VO': 6,
                 'NC': 7} 

SML_VLAN_ID	= 2048

# Multihost communication in a subnet is realized with the ethernet multicast 
# address:
SML_DST_MAC = '01:00:AA:00:00:00'

# Small Link Protocol Header:
#
# | 31 - 24  |  24 - 16 |      15 -  0       |
# | msg_typ  |  dev_id  |       seq_num      |
# |                 timestamp                |
#
# msg_type: 0 time      multicast
#           1 cmd       multicast/unicast
#           2 ack       unicast
#           3 data      unicast
#
# dev_id:       Deve class identification field.
#
# seq_num:      Seqence number initialized with random value.
#
# timestamp:    The timestamp is a 32-bit value, indicating the send time of
#               the packet.
class SmallLink(Packet):
    name = "SmallLinkPacket"
    fields_desc = [ByteEnumField("msg_type", 3, {0: "time", 1: "cmd", 2: "ack",
                                                 3: "data" }), 
                   ByteEnumField("dev_id", 1, {0: "MN", 1: "CN"}),
                   IntField("seq_num", 0), LongField("timestamp", 0)]



# To deliver the time over a subnet
class SmallLinkTimeServer():
    

    def __init__(self, ifname):
        self.__prot_bind()
        self.__ifname = ifname
        self.__head = Ether(src = get_if_hwaddr(ifname), dst = SML_DST_MAC)
        self.__head = self.__head / Dot1Q(prio = SML_VLAN_PRIO['NC'],
                                          id = SML_VLAN_ID)
        seq_num = random.randint(0, 2**16 - 1)
        self.__head = self.__head / SmallLink(msg_type = 0, 
                                              dev_id = 0,
                                              seq_num = seq_num)
        
    # time server function blocking
    def srv(self):
        # start infinite sending loop
        print "start time server... (CTRL-C abort)\n"
        while True :
            self.__head.lastlayer().seq_num += 1 
            pkt = self.__head / ('time is ...%f' %(time.time()))
            sendp(pkt, iface=self.__ifname) 
            time.sleep(1)

    # Bind Small Link Protocol to the Dot1Q type field
    def __prot_bind(self):
        bind_layers(Dot1Q, SmallLink, {'type': SML_ETH_TYPE})
        bind_layers(Ether, SmallLink, {'type': SML_ETH_TYPE})



class SmallLinkTimeClient():


    def __init__( self, ifname):
        self.__prot_bind()
        self.__sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, SML_ETH_TYPE)
        self.__sock.bind((ifname, SML_ETH_TYPE))

        # enable multicast traffic on the interface

        # struct packet_mreq{
        #       int             mr_ifindex;
        #       unsigned short  mr_type;
        #       unsigned short  mr_alen;
        #       unsigned char   mr_address[8];

        # define some missing constants for socket
        PACKET_MR_MULTICAST     = 0
        SOL_PACKET              = 263
        PACKET_ADD_MEMBERSHIP   = 1

        mr = struct.pack('iHH6sH', get_if_index(ifname), PACKET_MR_MULTICAST, 6,
                         ''.join([chr(int(s, 16)) 
                                  for s in SML_DST_MAC.split(':')]), 0) 

        self.__sock.setsockopt(SOL_PACKET, PACKET_ADD_MEMBERSHIP, mr)


    # time client function blocking 
    def cli(self):
        print 'start client time function... (CTRL-C abort)\n'
        while True:
            buf = self.__sock.recv(1024)
            pkt = Ether(buf)
            pkt.show()
        

    # Bind Small Link Protocol to the Dot1Q type field
    def __prot_bind(self):
        bind_layers(Dot1Q, SmallLink, {'type': SML_ETH_TYPE})
        bind_layers(Ether, SmallLink, {'type': SML_ETH_TYPE})


