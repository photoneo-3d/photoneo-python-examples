#!/usr/bin/env python
import argparse
import random
import socket
import struct
import sys
import textwrap
import time
from typing import Any, Iterable, Iterator, List, NamedTuple, Optional, Union

DISCOVERY_TIME = 1.1  # seconds


class Error(Exception):
    pass


class Gvcp:
    PORT: int = 3956

    ACK_REQUIRED: int = 0b00000001
    ALLOW_DISCOVERY_BROADCAST_ACK: int = 0b00010000

    MAGIC = 0x42
    DISCOVERY_CMD = 0x0002
    DISCOVERY_ACK = 0x0003
    FORCEIP_CMD = 0x0004
    FORCEIP_ACK = 0x0005
    READREG_CMD = 0x0080
    READREG_ACK = 0x0081
    WRITEREG_CMD = 0x0082
    WRITEREG_ACK = 0x0083

    GEV_STATUS_SUCCESS = 0x0000

    NETWORK_INTERFACE_CONFIGURATION = 0x0014
    PERSISTENT_DEFAULT_GATEWAY = 0x066C
    PERSISTENT_IP_ADDRESS = 0x064C
    PERSISTENT_SUBNET_MASK = 0x065C
    CCP_REG_ADDRESS = 0x0A00

    CCP_CONTROL_ACCESS = 0x02

    LOCAL_LINK_ADDRESS = 4
    DHCP = 2
    PERSISTENT_IP = 1

    @staticmethod
    def cmd(flag: int, command: int, req_id: int, data: bytes) -> bytes:
        """Create the gvcp command packet with data."""
        length = len(data)
        return struct.pack(">BBHHH", Gvcp.MAGIC, flag, command, length, req_id) + data

    @staticmethod
    def discovery_cmd(req_id: int, allow_broadcast_ack: bool) -> bytes:
        """Create the discovery packet."""
        flag = Gvcp.ACK_REQUIRED
        if allow_broadcast_ack:
            flag |= Gvcp.ALLOW_DISCOVERY_BROADCAST_ACK

        return Gvcp.cmd(flag, Gvcp.DISCOVERY_CMD, req_id, bytes())

    @staticmethod
    def forceip_cmd(
        req_id: int,
        mac: bytes,
        ip: int,
        subnet_mask: int,
        gw: int = 0,
        ack_required=False,
    ) -> bytes:
        """Create a FORCEIP packet."""
        flag = Gvcp.ACK_REQUIRED if ack_required else 0
        mac_high, mac_low = struct.unpack(">HI", mac)
        # fmt: off
        data = struct.pack(
            ">HHIIIIIIIIIIIII",
            0, mac_high, mac_low,
            0, 0, 0, ip,
            0, 0, 0, subnet_mask,
            0, 0, 0, gw
        )
        # fmt: on
        return Gvcp.cmd(flag, Gvcp.FORCEIP_CMD, req_id, data)

    @staticmethod
    def readreg_cmd(req_id: int, addresses: Iterable[int]) -> bytes:
        data = b"".join(struct.pack(">I", addr) for addr in addresses)
        return Gvcp.cmd(Gvcp.ACK_REQUIRED, Gvcp.READREG_CMD, req_id, data)

    class Assignment(NamedTuple):
        address: int
        value: int

        @classmethod
        def parse(cls, assignment: str) -> "Gvcp.Assignment":
            address, value = (int(x, 0) for x in assignment.split("=", 2))
            return cls(address, value)

    @staticmethod
    def writereg_cmd(req_id: int, assignments: Iterable[Assignment]) -> bytes:
        data = b"".join(struct.pack(">II", a.address, a.value) for a in assignments)
        return Gvcp.cmd(Gvcp.ACK_REQUIRED, Gvcp.WRITEREG_CMD, req_id, data)

    class AckError(Exception):
        pass

    class AckMessage(NamedTuple):
        status: int
        acknowledge: int
        length: int
        ack_id: int
        payload: bytes = b""

    @staticmethod
    def parse_ack(data: bytes) -> "Gvcp.AckMessage":
        if len(data) < 8:
            raise Gvcp.AckError("Packet too small")
        status, ack, length, ack_id = struct.unpack(">HHHH", data[0:8])
        return Gvcp.AckMessage(status, ack, length, ack_id, data[8:])

    @staticmethod
    def verify_ack(data: bytes, expected_ack: int, req_id: int) -> "Gvcp.AckMessage":
        ack = Gvcp.parse_ack(data)  # throws AckError
        if ack.acknowledge != expected_ack:
            raise Gvcp.AckError(
                f"Wrong acknowledge type ({ack.acknowledge:04x} instead of {expected_ack:04x})"
            )
        if ack.ack_id != req_id:
            raise Gvcp.AckError(f"Wrong ack_id ({ack.ack_id} instead of {req_id})")
        return ack

    @staticmethod
    def parse_readreg_ack(ack: "Gvcp.AckMessage") -> List[int]:
        payload = ack.payload
        if len(payload) % 4 != 0:
            raise Gvcp.AckError(f"Wrong payload size ({len(payload)}) for READREG_ACK")
        return [struct.unpack(">I", payload[i : i + 4])[0] for i in range(0, len(payload), 4)]

    @staticmethod
    def parse_writereg_ack(ack: "Gvcp.AckMessage") -> int:
        payload = ack.payload
        if len(payload) != 4:
            raise Gvcp.AckError(f"Wrong payload size ({len(payload)}) for WRITEREG_ACK")
        reserved, index = struct.unpack(">HH", payload)
        return index

    class DiscoveryEntry(NamedTuple):
        serial: str
        ip: str
        mac: bytes

        def __repr__(self):
            return f"{self.serial:16} {self.ip:16} {':'.join('%02x' % x for x in self.mac)}"

    @staticmethod
    def parse_discovery_ack(ack: "Gvcp.AckMessage") -> DiscoveryEntry:
        data = ack.payload
        mac = data[10:16]
        ip = data[9 * 4 : 9 * 4 + 4]
        ip_string = ip_to_str(ip)
        serial_offset = 18 * 4 + 3 * 32 + 48
        serial = data[serial_offset : serial_offset + 16].rstrip(b"\x00").decode("utf-8")
        return Gvcp.DiscoveryEntry(serial=serial, ip=ip_string, mac=mac)

    @staticmethod
    def open_broadcast_socket_(bind_address: str, port: int) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind_address, port))
        return sock

    def __init__(self) -> None:
        self.socket: Optional[socket.socket] = None
        self.req_id = random.randint(1, 65534)

    def __enter__(self) -> "Gvcp":
        return self

    def __exit__(self, typ, value, traceback) -> None:
        self.close_broadcast_socket()

    def get_req_id(self) -> int:
        tmp = self.req_id
        self.req_id += 1
        return tmp

    def open_broadcast_socket(self) -> socket.socket:
        if self.socket is None:
            self.socket = self.open_broadcast_socket_("0.0.0.0", Gvcp.PORT)
        return self.socket

    def close_broadcast_socket(self) -> None:
        if self.socket is not None:
            self.socket.close()
            self.socket = None

    def send_broadcast(self, data: bytes) -> int:
        """Send a broadcast message on all interfaces.

        Note that we should open sockets on all interfaces and then listen
        on all of them (because packets won't be delivered to the 0.0.0.0 socket
        then) but because waiting for packets from multiple interfaces gets messy,
        we just open, send and then immediately close these per-interface sockets,
        so that incoming packets are received on the 0.0.0.0 socket.

        Yes, this is a hack and introduces a small race window... but...
        The alternative is to correctly handle simultaneous receiving from
        multiple sockets...
        """

        def local_addresses_windows() -> List[str]:
            """Get ip addresses of local interfaces, one per interface.
            Note: this works only on windows, linux would return only localhost addresses ;)
            """
            try:
                return [
                    a[4][0]
                    for a in socket.getaddrinfo(socket.gethostname(), None, family=socket.AF_INET)
                    if not a[4][0].startswith("127.")
                ]
            except socket.gaierror as e:
                raise Error(f"Failed to get list of interface addresses: {e}")

        def local_addresses_linux() -> List[str]:
            """Get ip addresses of local interfaces, one per interface.
            Note: this works only on linux
            """
            ip_command = """
                if which ip  ; then  ip -4 ad ; else  ifconfig ; fi | awk '
                    $1=="inet" && isFirst { gsub("/.*", "", $2); print $2; isFirst=0 }
                    $1 ~ /:/ { isFirst=1; }
                '
            """
            import subprocess

            output = subprocess.run(ip_command, shell=True, capture_output=True).stdout.decode(
                "utf-8"
            )
            ips = (line.strip() for line in output.split("\n"))
            return [ip for ip in ips if ip and not ip.startswith("127.")]

        def local_addresses() -> List[str]:
            """Get ip addresses of local interfaces, one per interface."""
            if sys.platform == "win32":
                return local_addresses_windows()
            elif sys.platform == "linux":
                return local_addresses_linux()
            else:
                raise Error(f"Don't know how to enumerate interface addresses on {sys.platform}")

        if self.socket is None:
            self.open_broadcast_socket()
            assert self.socket is not None

        try:
            addresses = local_addresses()
            if len(addresses) == 0:
                raise Error("No interface addresses found, don't know where to send packets")
        except Error as e:
            print(f"Error: {e}", file=sys.stderr)
            print("Using only default interface", file=sys.stderr)
            return self.socket.sendto(data, ("255.255.255.255", Gvcp.PORT))

        last = 0
        for address in addresses:
            sock = self.open_broadcast_socket_(address, Gvcp.PORT)
            try:
                last = sock.sendto(data, ("255.255.255.255", Gvcp.PORT))
            finally:
                sock.close()

        return last

    def receive_ack(self, expected_ack: int, req_id: int, timeout: float = 1) -> "Gvcp.AckMessage":
        if self.socket is None:
            self.open_broadcast_socket()
            assert self.socket is not None

        deadline = time.perf_counter() + timeout
        while time.perf_counter() < deadline:
            self.socket.settimeout(deadline - time.perf_counter())
            try:
                data, _ = self.socket.recvfrom(2048)
            except socket.timeout:
                raise Error(
                    f"Failed to receive acknowledge for {expected_ack} with req_id {req_id}"
                )
            try:
                ack = Gvcp.verify_ack(data, expected_ack, req_id)
                return ack  # TODO also source address?
            except Gvcp.AckError as e:
                print(f"Ignoring wrong acknowledge message: {e}", file=sys.stderr)
                continue
        raise Error(f"Acknowledge not received for {expected_ack} with req_id {req_id}")

    class ReadregResult(NamedTuple):
        status: int
        values: List[int]

    def readreg(self, target: Any, addresses: Iterable[int]) -> ReadregResult:
        """Send a single READREG command and wait for the answer.

        Note: while this allows reading multiple registers in one command, the device capabilities
        should be checked to see if it supports this feature.
        """
        if self.socket is None:
            self.open_broadcast_socket()
            assert self.socket is not None
        req_id = self.get_req_id()
        cmd = Gvcp.readreg_cmd(req_id, addresses)
        self.socket.sendto(cmd, target)
        ack = self.receive_ack(Gvcp.READREG_ACK, req_id)
        values = Gvcp.parse_readreg_ack(ack)
        return Gvcp.ReadregResult(ack.status, values)

    class WriteregResult(NamedTuple):
        status: int
        idx: int

    def writereg(self, target: Any, assignments: Iterable[Assignment]) -> WriteregResult:
        """Send a single WRITEREG command and wait for the answer.

        Note: while this allows writing  multiple registers in one command, the device capabilities
        should be checked to see if it supports this feature.
        """
        if self.socket is None:
            self.open_broadcast_socket()
            assert self.socket is not None
        req_id = self.get_req_id()
        cmd = Gvcp.writereg_cmd(req_id, assignments)
        self.socket.sendto(cmd, target)
        ack = self.receive_ack(Gvcp.WRITEREG_ACK, req_id)
        index = Gvcp.parse_writereg_ack(ack)
        return Gvcp.WriteregResult(ack.status, index)

    def forceip(
        self, mac: bytes, ip: int, subnet_mask: int, gw: int = 0, ack_required=False
    ) -> int:
        req_id = self.get_req_id()
        forceip_packet = Gvcp.forceip_cmd(
            req_id, mac, ip, subnet_mask, gw, ack_required=ack_required
        )
        self.send_broadcast(forceip_packet)
        if ack_required:
            ack = self.receive_ack(Gvcp.FORCEIP_ACK, req_id, timeout=60.0)
            return ack.status
        else:
            return Gvcp.GEV_STATUS_SUCCESS

    def discovery(self, allow_broadcast_ack: bool = True) -> Iterator[DiscoveryEntry]:
        sock = self.open_broadcast_socket()
        req_id = self.get_req_id()
        discovery_packet = Gvcp.discovery_cmd(req_id, allow_broadcast_ack=allow_broadcast_ack)
        self.send_broadcast(discovery_packet)

        deadline = time.perf_counter() + DISCOVERY_TIME
        while time.perf_counter() < deadline:
            sock.settimeout(deadline - time.perf_counter())
            try:
                data, _ = sock.recvfrom(2048)
            except socket.timeout:
                continue

            try:
                ack = Gvcp.verify_ack(data, Gvcp.DISCOVERY_ACK, req_id)
            except Gvcp.AckError as e:
                print(f"Ignoring non discovery packets: {e}", file=sys.stderr)
                continue
            yield Gvcp.parse_discovery_ack(ack)


