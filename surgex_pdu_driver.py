import socket
import struct

__version__ = "1.0.0"
__author__ = "Matthew Franklin"


class SurgeX_DxPClient:
    """
    DxP client for SurgeX Switched PDU's

    Built and tested with a Surgex SA-82-AR PDU

    See updates and license at:
    github.com/mefranklin6/SurgeX-PDU-DxP-Client
    """

    # Number of controlled outlets for each model
    # Add more models as needed
    MODEL_OUTLETS = {
        "SA-82-AR": 1,  # Two outlets but only one relay for both
    }

    DEFAULT_PORT = 9100  # DxP Port

    COMMANDS = {
        "CMD_IO": 0x03,
        "IO_CHANGE_RELAY": 0x01,
        "IO_GET_RELAYS": 0x04,
        "STATE_ENERGIZE": 0x01,
        "STATE_RELAX": 0x00,
    }

    HELLO_MSG = b"hello-000\x00"
    HEADER_PREFIX = "<B21s21sBBH"

    def __init__(
        self,
        host: str,
        model: str,
        port: int = DEFAULT_PORT,
        username: str = "",
        password: str = "",
        timeout: float = 3.0,  # Seconds
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.uName = username.encode("ascii")[:20].ljust(21, b"\x00")
        self.pwd = password.encode("ascii")[:20].ljust(21, b"\x00")
        self.sock = None
        self.seq = 0
        if model not in self.MODEL_OUTLETS.keys():
            raise ValueError(
                f"Unsupported model: {model}. Supported models: {list(self.MODEL_OUTLETS.keys())}"
            )
        self.relay_count = self.MODEL_OUTLETS[model]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._disconnect()

    def _hello(self):
        try:
            self.sock = socket.create_connection((self.host, self.port), self.timeout)
            self.sock.settimeout(self.timeout)
            msg = self.HELLO_MSG
            self.sock.sendall(msg)
            seqb = self.sock.recv(2)
            if len(seqb) != 2:
                print(f"Handshake failed: got {len(seqb)} bytes, expected 2")
            self.seq = struct.unpack("<H", seqb)[0]
        except (socket.timeout, socket.error, ConnectionError) as e:
            self._disconnect()
            print(f"Failed to connect to PDU at {self.host}:{self.port}: {e}")
        except Exception as e:
            self._disconnect()
            print(f"Unexpected error during connection: {e}")

    def _ensure_connected(self):
        if self.sock is None:
            self._hello()

    def _disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def _change_outlet(self, outlet: int, state: int) -> bool:
        if not (0 <= outlet < self.relay_count):
            self._disconnect()
            print(
                f"Invalid outlet index: {outlet}. Valid range: 0 to {self.relay_count - 1}"
            )
            return False

        self._ensure_connected()

        # build header+payload
        self.seq += 1
        header = struct.pack(
            self.HEADER_PREFIX,
            self.COMMANDS["CMD_IO"],
            self.uName,
            self.pwd,
            self.COMMANDS["IO_CHANGE_RELAY"],
            0,
            self.seq,
        )
        chan = outlet + 1
        payload = struct.pack("<BB", chan, state)
        packet = header + payload
        self.sock.sendall(packet)

        # read single-byte ACK
        ack = self.sock.recv(1)
        self._disconnect()

        if ack == b"\x00":
            return True
        else:
            print(f"Failed to change outlet {outlet} to state {state}: {ack}")
            return False

    def get_outlet_state(self, outlet=0) -> bool:
        """
        Get the status of the specified outlet.
        :param outlet: Outlet index (0-based)
        :return: bool indicating if the outlet is energized (True) or relaxed (False)
        """
        if not (0 <= outlet < self.relay_count):
            self._disconnect()
            raise ValueError("Invalid outlet index")
        self._ensure_connected()
        self.seq += 1
        header = struct.pack(
            self.HEADER_PREFIX,
            self.COMMANDS["CMD_IO"],
            self.uName,
            self.pwd,
            self.COMMANDS["IO_GET_RELAYS"],
            0,
            self.seq,
        )
        packet = header
        self.sock.sendall(packet)

        data = self.sock.recv(self.relay_count)
        self._disconnect()

        data = data.ljust(self.relay_count, b"\x00")
        status = data[outlet] == self.COMMANDS["STATE_ENERGIZE"]
        # Will raise IndexError if outlet is out of range
        return status

    def turn_on_outlet(self, outlet=0) -> bool:
        """
        Turn on the specified outlet.
        :param outlet: Outlet index (0-based)
        :return: success boolean
        """
        return self._change_outlet(outlet, self.COMMANDS["STATE_ENERGIZE"])

    def turn_off_outlet(self, outlet=0) -> bool:
        """
        Turn off the specified outlet.
        :param outlet: Outlet index (0-based)
        :return: success boolean
        """
        return self._change_outlet(outlet, self.COMMANDS["STATE_RELAX"])


if __name__ == "__main__":
    pass

    #### Quick self-test ####
    # from time import sleep

    # HOST = "192.168.1.254" # Default if no DHCP
    # test_outlet = 0  # 0 index

    # test = SurgeX_DxPClient(
    #   HOST,
    #   model="SA-82-AR",
    #   username="admin", # Default is admin
    #   password="admin", # Default is admin
    # )
    # print(f"Outlet {test_outlet} is {test.get_outlet_state(test_outlet)}")
    # print(
    #    f"Turn Off Outlet {test_outlet} Success"
    #    if test.turn_off_outlet(test_outlet)
    #    else f"Turn Off Outlet {test_outlet} Failed!"
    # )
    # print(f"Outlet {test_outlet} is {test.get_outlet_state(test_outlet)}")
    # sleep(2)
    # print(
    #    f"Turn On Outlet {test_outlet} Success"
    #    if test.turn_on_outlet(test_outlet)
    #    else f"Turn On Outlet {test_outlet} Failed!"
    # )
    # print(f"Outlet {test_outlet} is {test.get_outlet_state(test_outlet)}")
