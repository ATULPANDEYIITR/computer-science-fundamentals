#!/usr/bin/env python3
"""
TCP Deep Dive: Connection Establishment, Reliability and Congestion Control.

A self-contained educational TCP simulator implementing:
- TCP three-way handshake
- Sequence and acknowledgment numbers
- Sliding-window transmission
- Cumulative acknowledgments
- Retransmission timeout
- Fast retransmission
- Duplicate ACK detection
- Slow start
- Congestion avoidance
- Fast recovery
- Receiver flow control
- Connection termination
- Packet-loss simulation
- Transmission statistics

Run:
    python tcp_deep_dive.py
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


MSS = 1000
INITIAL_CWND = 1.0
INITIAL_RTO = 1.0
MIN_RTO = 0.2
MAX_RTO = 60.0


class TCPState(Enum):
    CLOSED = auto()
    LISTEN = auto()
    SYN_SENT = auto()
    SYN_RECEIVED = auto()
    ESTABLISHED = auto()
    FIN_WAIT_1 = auto()
    FIN_WAIT_2 = auto()
    CLOSE_WAIT = auto()
    LAST_ACK = auto()
    TIME_WAIT = auto()


class CongestionState(Enum):
    SLOW_START = auto()
    CONGESTION_AVOIDANCE = auto()
    FAST_RECOVERY = auto()


class PacketType(Enum):
    SYN = auto()
    SYN_ACK = auto()
    ACK = auto()
    DATA = auto()
    FIN = auto()


@dataclass
class Segment:
    sequence: int
    acknowledgment: int
    payload: bytes = b""
    flags: set[str] = field(default_factory=set)
    timestamp: float = 0.0

    @property
    def length(self) -> int:
        # SYN and FIN each consume one sequence number.
        return len(self.payload) + int("SYN" in self.flags) + int("FIN" in self.flags)


@dataclass
class TCPStatistics:
    transmitted_segments: int = 0
    received_segments: int = 0
    retransmissions: int = 0
    duplicate_acks: int = 0
    dropped_segments: int = 0
    acknowledged_bytes: int = 0


@dataclass
class OutstandingSegment:
    segment: Segment
    first_sent: float
    last_sent: float
    retransmitted: bool = False


class NetworkSimulator:
    """Simulates an unreliable network with configurable packet loss."""

    def __init__(self, loss_probability: float = 0.0, seed: int = 42):
        if not 0 <= loss_probability <= 1:
            raise ValueError("Loss probability must be between 0 and 1.")

        self.loss_probability = loss_probability
        self.random = random.Random(seed)

    def transmit(self, segment: Segment) -> bool:
        return self.random.random() >= self.loss_probability


class TCPConnection:
    """Simplified TCP endpoint with reliability and congestion control."""

    def __init__(
        self,
        name: str,
        initial_sequence: int = 1000,
        mss: int = MSS,
        receiver_window: int = 64000,
    ):
        if initial_sequence < 0:
            raise ValueError("Initial sequence number cannot be negative.")
        if mss <= 0 or receiver_window < 0:
            raise ValueError("Invalid MSS or receiver window.")

        self.name = name
        self.state = TCPState.CLOSED

        self.iss = initial_sequence
        self.snd_una = initial_sequence
        self.snd_nxt = initial_sequence
        self.rcv_nxt = 0

        self.mss = mss
        self.rwnd = receiver_window

        self.cwnd = INITIAL_CWND
        self.ssthresh = 16.0
        self.congestion_state = CongestionState.SLOW_START

        self.rto = INITIAL_RTO
        self.srtt: Optional[float] = None
        self.rttvar: Optional[float] = None

        self.duplicate_ack_count = 0
        self.outstanding: dict[int, OutstandingSegment] = {}
        self.statistics = TCPStatistics()

    def _segment(
        self,
        sequence: int,
        acknowledgment: int = 0,
        flags: Optional[set[str]] = None,
        payload: bytes = b"",
    ) -> Segment:
        return Segment(
            sequence=sequence,
            acknowledgment=acknowledgment,
            payload=payload,
            flags=flags or set(),
            timestamp=time.monotonic(),
        )

    def connect(self, peer: TCPConnection) -> None:
        """Perform the TCP three-way handshake."""

        if self.state != TCPState.CLOSED:
            raise RuntimeError("Connection is not closed.")

        if peer.state not in (TCPState.CLOSED, TCPState.LISTEN):
            raise RuntimeError("Peer cannot accept a new connection.")

        self.state = TCPState.SYN_SENT
        peer.state = TCPState.LISTEN

        syn = self._segment(self.snd_nxt, flags={"SYN"})
        self.snd_nxt += 1

        self._record_transmission(syn)
        print(f"{self.name} -> {peer.name}: SYN seq={syn.sequence}")

        peer.rcv_nxt = syn.sequence + 1
        peer.iss = peer.snd_nxt
        peer.snd_una = peer.iss
        peer.snd_nxt += 1
        peer.state = TCPState.SYN_RECEIVED

        syn_ack = peer._segment(
            peer.iss,
            peer.rcv_nxt,
            {"SYN", "ACK"},
        )
        peer._record_transmission(syn_ack)

        print(
            f"{peer.name} -> {self.name}: SYN-ACK "
            f"seq={syn_ack.sequence} ack={syn_ack.acknowledgment}"
        )

        self.rcv_nxt = syn_ack.sequence + 1
        self.snd_una = syn_ack.acknowledgment

        ack = self._segment(
            self.snd_nxt,
            self.rcv_nxt,
            {"ACK"},
        )
        self._record_transmission(ack)

        peer.snd_una = ack.acknowledgment
        peer.state = TCPState.ESTABLISHED
        self.state = TCPState.ESTABLISHED

        print(
            f"{self.name} -> {peer.name}: ACK "
            f"seq={ack.sequence} ack={ack.acknowledgment}"
        )
        print("TCP connection established.")

    def _record_transmission(self, segment: Segment) -> None:
        self.statistics.transmitted_segments += 1

    def send_data(
        self,
        data: bytes,
        network: NetworkSimulator,
        receiver: TCPConnection,
        now: float,
    ) -> int:
        """Send data subject to congestion and receiver windows."""

        if self.state != TCPState.ESTABLISHED:
            raise RuntimeError("Connection is not established.")

        if not isinstance(data, bytes):
            raise TypeError("TCP payload must be bytes.")

        effective_window = min(
            int(self.cwnd * self.mss),
            self.rwnd,
        )

        in_flight = self.snd_nxt - self.snd_una
        available = max(0, effective_window - in_flight)

        payload = data[: min(self.mss, available)]

        if not payload:
            return 0

        segment = self._segment(
            self.snd_nxt,
            receiver.rcv_nxt,
            {"ACK"},
            payload,
        )

        self._record_transmission(segment)

        self.outstanding[segment.sequence] = OutstandingSegment(
            segment=segment,
            first_sent=now,
            last_sent=now,
        )

        self.snd_nxt += len(payload)

        if network.transmit(segment):
            receiver._receive_data(segment, self)
            self.statistics.received_segments += 1
        else:
            self.statistics.dropped_segments += 1
            print(f"Network dropped segment at seq={segment.sequence}")

        return len(payload)

    def _receive_data(
        self,
        segment: Segment,
        sender: TCPConnection,
    ) -> None:
        """Accept only contiguous bytes in this simplified receiver."""

        if segment.sequence == self.rcv_nxt:
            self.rcv_nxt += len(segment.payload)
            self.statistics.acknowledged_bytes += len(segment.payload)

            print(
                f"{self.name}: received {len(segment.payload)} bytes; "
                f"next expected={self.rcv_nxt}"
            )
        else:
            print(
                f"{self.name}: out-of-order segment; "
                f"expected={self.rcv_nxt}, got={segment.sequence}"
            )

        sender.process_ack(self.rcv_nxt)

    def process_ack(self, acknowledgment: int) -> None:
        """Process cumulative acknowledgments and congestion feedback."""

        if acknowledgment > self.snd_nxt:
            raise ValueError("ACK acknowledges unsent data.")

        if acknowledgment < self.snd_una:
            return

        if acknowledgment == self.snd_una:
            self.duplicate_ack_count += 1
            self.statistics.duplicate_acks += 1

            if self.duplicate_ack_count == 3:
                self._fast_retransmit()

            return

        acknowledged = acknowledgment - self.snd_una
        self.snd_una = acknowledgment
        self.duplicate_ack_count = 0

        # Remove segments completely covered by the cumulative ACK.
        acknowledged_sequences = [
            sequence
            for sequence, item in self.outstanding.items()
            if sequence + item.segment.length <= acknowledgment
        ]

        for sequence in acknowledged_sequences:
            del self.outstanding[sequence]

        self._increase_congestion_window()
        print(f"ACK received: {acknowledgment}, bytes acknowledged: {acknowledged}")

    def _increase_congestion_window(self) -> None:
        if self.congestion_state == CongestionState.SLOW_START:
            self.cwnd += 1.0

            if self.cwnd >= self.ssthresh:
                self.congestion_state = CongestionState.CONGESTION_AVOIDANCE

        elif self.congestion_state == CongestionState.CONGESTION_AVOIDANCE:
            self.cwnd += 1.0 / self.cwnd

        elif self.congestion_state == CongestionState.FAST_RECOVERY:
            self.cwnd = self.ssthresh
            self.congestion_state = CongestionState.CONGESTION_AVOIDANCE

    def _fast_retransmit(self) -> None:
        if not self.outstanding:
            return

        self.ssthresh = max(self.cwnd / 2.0, 2.0)
        self.cwnd = self.ssthresh + 3.0
        self.congestion_state = CongestionState.FAST_RECOVERY

        sequence = min(self.outstanding)
        item = self.outstanding[sequence]

        item.retransmitted = True
        item.last_sent = time.monotonic()

        self.statistics.retransmissions += 1
        self.statistics.transmitted_segments += 1

        print(f"Fast retransmission: seq={sequence}")

    def check_timeout(self, now: float) -> bool:
        """Retransmit the oldest unacknowledged segment after timeout."""

        if not self.outstanding:
            return False

        sequence = min(self.outstanding)
        item = self.outstanding[sequence]

        if now - item.last_sent < self.rto:
            return False

        self.statistics.retransmissions += 1
        self.statistics.transmitted_segments += 1

        item.last_sent = now
        item.retransmitted = True

        self.ssthresh = max(self.cwnd / 2.0, 2.0)
        self.cwnd = 1.0
        self.congestion_state = CongestionState.SLOW_START

        self.rto = min(self.rto * 2.0, MAX_RTO)
        self.duplicate_ack_count = 0

        print(
            f"Timeout: retransmitting seq={sequence}, "
            f"new RTO={self.rto:.2f}s, cwnd={self.cwnd}"
        )

        return True

    def update_rtt(self, measured_rtt: float) -> None:
        """Estimate RTT using smoothed RTT and RTT variation."""

        if measured_rtt <= 0:
            raise ValueError("RTT must be positive.")

        if self.srtt is None:
            self.srtt = measured_rtt
            self.rttvar = measured_rtt / 2.0
        else:
            assert self.rttvar is not None

            self.rttvar = (
                0.75 * self.rttvar
                + 0.25 * abs(self.srtt - measured_rtt)
            )

            self.srtt = (
                0.875 * self.srtt
                + 0.125 * measured_rtt
            )

        assert self.rttvar is not None

        self.rto = min(
            MAX_RTO,
            max(
                MIN_RTO,
                self.srtt + 4 * self.rttvar,
            ),
        )

    def close(self, peer: TCPConnection) -> None:
        """Demonstrate the active side of TCP connection termination."""

        if self.state != TCPState.ESTABLISHED:
            raise RuntimeError("Only established connections can close.")

        self.state = TCPState.FIN_WAIT_1
        fin = self._segment(self.snd_nxt, flags={"FIN", "ACK"})
        self.snd_nxt += 1

        peer.rcv_nxt = fin.sequence + 1
        peer.state = TCPState.CLOSE_WAIT

        self.snd_una = self.snd_nxt
        self.state = TCPState.FIN_WAIT_2

        print(f"{self.name} -> {peer.name}: FIN")
        print(f"{peer.name} -> {self.name}: ACK")

        peer.state = TCPState.LAST_ACK
        peer.snd_nxt += 1
        self.rcv_nxt = peer.snd_nxt
        peer.snd_una = peer.snd_nxt

        print(f"{peer.name} -> {self.name}: FIN")
        print(f"{self.name} -> {peer.name}: ACK")

        peer.state = TCPState.CLOSED
        self.state = TCPState.TIME_WAIT

        print("Active endpoint enters TIME_WAIT.")
        print("TIME_WAIT prevents delayed old segments from contaminating a new connection.")

    def report(self) -> None:
        print(f"\nTCP statistics: {self.name}")
        print(f"State: {self.state.name}")
        print(f"Congestion state: {self.congestion_state.name}")
        print(f"cwnd: {self.cwnd:.2f} MSS")
        print(f"ssthresh: {self.ssthresh:.2f} MSS")
        print(f"RTO: {self.rto:.2f}s")
        print(f"Outstanding segments: {len(self.outstanding)}")
        print(f"Transmitted: {self.statistics.transmitted_segments}")
        print(f"Retransmissions: {self.statistics.retransmissions}")
        print(f"Duplicate ACKs: {self.statistics.duplicate_acks}")
        print(f"Dropped: {self.statistics.dropped_segments}")


def demonstrate_handshake() -> tuple[TCPConnection, TCPConnection]:
    client = TCPConnection("Client", initial_sequence=1000)
    server = TCPConnection("Server", initial_sequence=5000)

    client.connect(server)

    assert client.state == TCPState.ESTABLISHED
    assert server.state == TCPState.ESTABLISHED

    return client, server


def demonstrate_data_transfer(
    client: TCPConnection,
    server: TCPConnection,
) -> None:
    network = NetworkSimulator(loss_probability=0.0)

    print("\n--- Reliable data transmission ---")

    now = time.monotonic()

    payload = b"A" * 2500
    offset = 0

    while offset < len(payload):
        sent = client.send_data(
            payload[offset:],
            network,
            server,
            now,
        )

        if sent == 0:
            break

        offset += sent
        now += 0.1

    assert client.snd_una == client.snd_nxt
    print("All transmitted data acknowledged.")


def demonstrate_timeout() -> None:
    print("\n--- Retransmission timeout ---")

    sender = TCPConnection("Sender")
    receiver = TCPConnection("Receiver")

    sender.state = TCPState.ESTABLISHED
    receiver.state = TCPState.ESTABLISHED

    sender.send_data(
        b"Important network data",
        NetworkSimulator(loss_probability=1.0),
        receiver,
        10.0,
    )

    assert sender.check_timeout(12.0)
    assert sender.statistics.retransmissions == 1


def demonstrate_rtt_estimation() -> None:
    print("\n--- RTT estimation ---")

    connection = TCPConnection("RTT-Endpoint")

    for sample in (0.12, 0.15, 0.11, 0.18, 0.14):
        connection.update_rtt(sample)
        print(
            f"Sample={sample:.3f}s, "
            f"SRTT={connection.srtt:.3f}s, "
            f"RTO={connection.rto:.3f}s"
        )


def main() -> None:
    print("=" * 65)
    print("TCP DEEP DIVE")
    print("=" * 65)

    client, server = demonstrate_handshake()

    demonstrate_data_transfer(client, server)

    demonstrate_timeout()

    demonstrate_rtt_estimation()

    print("\n--- Connection termination ---")
    client.close(server)

    client.report()

    print("\nTCP simulation completed.")


if __name__ == "__main__":
    main()
