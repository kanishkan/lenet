import xml.etree.ElementTree as ET
import re
from collections import Counter
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--adf', type=str, help='ADF file', required=True)
parser.add_argument('--log', type=str, help='Log file of training', required=True)
args = parser.parse_args()

"""# Parse ADF"""
tree = ET.parse(args.adf)
root = tree.getroot()

# Parse AS info (name, width, size)
as_info = {}  # Dict of name: {size:val}
for child in root.findall("address-space"):
    as_name = child.items()[0][1]  # Get name
    as_info[as_name] = {}

    as_info[as_name]["width"] = int(child.findtext("width"))
    as_info[as_name]["size"] = int(child.findtext("max-address"))

# print(as_info)

# Get connection count for each bus
rd_connections = [i.text for i in root.findall("socket/reads-from/bus")]
wr_connections = [i.text for i in root.findall("socket/writes-to/bus")]
rdwr_connections = rd_connections + wr_connections
bus_connections = dict(Counter(rdwr_connections))

# Parse Bus info (name, width)
bus_info = {}  # Dict of name: {size:val}
for child in root.findall("bus"):
    bus_name = child.items()[0][1]  # Get name
    bus_info[bus_name] = {}

    bus_info[bus_name]["width"] = int(child.findtext("width"))
    bus_info[bus_name]["connections"] = int(bus_connections[bus_name])

# print(bus_info)

# Parse FU info (name, address-space, instr)
fu_info = {}  # Dict of name: {size:val}
for child in root.findall("function-unit"):
    fu_name = child.items()[0][1]  # Get name
    fu_info[fu_name] = {}

    fu_addrspace = child.findtext("address-space")
    if (fu_addrspace != ''):
        fu_info[fu_name]['as'] = fu_addrspace
    fu_info[fu_name]["instr"] = [i.findtext('name') for i in child.findall('operation')]

# print(fu_info)

# Parse RF info (name, width, size, ports [rd+wr])
rf_info = {}  # Dict of name: {size:val}
for child in root.findall("register-file"):
    rf_name = child.items()[0][1]  # Get name
    rf_info[rf_name] = {}

    rf_info[rf_name]["width"] = int(child.findtext("width"))
    rf_info[rf_name]["size"] = int(child.findtext("size"))
    rf_info[rf_name]["ports"] = int(len(child.findall('port')))

# print(rf_info)

"""# Parse ttasim stats"""
ttasim_log = open(args.log, 'r').read()

# Bus stats
headless = ttasim_log.split("buses:\n\n")[1]
split_sockets = headless.split("sockets:\n\n")
bus_stat = split_sockets[0]

# FU stats
fu_split = split_sockets[1].split("operations executed in function units:\n\n")[1]
op_split = fu_split.split("operations:\n\n")
fu_stat = op_split[0]

# RF Access
rf_split = op_split[1].split("register accesses:\n\n")[1]
imm_split = rf_split.split("immediate unit accesses:\n\n")
rf_stat = imm_split[0]

"""## Parse stats to dict"""

# Bus stats
bus_writes = {}
lines = bus_stat.split("\n")
bus_lines = [line for line in lines if line.strip()]
for l in bus_lines:
    bus_name = l.split(" ")[0]
    bus_writes[bus_name] = int(re.findall(r'(\d+) writes', l)[0])

# print(bus_writes)

# RF stats
rf_reads = {}
rf_writes = {}
lines = rf_stat.split("\n\n")
rf_lines = [line for line in lines if line.strip()]
for l in rf_lines:
    rf_name = l.split(":\n")[0]
    rf_total_stats = l.split("TOTAL")[1]
    rf_reads[rf_name] = int(re.findall(r'(\d+) reads', rf_total_stats)[0])
    rf_writes[rf_name] = int(re.findall(r'(\d+) writes', rf_total_stats)[0])
# print("reads:"); print(rf_reads)
# print("writes:"); print(rf_writes)

# FU stats
fu_ops = {}
lines = fu_stat.split("\n\n")
per_fu_stat = [line for line in lines if line.strip()]
for fu in per_fu_stat:
    fu_name = fu.split(":\n")[0]
    op_split = fu.split(":\n")[1].split("\n")
    fu_ops[fu_name] = {}
    for op in op_split:
        op_name = op.split(" ")[0]
        if (op_name == "TOTAL"):
            continue
        fu_ops[fu_name][op_name] = int(re.findall(r'(\d+) executions', op)[0])

# print(fu_ops)


### Energy model
# it support lambda functions that takes the width of the operation, e.g. add64 to increase energy number/op
# also for loads/stores we can take into account the memory size. Parameter s in this case
# 32-bit operands!

import math