def mac_from_str(mac: str) -> bytes:
    return bytes.fromhex(mac.replace(":", ""))


def mac_to_str(mac: bytes) -> str:
    return ":".join("%02x" % x for x in mac)


def ip_from_str(ip: str) -> int:
    return struct.unpack(">I", bytes(int(x) for x in ip.split(".")))[0]


def ip_to_str(ip: Union[bytes, int]) -> str:
    if type(ip) is bytes:
        return ".".join(str(x) for x in ip)
    else:
        return ip_to_str(struct.pack(">I", ip))


def usage():
    print(
        textwrap.dedent(
            """\
            Usage:
                forceip.py d[iscovery] [-B]
                forceip.py f[orceip] [-a] mac [ip [subnet [gw]]]
                forceip.py r[eadreg] device_ip address [address ...]
                forceip.py w[writereg] device_ip address=value [address=value ...]
                forceip.py p[ersist] mode [dhcp/static] ...
                forceip.py s[et] mode [static] ...

            The first invocation sends a discovery command and prints responses.
            The second invocation sends a FORCEIP command to a specific device.
            The third invocation issues a READREG command to a device.
            The fourth invocation issues a WRITEREG command to a device.
            The fifth invocation configures  the device to use the appropriate
            IP configuration mode.
            The sixth invocation discovers the device, changes it's ip to one on the
            current subnet and then configures it to use the appropriate
            IP configuration mode.

            Use  "forceip.py subcommand --help" to see more detailed parameter information
            for each subcommand.


            Options:
                -B  Disallow broadcast of discovery response.
                -a  Require acknowledge for FORCEIP command.

            Parameters:
                mac     MAC address of the device.
                ip      The new static IP to set.
                subnet  The new subnet.
                gw      The new gateway (if any).

            Mode:
                mode    IP configuration mode.

            If the forceip command is invoked without an ip (and thus without subnet and gateway)
            the device should reconfigure its IP configuration as per its stored settings.

            You can use this tool to change IP configuration mode:
            - Set persistent DHCP IP configuration mode, where <device_address> stands for IPv4
             address or device hostname.

                forceip.py persist dhcp <device_address>

            - Set persistent static IP configuration mode, where <device_address> stands for IPv4
             address or device hostname.

                forceip.py persist static <device_address> <new_static_ip> <new_subnet>.

            - Set a persistent static IP mode for a device with a different subnet,
             where <device_address> stands for the device's serial number, by first
             discovering the device, then making it visible in our subnet through the
             'forceip' command to set a new static IP address, and finally, ensuring
             that this configuration is set as persistent.

                forceip.py set static <device_sn> <new_static_ip> <new_subnet>.

            After making changes to IP configuration, a device reset may be required
            to apply the changes.
            """
        )
    )
    sys.exit(1)


