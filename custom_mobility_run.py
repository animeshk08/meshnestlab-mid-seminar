#!/usr/bin/env python3

import os
import sys
import glob
import copy

import json

sys.path.append('../../')
import software
import network
import topology
import mobility
from shared import Remote
import tools


remotes= [Remote()]

tools.check_access(remotes)
software.clear(remotes)
network.clear(remotes)

prefix = os.environ.get('PREFIX', '')

# 100MBit LAN cable
def get_tc_command(link, ifname):
	return f'tc qdisc replace dev "{ifname}" root tbf rate 100mbit burst 8192 latency 1ms'

def run(protocol, csvfile):
	tools.seed_random(42)

	node_count = 3
	state = topology.create_nodes(node_count)
	mobility.randomize_positions(state, xy_range=1000)
	mobility.connect_range(state, max_links=150)

	# create network and start routing software
	network.apply(state, link_command=get_tc_command, remotes=remotes)
	software.start(protocol)

	test_beg_ms = tools.millis()
	for n in range(0, 5):
		print(f'{protocol}: iteration {n}')

		# connect nodes range
		wait_beg_ms = tools.millis()

		# update network representation
		mobility.move_random(state, distance=20)
		mobility.connect_range(state, max_links=150)

		with open(f'./example_dump/graph-{protocol}-{n:03d}.json', 'w+') as file:
			json.dump(state, file, indent='  ')

		# update network
		tmp_ms = tools.millis()
		network.apply(state=state, link_command=get_tc_command, remotes=remotes)

		network_ms = tools.millis() - tmp_ms

		# Wait until wait seconds are over, else error
		tools.wait(wait_beg_ms, 10)

		paths = tools.get_random_paths(state, 1)
		# paths = tools.filter_paths(state, paths, min_hops=2, path_count=10)
		ping_result = tools.ping_paths(paths=paths, duration_ms=2000, verbosity='verbose', remotes=remotes)

		# add data to csv file
		extra = (['node_count', 'time_ms'], [node_count, tools.millis() - test_beg_ms])
		tools.csv_update(csvfile, '\t', extra, ping_result.getData())

	software.clear(remotes)
	network.clear(remotes)

for protocol in ['babel']:
	with open(f"{prefix}custom_mobility-{protocol}.csv", 'w+') as csvfile:
		run(protocol, csvfile )

tools.stop_all_terminals()
