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

from __future__ import absolute_import, division, print_function, \
    unicode_literals

from abc import ABC, abstractmethod

from ipaddress import ip_address, ip_network
from typing import List

from magma.mobilityd.ip_descriptor import IPDesc, IPType

DEFAULT_IP_RECYCLE_INTERVAL = 15


class IPAllocator(ABC):

    @abstractmethod
    def add_ip_block(self, ipblock: ip_network):
        ...

    @abstractmethod
    def remove_ip_blocks(self, *ipblocks: List[ip_network],
                         force: bool) -> List[ip_network]:
        ...

    @abstractmethod
    def list_added_ip_blocks(self) -> List[ip_network]:
        ...

    @abstractmethod
    def list_allocated_ips(self, ipblock: ip_network) -> List[ip_address]:
        ...

    @abstractmethod
    def alloc_ip_address(self, sid: str) -> IPDesc:
        ...

    @abstractmethod
    def release_ip(self, ip_desc: IPDesc):
        ...


class OverlappedIPBlocksError(Exception):
    """ Exception thrown when a given IP block overlaps with existing ones
    """
    pass


class IPBlockNotFoundError(Exception):
    """ Exception thrown when listing an IP block that is not found in the ip
    block list
    """
    pass


class NoAvailableIPError(Exception):
    """ Exception thrown when no IP is available in the free list for an ip
    allocation request
    """
    pass


class DuplicatedIPAllocationError(Exception):
    """ Exception thrown when an IP has already been allocated to a UE
    """
    pass