discovery_parser = argparse.ArgumentParser()
discovery_parser.add_argument("discovery")
discovery_parser.add_argument("-B", action="store_false", dest="allow_broadcast_ack")

forceip_parser = argparse.ArgumentParser()
forceip_parser.add_argument("forceip")
forceip_parser.add_argument("-a", action="store_true", dest="ack_required")
forceip_parser.add_argument("mac")
forceip_parser.add_argument("ip", nargs="?")
forceip_parser.add_argument("subnet_mask", nargs="?")
forceip_parser.add_argument("gw", nargs="?")

readreg_parser = argparse.ArgumentParser()
readreg_parser.add_argument("readreg")
readreg_parser.add_argument("ip")
readreg_parser.add_argument("addresses", metavar="address", type=lambda x: int(x, 0), nargs="+")

writereg_parser = argparse.ArgumentParser()
writereg_parser.add_argument("writereg")
writereg_parser.add_argument("ip")
writereg_parser.add_argument(
    "assignments", metavar="address=value", type=Gvcp.Assignment.parse, nargs="+"
)


def add_static_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("ip")
    parser.add_argument("subnet_mask")
    parser.add_argument("gw", nargs="?")


persist_parser = argparse.ArgumentParser()
persist_parser.add_argument("persist")
persist_subparser = persist_parser.add_subparsers(title="mode", dest="mode", required=True)

