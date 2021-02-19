#!/usr/bin/env python3

import os
import sys
import glob

sys.path.append('../../')
from shared import Remote
import software
import network
import tools


remotes= [Remote()] #[Remote('192.168.44.133'), Remote('192.168.44.137')]

tools.check_access(remotes)
software.clear(remotes)
network.clear(remotes)

prefix = os.environ.get('PREFIX', '')

# 100MBit LAN cable
def get_tc_command(link, ifname):
	return f'tc qdisc replace dev "{ifname}" root tbf rate 100mbit burst 8192 latency 1ms'

def run(protocol, csvfile):
	for path in sorted(glob.glob(f'graph_grid4.json')):
		print("Loading topology..")
		state = tools.load_json(path)
		(node_count, link_count) = tools.json_count(state)
		print("Creating network..")
		network.apply(state=state, link_command=get_tc_command, remotes=remotes)

		tools.sleep(2)
		print("Starting protocol on network..", protocol)
		
		software_start_ms = tools.millis()
		software.start(protocol, remotes)
		software_startup_ms = tools.millis() - software_start_ms

		tools.sleep(5)

		start_ms = tools.millis()
		traffic_beg = tools.traffic(remotes)

		paths = tools.get_random_paths(state,  link_count)
		# paths = tools.filter_paths(state, paths, min_hops=2, path_count=link_count)
		ping_result = tools.ping_paths(remotes=remotes, paths=paths, duration_ms=30000, verbosity='verbose')

		traffic_ms = tools.millis() - start_ms
		traffic_end = tools.traffic(remotes)

		sysload_result = tools.sysload(remotes)

		software.clear(remotes)
		network.clear(remotes)

		# add data to csv file
		extra = (['node_count', 'traffic_ms', 'software_startup_ms'], [node_count, traffic_ms, software_startup_ms])
		tools.csv_update(csvfile, '\t', extra, (traffic_end - traffic_beg).getData(), ping_result.getData(), sysload_result)

for protocol in ['babel','bmx7']:
	with open(f"{prefix}custom-{protocol}.csv", 'w+') as csvfile:
		run(protocol, csvfile)

tools.stop_all_terminals()
