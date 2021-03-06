#!/usr/bin/env python3

"""
Copyright 2020 The Magma Authors.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import argparse
import ipaddress
import sys

from magma.common.rpc_utils import grpc_wrapper
from magma.subscriberdb.sid import SIDUtils
from orc8r.protos.common_pb2 import Void
from lte.protos.mobilityd_pb2 import AllocateIPRequest, \
    IPAddress, IPBlock, ReleaseIPRequest, RemoveIPBlockRequest, GWInfo
from lte.protos.mobilityd_pb2_grpc import MobilityServiceStub


@grpc_wrapper
def add_ip_block_handler(client, args):
    try:
        ipblock = ipaddress.ip_network(args.ipblock)
    except ValueError:
        print("Error: invalid IP block format: %s" % args.ipblock)
        return
    ipblock_msg = IPBlock()
    if ipblock.version == 4:
        ipblock_msg.version = IPBlock.IPV4
    else:
        print("Error: IP version %d is not supported yet" % ipblock.version)
        return
    ipblock_msg.net_address = ipblock.network_address.packed
    ipblock_msg.prefix_len = ipblock.prefixlen
    client.AddIPBlock(ipblock_msg)


@grpc_wrapper
def list_ipv4_blocks_handler(client, args):
    resp = client.ListAddedIPv4Blocks(Void())
    print("IPv4 Blocks Assigned:")
    for block_msg in resp.ip_block_list:
        ip = ipaddress.ip_address(block_msg.net_address)
        block = ipaddress.ip_network("%s/%d" % (ip, block_msg.prefix_len))
        print("\t%s" % block)


@grpc_wrapper
def allocate_ip_handler(client, args):
    try:
        sid_msg = SIDUtils.to_pb(args.sid)
    except ValueError:
        print("Invalid SubscriberID format: %s" % args.sid)
        return

    request = AllocateIPRequest()
    request.version = AllocateIPRequest.IPV4
    request.sid.CopyFrom(sid_msg)

    ip_msg = client.AllocateIPAddress(request)
    if ip_msg.version == IPAddress.IPV4:
        ip = ipaddress.IPv4Address(ip_msg.address)
        print("IPv4 address allocated: %s" % ip)
    elif ip_msg.version == IPAddress.IPV6:
        ip = ipaddress.IPv6Address(ip_msg.address)
        print("IPv6 address allocated: %s" % ip)
    else:
        print("Error: unknown IP version")


@grpc_wrapper
def release_ip_handler(client, args):
    try:
        sid_msg = SIDUtils.to_pb(args.sid)
    except ValueError:
        print("Error: invalid SubscriberID format: %s" % args.sid)
        return

    try:
        ip = ipaddress.ip_address(args.ip)
    except ValueError:
        print("Error: invalid IP format: %s" % args.ip)
        return

    ip_msg = IPAddress()
    if ip.version == 4:
        ip_msg.version = IPAddress.IPV4
    elif ip.version == 6:
        ip_msg.version = IPAddress.IPV6
    else:
        print("Error: unknown IP version")
        return

    ip_msg.address = ip.packed

    request = ReleaseIPRequest()
    request.sid.CopyFrom(sid_msg)
    request.ip.CopyFrom(ip_msg)

    client.ReleaseIPAddress(request)


@grpc_wrapper
def remove_ip_block_handler(client, args):
    ipblock_msgs = ()
    for ipblock in args.ipblocks:
        ipblock_msg = IPBlock()
        if ipblock.version == 4:
            ipblock_msg.version = IPBlock.IPV4
        else:
            print(
                "Error: IP version %d is not supported yet" % ipblock.version)
            return
        ipblock_msg.net_address = ipblock.network_address.packed
        ipblock_msg.prefix_len = ipblock.prefixlen
        ipblock_msgs += (ipblock_msg,)

    request = RemoveIPBlockRequest(ip_blocks=ipblock_msgs, force=args.force)
    remove_response = client.RemoveIPBlock(request)
    print("IPv4 Blocks Removed: ")
    for block_msg in remove_response.ip_blocks:
        ip = ipaddress.ip_address(block_msg.net_address)
        block = ipaddress.ip_network("%s/%d" % (ip, block_msg.prefix_len))
        print("\t%s" % block)


@grpc_wrapper
def list_allocated_ips_handler(client, args):
    list_blocks_resp = client.ListAddedIPv4Blocks(Void())
    for block_msg in list_blocks_resp.ip_block_list:
        ip = ipaddress.ip_address(block_msg.net_address)
        block = ipaddress.ip_network("%s/%d" % (ip, block_msg.prefix_len))
        print("IPs allocated from block %s:" % block)

        list_ips_resp = client.ListAllocatedIPs(block_msg)
        for ip_msg in list_ips_resp.ip_list:
            if ip_msg.version == IPAddress.IPV4:
                ip = ipaddress.IPv4Address(ip_msg.address)
            elif ip_msg.address == IPAddress.IPV6:
                ip = ipaddress.IPv6Address(ip_msg.address)
            else:
                print("Unsupported IP Version")
                continue
            print("\t%s" % ip)


@grpc_wrapper
def get_subscriber_ip_table_handler(client, args):
    table = client.GetSubscriberIPTable(Void())
    print("SID\t\tIP\t\tAPN")
    for entry in table.entries:
        ip = ipaddress.ip_address(entry.ip.address)
        print("%s\t%s\t%s" % (SIDUtils.to_str(entry.sid), ip, entry.apn))


@grpc_wrapper
def get_gw_info_handler(client, args):
    info = client.GetGatewayInfo(Void())
    ip = ipaddress.ip_address(info.ip.address)
    print("GW IP: %s" % ip)
    print("GW MAC: %s" % info.mac)


@grpc_wrapper
def set_gw_ip_addressk_handler(client, args):
    try:
        ipaddr = ipaddress.ip_address(args.gwip)
    except ValueError:
        print("Error: invalid IP address format: %s" % args.gwip)
        return

    gwinfo_msg = GWInfo()
    if ipaddr.version == 4:
        gwinfo_msg.ip.version = IPBlock.IPV4
    else:
        print("Error: IP version %d is not supported yet" % ipaddr.version)
        return

    gwinfo_msg.ip.address = ipaddr.packed
    gwinfo_msg.mac = ""
    client.SetGatewayInfo(gwinfo_msg)


def main():
    parser = argparse.ArgumentParser(
        description='Management CLI for MobilityService',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Add subcommands
    subparsers = parser.add_subparsers(title='subcommands', dest='cmd')

    # add_ip_block
    subparser = subparsers.add_parser(
        'add_ip_block', help='Add an IP block')
    subparser.add_argument('ipblock', help='Range of IP addresses,'
                           ' e.g.  "10.0.0.0/24"')
    subparser.set_defaults(func=add_ip_block_handler)

    # list_ipv4_blocks
    subparser = subparsers.add_parser(
        'list_ipv4_blocks', help='List assigned IPv4 blocks')
    subparser.set_defaults(func=list_ipv4_blocks_handler)

    # allocate_ip
    subparser = subparsers.add_parser(
        'allocate_ip', help='Allocate an IP address')
    subparser.add_argument('sid', help='Subscriber ID, e.g. "IMSI12345"')
    subparser.set_defaults(func=allocate_ip_handler)

    # release_ip
    subparser = subparsers.add_parser(
        'release_ip', help='Release an IP address')
    subparser.add_argument('sid', help='Subscriber ID, e.g. "IMSI12345"')
    subparser.add_argument('ip',
                           help='IP address to release, e.g. "192.168.1.1"')
    subparser.set_defaults(func=release_ip_handler)

    # remove_ip_blocks
    subparser = subparsers.add_parser(
        'remove_ip_blocks', help='Remove specified IP blocks')
    subparser.add_argument('-f', '--force',
                           action='store_true',
                           default=False,
                           help='If set, forcibly remove all IP blocks')
    subparser.add_argument('ipblocks',
                           action='store',
                           default=(),
                           nargs=argparse.REMAINDER,
                           type=ipaddress.ip_network,
                           help='The IP address block(s) to remove')
    subparser.set_defaults(func=remove_ip_block_handler)

    # list_allocated_ips
    subparser = subparsers.add_parser(
        'list_allocated_ips', help='List allocated IP addresses')
    subparser.set_defaults(func=list_allocated_ips_handler)

    # get_subscriber_table
    subparser = subparsers.add_parser(
        'get_subscriber_table', help='Get SubscriberID, IP table')
    subparser.set_defaults(func=get_subscriber_ip_table_handler)

    # GW info CLI
    # GetGatewayIPInfo
    subparser = subparsers.add_parser(
        'get_def_gw', help='Get default gw info')
    subparser.set_defaults(func=get_gw_info_handler)

    # SetGatewayIpAddress
    subparser = subparsers.add_parser(
        'set_def_gw', help='set default gw IP address')
    subparser.add_argument('gwip', help='Default gw IP addresses,'
                           ' e.g.  "10.0.0.1"')
    subparser.set_defaults(func=set_gw_ip_addressk_handler)

    # Parse the args
    args = parser.parse_args()
    if not args.cmd:
        parser.print_usage()
        sys.exit(1)

    # Execute the subcommand function
    args.func(args, MobilityServiceStub, 'mobilityd')


if __name__ == "__main__":
    main()