persist_dhcp_parser = persist_subparser.add_parser("dhcp", help="Set DHCP IP configuration mode")
persist_dhcp_parser.add_argument("device_address")

persist_static_parser = persist_subparser.add_parser(
    "static", help="Set static IP configuration mode"
)
persist_static_parser.add_argument("device_address")
add_static_options(persist_static_parser)

set_parser = argparse.ArgumentParser()
set_parser.add_argument("set")
set_subparser = set_parser.add_subparsers(title="mode", dest="mode", required=True)

set_static_parser = set_subparser.add_parser(name="static", help="Set static IP configuration mode")
set_static_parser.add_argument("device_address", metavar="Device Serial")
add_static_options(set_static_parser)


def parse_ip(ip: str, error_message: str = "Wrong ip") -> int:
    try:
        int_ip = ip_from_str(ip)
    except Exception as e:
        print(f"{error_message} {ip!r}: {e}")
        print()
        usage()
    return int_ip


def parse_subnet_mask(mask: str) -> int:
    subnet_mask = parse_ip(mask, error_message="Wrong subnet mask")
    if "01" in bin(subnet_mask):
        print(f"Invalid subnet mask {mask} ({bin(subnet_mask)})")
        print()
        usage()
    return subnet_mask


def discovery_command() -> None:
    """Multicast a discovery command and process answers."""
    args = discovery_parser.parse_args()
    with Gvcp() as gvcp:
        for d in gvcp.discovery(allow_broadcast_ack=args.allow_broadcast_ack):
            print(d)