base_memory_size = 65535/2
base_rf_size = 32 * 5
base_energy_per_op = {
    # 1pj/read
    'ld': lambda op_width, size: 2.431659318662712 * op_width / 32 * math.sqrt(size / base_memory_size),
    'ldu': lambda op_width, size: 2.431659318662712 * op_width / 32 * math.sqrt(size / base_memory_size),  # ==ld
    'st': lambda op_width, size: 2.2368848480025094 * op_width / 32 * math.sqrt(size / base_memory_size),

    'add': lambda width: 1.281374803449883 * width / 32,
    'sub': lambda width: 1.2921415851154878 * width / 32,
    'mul': lambda width: 22.506646009287152 * (width / 32) ** 1.25,
    'mac': lambda width: 23.288020812737035 * (width / 32) ** 1.25,

    'eq': 0.9353093596016868,
    'gt': 1.1899963143931334,
    'gtu': 1.1799530584563398,
    'and': 1.30367578650223,
    'ior': 1.2737583845954128,
    'xor': 1.4277455280801707,
    'shl': 1.3038434338600136,
    'shr': 1.339878498206208,
    'shru': 1.339878498206208,

    'jump': 1.2959699620656189,
    'call': 1.2959699620656189,
    'ecc': 0,
    'lcc': 0,

    'imm': 0.6189188656912776,  # need to check what immediate actually is in TTA

    'rf_read': lambda op_width, size, ports: 0.8936382686651276 * op_width / 32 * math.sqrt(size / base_rf_size) * (
            ports + 1) / 2,
    'rf_write': lambda op_width, size, ports: 1.4568385799211798 * op_width / 32 * math.sqrt(size / base_rf_size) * (
            ports + 1) / 2,

    'bus_write': lambda width, connections: 0.5 * width / 32 * (connections / 15) ** 2,
}

rf_dict = {}
for name, num in rf_reads.items():
    rf_dict[name] = {'rf_read': num, 'rf_write': rf_writes[name]}
bus_dict = {}
for name, num in bus_writes.items():
    bus_dict[name] = {'bus_write': num}

total_op_energy = 0
item_energy = {}
item_area = {}
for name, v in as_info.items():
    item_area[f'MEM_{name}'] = v['width'] * v['size'] * 0.25

item_ops = {**fu_ops, **rf_dict, **bus_dict}
for fu_name, ops in item_ops.items():
    item_energy[fu_name] = {}
    item_area[fu_name] = 0

    for op_name_orig, num in ops.items():
        item_energy[fu_name][op_name_orig] = 0
        area_factor = 137
        op_width = ''.join(list(filter(str.isdigit, op_name_orig.lower())))  # get number from string
        op_width = int(op_width) if op_width else 32  # default 32bits
        op_name = op_name_orig.replace(str(op_width), '').lower()  # remove width from operation name

        # energy
        if callable(base_energy_per_op[op_name]):
            if op_name in ('ld', 'ldu', 'st'):
                energy = num * base_energy_per_op[op_name](op_width, as_info[fu_info[fu_name]['as']]['width'] *
                                                           as_info[fu_info[fu_name]['as']]['size'])  # calculate energy
            elif op_name in ('rf_read', 'rf_write'):
                energy = num * base_energy_per_op[op_name](op_width,
                                                           rf_info[fu_name]['width'] * rf_info[fu_name]['size'],
                                                           rf_info[fu_name]['ports'])  # calculate energy
            elif op_name in ('bus_write',):
                energy = num * base_energy_per_op[op_name](bus_info[fu_name]['width'],
                                                           bus_info[fu_name]['connections'])  # calculate energy

            else:
                energy = num * base_energy_per_op[op_name](op_width)  # calculate energy
        else:
            energy = num * base_energy_per_op[op_name]  # calculate energy

        # area
        if op_name in ('ld', 'ldu', 'st'):
            area_factor /= 2
        elif op_name in ('rf_read', 'rf_write'):
            area_factor = rf_info[fu_name]['width'] * rf_info[fu_name]['size'] * (rf_info[fu_name]['ports'] + 1) / 2 * \
                          0.3

        elif op_name in ('bus_write',):
            area_factor = bus_info[fu_name]['width'] / 32 * (bus_info[fu_name]['connections'] / 15) ** 1.5 * 35 * 137
        elif op_name in ('mul', 'mac'):
            area_factor *= op_width / 32 * 25
        else:
            area_factor *= op_width / 32

        total_op_energy += energy
        item_energy[fu_name][op_name_orig] += energy
        item_area[fu_name] = max(item_area[fu_name], area_factor)

print(f'Total energy consumed {total_op_energy:.0f} pJ')
print('Energy breakdown per unit:')
for name, energy_per_op in item_energy.items():
    e_total = sum(energy_per_op.values())
    print(f' Unit "{name}": {e_total:.0f} pJ')

print('Energy breakdown per operation:')
for fu_name, energy_per_op in item_energy.items():
    print(f' Unit "{fu_name}":')
    for op_name, energy in energy_per_op.items():
        print(f'  Op "{op_name}": {energy:.0f} pJ')

total_area = sum(item_area.values())
print(f'Total area: {total_area:.3f} um2')
for fu_name, area in item_area.items():
    print(f' Unit "{fu_name}": {area:.3f} um2')
