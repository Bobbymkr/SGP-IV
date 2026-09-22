"""Wire-level tests for the REAL NTCIP1202STMPAdapter (no mocks).

A fake-controller UDP socket on 127.0.0.1 answers requests, proving the
adapter's bytes-on-wire (header, OID BER, varbind framing), the retry/timeout
path, and transaction-id sequencing.

Explicit non-goal: response parsing. ``_parse_stmp_response`` is an
unimplemented stub returning ``{}`` (so GET yields default cycle values).
That is asserted below as DOCUMENTED behavior — when someone implements the
ASN.1 parser, ``test_get_returns_defaults`` must be rewritten, not deleted.
"""

import socket
import struct
import threading

import pytest

from adaptive_traffic.adapters.ntcip_stmp import NTCIP1202STMPAdapter
from adaptive_traffic.core.ports.ntcip_port import NTCIPCycleConfig, NTCIPPhaseTiming

STMP_SET, STMP_GET, STMP_RESPONSE = 0x40, 0x41, 0x42


class FakeController:
    """Minimal UDP controller: records requests, replies canned responses."""

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.settimeout(0.2)
        self.port = self.sock.getsockname()[1]
        self.seen = []  # raw request datagrams
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self):
        while not self._stop.is_set():
            try:
                data, addr = self.sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                return
            self.seen.append(data)
            tid = struct.unpack("!H", data[3:5])[0]
            comm_len = data[5]
            comm = data[6 : 6 + comm_len]
            self.sock.sendto(
                struct.pack("!BBBHB", 1, STMP_RESPONSE, 0, tid, comm_len) + comm + b"OK",
                addr,
            )

    def pdu_types(self):
        return [d[1] for d in self.seen]

    def tids(self):
        return [struct.unpack("!H", d[3:5])[0] for d in self.seen]

    def close(self):
        self._stop.set()
        self._thread.join(timeout=2)
        self.sock.close()


@pytest.fixture()
def controller():
    c = FakeController()
    yield c
    c.close()


def _adapter(port, **over):
    cfg = {
        "ntcip_controller_ip": "127.0.0.1",
        "ntcip_stmp_port": port,
        "ntcip_timeout": 2.0,
        "ntcip_max_retries": 2,
    }
    cfg.update(over)
    a = NTCIP1202STMPAdapter(cfg)
    yield a
    a.close()


@pytest.fixture()
def adapter(controller):
    yield from _adapter(controller.port)


def _cycle(green=20.0):
    return NTCIPCycleConfig(
        cycle_length=120.0,
        offset=0.0,
        phases=[NTCIPPhaseTiming(i + 1, green, 5.0, 85.0) for i in range(4)],
    )


def test_header_encoding(adapter):
    assert adapter._build_stmp_header(STMP_SET, 0x1234) == (
        bytes([1, STMP_SET, 0]) + struct.pack("!H", 0x1234) + bytes([6]) + b"public"
    )


def test_oid_ber_known_vector(adapter):
    # 1.3 -> 0x2B; 1206 -> 0x89 0x36 (multi-byte BER); rest single bytes
    assert adapter._encode_oid("1.3.6.1.4.1.1206.4.2.3.1.0") == bytes(
        [0x2B, 6, 1, 4, 1, 0x89, 0x36, 4, 2, 3, 1, 0]
    )
    with pytest.raises(ValueError):
        adapter._encode_oid("9")


def test_varbind_framing(adapter):
    vb = adapter._build_varbind(adapter.OID_CYCLE_LENGTH, 120)
    assert vb[0] == 0x30  # SEQUENCE
    assert b"\x06" in vb and b"\x02" in vb  # OID + INTEGER tags present


def test_length_long_form(adapter):
    assert adapter._encode_length(100) == bytes([100])
    assert adapter._encode_length(200) == bytes([0x81, 0xC8])
    assert adapter._encode_length(300) == bytes([0x82, 0x01, 0x2C])


def test_set_succeeds_over_loopback(adapter, controller):
    assert adapter.set_phase_timing(_cycle()) is True
    assert controller.pdu_types() == [STMP_SET]
    assert len(controller.seen[0]) > 20  # header + cycle/offset/phase varbinds


def test_transaction_id_increments(adapter, controller):
    adapter.set_phase_timing(_cycle())
    adapter.set_phase_timing(_cycle())
    assert controller.tids() == [1, 2]


def test_timeout_returns_false_fast(controller):
    dead_port = controller.port  # rebound below is avoided: use a closed socket's port
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    probe.bind(("127.0.0.1", 0))
    dead = probe.getsockname()[1]
    probe.close()
    assert dead != dead_port
    gen = _adapter(dead, ntcip_timeout=0.2, ntcip_max_retries=1)
    adapter = next(gen)
    try:
        assert adapter.set_phase_timing(_cycle()) is False
        assert adapter.is_connected() is False
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


def test_get_returns_defaults_parser_stub_documented(adapter, controller):
    """GET succeeds on the wire but the stub parser drops the body, so the
    adapter returns default cycle values. Update (don't delete) this test
    when _parse_stmp_response is implemented."""
    cfg = adapter.get_phase_timing()
    assert controller.pdu_types() == [STMP_GET]
    assert cfg is not None and cfg.cycle_length == 120
    assert len(cfg.phases) == 4