def forceip_command() -> None:
    """Send a forceip command to the device."""

    args = forceip_parser.parse_args()
    try:
        mac = mac_from_str(args.mac)
    except Exception as e:
        print(f"Wrong mac {args.mac!r}: {e}")
        print()
        usage()

    if len(mac) != 6:
        print(f"Wrong mac {args.mac!r}")
        print()
        usage()

    ip: int = 0
    subnet_mask: int = 0
    gw: int = 0

    if args.ip is not None:
        ip = parse_ip(args.ip)

    if args.subnet_mask is not None:
        subnet_mask = parse_subnet_mask(args.subnet_mask)

    if args.gw is not None:
        gw = parse_ip(args.gw, error_message="Wrong default gateway address")

    print(f"mac={mac_to_str(mac)}")
    print(f"ip={ip_to_str(ip)}")
    print(f"subnet_mask={ip_to_str(subnet_mask)}")
    print(f"gw={ip_to_str(gw)}")

    with Gvcp() as gvcp:
        gvcp.forceip(mac=mac, ip=ip, subnet_mask=subnet_mask, gw=gw)


def readreg_command() -> None:
    """Send a readreg command to the device and print the result."""

    args = readreg_parser.parse_args()

    with Gvcp() as gvcp:
        # TODO should check capability for multi-register reads,
        # right now this is left for the user to invoke appropriately :)
        readreg_ack = gvcp.readreg((args.ip, Gvcp.PORT), args.addresses)
        print(f"status: 0x{readreg_ack.status:x}")
        for value in readreg_ack.values:
            print(f"{value:08x}")


def writereg_command(args=None) -> None:
    """Send a writereg command to the device."""

    if not args:
        args = writereg_parser.parse_args()

    with Gvcp() as gvcp:
        # TODO split the writes to one per write command (both because of the initial CCP write
        # and because we don't care about checking the capability for multi-register writes)
        writereg_ack = gvcp.writereg((args.ip, Gvcp.PORT), args.assignments)
        print(f"status: 0x{writereg_ack.status:x}")
        print(f"index: {writereg_ack.idx}")


