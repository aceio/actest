#!/usr/bin/python
# -*- coding: utf-8 -*-
# scapy library will be used for packet processing

import os
import sys

from scapy.all import *

# SMALL LINK PROTOCOL (SML)
# Ethernet Layer 2 protocol using VLAN Priority to establish realtime
# communication. 
SML_ETH_TYPE = '0x81AA'

# Multihost communication in a subnet is realized with  the ethernet multicast address:
# MAC = 01:00:AA:00:00:00
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
    fields_desc=[ ByteEnumField("msg_type", 3, { 0: "time", 1: "cmd", 2: "ack",
        3: "data" }), ByteEnumField("dev_id", 1, { 0: "MN", 1: "CN"}),
            IntField("seq_num", 0), LongField("timestamp", 0)]


# To deliver the time over a subnet
class SmallLinkTimeServer():
    
    def __init__( self, ifname):
        self.__prot_bind()
        self.__pkt = Ether( src = get_if_hwaddr(ifname), dst = SML_DST_MAC ) /
        Dot1Q() / SmallLink( msg_type = 0, dev_id = 0, seq_num =
                random.randint( 0, 2**16-1 ) )

    # time server function blocking
    def serv(self):
        # start infinite sending loop
        while True :
            print "start time server... (CTRL-C abort)\n"
            self.__pkt.add_payload('time is ...')
            time.sleep(1)

    # Bind Small Link Protocol to the Dot1Q type field
    def __prot_bind(self):
        bind_layers( Dot1Q, SmallLink, {'type':int(SML_ETH_TYPE,16)})