def evaluate_writereg(res) -> None:
    status = res.status
    if status == Gvcp.GEV_STATUS_SUCCESS:
        print(f"Operation with id {res.idx} finished. [OK]")
    else:
        print(f"Operation with id: {res.idx} finished. [FAILED]")


def generate_static_assignments(gvcp: Gvcp, args: argparse.Namespace) -> List[Gvcp.Assignment]:
    assignments = [gvcp.Assignment(address=Gvcp.CCP_REG_ADDRESS, value=Gvcp.CCP_CONTROL_ACCESS)]
    if args.ip is not None:
        ip = parse_ip(args.ip)
        assignments.append(gvcp.Assignment(address=Gvcp.PERSISTENT_IP_ADDRESS, value=ip))
    if args.subnet_mask is not None:
        subnet_mask = parse_subnet_mask(args.subnet_mask)
        assignments.append(gvcp.Assignment(address=Gvcp.PERSISTENT_SUBNET_MASK, value=subnet_mask))
    if args.gw is not None:
        gw = parse_ip(args.gw, error_message="Wrong default gateway address")
        assignments.append(gvcp.Assignment(address=Gvcp.PERSISTENT_DEFAULT_GATEWAY, value=gw))
    assignments.append(
        gvcp.Assignment(
            address=Gvcp.NETWORK_INTERFACE_CONFIGURATION,
            value=Gvcp.LOCAL_LINK_ADDRESS + Gvcp.PERSISTENT_IP,
        )
    )
    return assignments


def persist_command() -> None:
    args = persist_parser.parse_args()
    if args.mode == "dhcp":
        with Gvcp() as gvcp:
            assignments = [
                gvcp.Assignment(address=Gvcp.CCP_REG_ADDRESS, value=Gvcp.CCP_CONTROL_ACCESS),
                gvcp.Assignment(
                    address=Gvcp.NETWORK_INTERFACE_CONFIGURATION,
                    value=Gvcp.LOCAL_LINK_ADDRESS + Gvcp.DHCP,
                ),
            ]
            writereg_ack = gvcp.writereg((args.device_address, Gvcp.PORT), assignments)
            evaluate_writereg(writereg_ack)
    elif args.mode == "static":
        with Gvcp() as gvcp:
            assignments = generate_static_assignments(gvcp, args)
            writereg_ack = gvcp.writereg((args.device_address, Gvcp.PORT), assignments)
            evaluate_writereg(writereg_ack)
    else:
        print("Unknown option")


def set_command() -> None:
    args = set_parser.parse_args()

    def find_by_id(x) -> bool:
        return x.serial == args.device_address

    with Gvcp() as gvcp:
        # Discovery
        dev = next((d for d in gvcp.discovery() if find_by_id(d)), None)
        if dev is None:
            raise Error(f"No devices found with id: {args.device_address}")

        ip: int = 0
        subnet_mask: int = 0
        gw: int = 0

        if args.ip is not None:
            ip = parse_ip(args.ip)
        if args.subnet_mask is not None:
            subnet_mask = parse_subnet_mask(args.subnet_mask)
        if args.gw is not None:
            gw = parse_ip(args.gw, error_message="Wrong default gateway address")

        # Make visible on subnet
        gvcp.forceip(mac=dev.mac, ip=ip, subnet_mask=subnet_mask, gw=gw, ack_required=True)

        # Set static
        assignments = generate_static_assignments(gvcp, args)
        print("Sending writereg command")
        writereg_ack = gvcp.writereg((args.ip, Gvcp.PORT), assignments)
        evaluate_writereg(writereg_ack)


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            if sys.argv[1] in ("-h", "--help"):
                usage()
            elif "discovery".startswith(sys.argv[1]):
                discovery_command()
            elif "readreg".startswith(sys.argv[1]):
                readreg_command()
            elif "writereg".startswith(sys.argv[1]):
                writereg_command()
            elif "persist".startswith(sys.argv[1]):
                persist_command()
            elif "set".startswith(sys.argv[1]):
                set_command()
            elif "forceip".startswith(sys.argv[1]):
                forceip_command()
            else:
                usage()
        else:
            usage()
    except Error as e:
        print(f"Error: {e}")
