#!/usr/bin/env python3
"""
Application Layer Protocols
HTTP, HTTPS, DNS, SMTP, FTP and SSH

A self-contained protocol learning and simulation environment.
Uses Python standard-library components only.
"""

from __future__ import annotations

import base64
import hashlib
import ipaddress
import json
import re
import socket
import ssl
import struct
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from urllib.parse import urlparse


# ============================================================
# 1. Common protocol infrastructure
# ============================================================

class ProtocolError(Exception):
    """Base exception for application protocol failures."""


class ValidationError(ProtocolError):
    """Raised when protocol input is invalid."""


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    CLOSED = "closed"


@dataclass
class ProtocolResult:
    protocol: str
    success: bool
    message: str
    duration_ms: float = 0.0
    details: dict = field(default_factory=dict)


def validate_hostname(hostname: str) -> str:
    if not isinstance(hostname, str) or not hostname:
        raise ValidationError("Hostname cannot be empty.")

    hostname = hostname.rstrip(".").lower()

    if len(hostname) > 253:
        raise ValidationError("Hostname exceeds DNS length limits.")

    labels = hostname.split(".")

    for label in labels:
        if (
            not label
            or len(label) > 63
            or not re.fullmatch(
                r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?",
                label
            )
        ):
            raise ValidationError(f"Invalid DNS label: {label}")

    return hostname


def timed_call(protocol: str, operation) -> ProtocolResult:
    start = time.perf_counter()

    try:
        details = operation()
        return ProtocolResult(
            protocol=protocol,
            success=True,
            message="Operation completed successfully.",
            duration_ms=(time.perf_counter() - start) * 1000,
            details=details or {}
        )
    except Exception as exc:
        return ProtocolResult(
            protocol=protocol,
            success=False,
            message=str(exc),
            duration_ms=(time.perf_counter() - start) * 1000
        )


# ============================================================
# 2. DNS: Domain Name System
# ============================================================

class DNSRecordType(Enum):
    A = 1
    NS = 2
    CNAME = 5
    SOA = 6
    PTR = 12
    MX = 15
    TXT = 16
    AAAA = 28


@dataclass
class DNSRecord:
    hostname: str
    record_type: DNSRecordType
    value: str
    ttl: int = 300


class DNSCache:
    """TTL-aware in-memory DNS cache."""

    def __init__(self):
        self._records = {}

    def put(self, record: DNSRecord):
        hostname = validate_hostname(record.hostname)

        if record.ttl < 0:
            raise ValidationError("TTL cannot be negative.")

        self._records[(hostname, record.record_type)] = (
            record,
            time.monotonic() + record.ttl
        )

    def get(
        self,
        hostname: str,
        record_type: DNSRecordType
    ) -> Optional[DNSRecord]:

        key = (validate_hostname(hostname), record_type)
        entry = self._records.get(key)

        if entry is None:
            return None

        record, expires_at = entry

        if time.monotonic() >= expires_at:
            del self._records[key]
            return None

        return record

    def purge_expired(self):
        now = time.monotonic()

        expired = [
            key
            for key, (_, expiry) in self._records.items()
            if expiry <= now
        ]

        for key in expired:
            del self._records[key]

        return len(expired)


class DNSClient:
    """DNS resolver using UDP with a bounded response timeout."""

    def __init__(
        self,
        server: str = "8.8.8.8",
        timeout: float = 3.0
    ):
        self.server = server
        self.timeout = timeout
        self.cache = DNSCache()

    @staticmethod
    def encode_name(hostname: str) -> bytes:
        hostname = validate_hostname(hostname)
        encoded = b""

        for label in hostname.split("."):
            data = label.encode("ascii")
            encoded += bytes([len(data)]) + data

        return encoded + b"\x00"

    @staticmethod
    def decode_name(packet: bytes, offset: int):
        labels = []
        visited = set()
        original_offset = None

        while True:
            if offset >= len(packet):
                raise ProtocolError("Truncated DNS name.")

            length = packet[offset]

            if length == 0:
                offset += 1
                break

            if length & 0xC0 == 0xC0:
                if offset + 1 >= len(packet):
                    raise ProtocolError("Invalid DNS pointer.")

                pointer = ((length & 0x3F) << 8) | packet[offset + 1]

                if pointer in visited or pointer >= len(packet):
                    raise ProtocolError("DNS compression loop.")

                visited.add(pointer)

                if original_offset is None:
                    original_offset = offset + 2

                offset = pointer
                continue

            if length & 0xC0:
                raise ProtocolError("Unsupported DNS label encoding.")

            if offset + 1 + length > len(packet):
                raise ProtocolError("Truncated DNS label.")

            label = packet[offset + 1:offset + 1 + length]
            labels.append(label.decode("ascii"))
            offset += length + 1

        return ".".join(labels), (
            original_offset if original_offset is not None else offset
        )

    def resolve(
        self,
        hostname: str,
        record_type: DNSRecordType = DNSRecordType.A
    ) -> list[str]:

        hostname = validate_hostname(hostname)

        cached = self.cache.get(hostname, record_type)

        if cached:
            return [cached.value]

        transaction_id = int(time.time_ns()) & 0xFFFF

        header = struct.pack(
            "!HHHHHH",
            transaction_id,
            0x0100,
            1,
            0,
            0,
            0
        )

        question = (
            self.encode_name(hostname)
            + struct.pack("!HH", record_type.value, 1)
        )

        packet = header + question

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(self.timeout)
            sock.sendto(packet, (self.server, 53))
            response, _ = sock.recvfrom(4096)

        if len(response) < 12:
            raise ProtocolError("Incomplete DNS response.")

        (
            response_id,
            flags,
            questions,
            answers,
            _,
            _
        ) = struct.unpack("!HHHHHH", response[:12])

        if response_id != transaction_id:
            raise ProtocolError("DNS transaction ID mismatch.")

        if not flags & 0x8000:
            raise ProtocolError("Response is not a DNS response.")

        if flags & 0x000F:
            raise ProtocolError(
                f"DNS returned error code {flags & 0x000F}."
            )

        offset = 12

        for _ in range(questions):
            _, offset = self.decode_name(response, offset)
            offset += 4

        results = []

        for _ in range(answers):
            name, offset = self.decode_name(response, offset)

            if offset + 10 > len(response):
                raise ProtocolError("Truncated DNS answer.")

            rtype, rclass, ttl, length = struct.unpack(
                "!HHIH",
                response[offset:offset + 10]
            )

            offset += 10

            if offset + length > len(response):
                raise ProtocolError("Truncated DNS record data.")

            data = response[offset:offset + length]
            offset += length

            if rclass != 1 or rtype != record_type.value:
                continue

            if rtype == DNSRecordType.A.value and length == 4:
                value = socket.inet_ntoa(data)
            elif rtype == DNSRecordType.AAAA.value and length == 16:
                value = socket.inet_ntop(socket.AF_INET6, data)
            else:
                continue

            results.append(value)

            self.cache.put(
                DNSRecord(
                    hostname=name or hostname,
                    record_type=record_type,
                    value=value,
                    ttl=ttl
                )
            )

        return results


# ============================================================
# 3. HTTP and HTTPS
# ============================================================

@dataclass
class HTTPRequest:
    method: str
    url: str
    headers: dict = field(default_factory=dict)
    body: bytes = b""

    def validate(self):
        if not re.fullmatch(
            r"[A-Z]{3,10}",
            self.method.upper()
        ):
            raise ValidationError("Invalid HTTP method.")

        parsed = urlparse(self.url)

        if parsed.scheme not in ("http", "https"):
            raise ValidationError("Only HTTP and HTTPS are supported.")

        if not parsed.hostname:
            raise ValidationError("URL hostname is required.")

        if any(ord(char) < 32 for char in self.url):
            raise ValidationError("Control character in URL.")


class HTTPClient:
    """HTTP/HTTPS client with certificate verification."""

    def __init__(self, timeout=5.0):
        self.timeout = timeout

    def request(self, request: HTTPRequest):
        request.validate()

        parsed = urlparse(request.url)

        context = ssl.create_default_context()

        connection_class = (
            ssl.create_default_context
            if parsed.scheme == "https"
            else None
        )

        import http.client

        if parsed.scheme == "https":
            connection = http.client.HTTPSConnection(
                parsed.hostname,
                parsed.port or 443,
                timeout=self.timeout,
                context=context
            )
        else:
            connection = http.client.HTTPConnection(
                parsed.hostname,
                parsed.port or 80,
                timeout=self.timeout
            )

        path = parsed.path or "/"

        if parsed.query:
            path += "?" + parsed.query

        headers = {
            "User-Agent": "ProtocolLab/1.0",
            "Connection": "close",
            **request.headers
        }

        try:
            connection.request(
                request.method.upper(),
                path,
                body=request.body or None,
                headers=headers
            )

            response = connection.getresponse()

            response_body = response.read(1024 * 1024 + 1)

            if len(response_body) > 1024 * 1024:
                raise ProtocolError("Response exceeds 1 MB limit.")

            return {
                "status": response.status,
                "reason": response.reason,
                "headers": dict(response.getheaders()),
                "body": response_body.decode(
                    "utf-8",
                    errors="replace"
                ),
                "http_version": response.version
            }

        finally:
            connection.close()


# ============================================================
# 4. SMTP: Simple Mail Transfer Protocol
# ============================================================

class SMTPWorkflow:
    """Email submission using authenticated SMTP."""

    def __init__(self, host, port=587, timeout=10):
        self.host = validate_hostname(host)
        self.port = port
        self.timeout = timeout

    def send(
        self,
        username,
        password,
        sender,
        recipients,
        subject,
        body
    ):
        import smtplib
        from email.message import EmailMessage

        if not recipients:
            raise ValidationError("At least one recipient is required.")

        message = EmailMessage()
        message["From"] = sender
        message["To"] = ", ".join(recipients)
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(
            self.host,
            self.port,
            timeout=self.timeout
        ) as server:

            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            server.login(username, password)

            refused = server.send_message(message)

            if refused:
                raise ProtocolError(
                    f"Some recipients were refused: {refused}"
                )

        return {
            "sender": sender,
            "recipient_count": len(recipients),
            "subject": subject,
            "transport_security": "STARTTLS"
        }


# ============================================================
# 5. FTP: File Transfer Protocol
# ============================================================

class FTPWorkflow:
    """FTP transfer with explicit TLS support."""

    def __init__(self, host, port=21, timeout=10):
        self.host = validate_hostname(host)
        self.port = port
        self.timeout = timeout

    def list_directory(
        self,
        username,
        password,
        use_tls=True
    ):
        import ftplib

        ftp = None

        try:
            if use_tls:
                ftp = ftplib.FTP_TLS(timeout=self.timeout)
            else:
                ftp = ftplib.FTP(timeout=self.timeout)

            ftp.connect(self.host, self.port)
            ftp.login(username, password)

            if use_tls:
                ftp.prot_p()

            return ftp.nlst()

        finally:
            if ftp is not None:
                try:
                    ftp.quit()
                except Exception:
                    ftp.close()


# ============================================================
# 6. SSH: Secure Shell
# ============================================================

class SSHWorkflow:
    """
    Uses the operating-system OpenSSH client.

    Host-key verification remains enabled through
    StrictHostKeyChecking=yes.
    """

    def execute(
        self,
        hostname,
        username,
        command,
        port=22,
        timeout=15
    ):
        import subprocess

        hostname = validate_hostname(hostname)

        if not username or not re.fullmatch(
            r"[A-Za-z0-9_.-]+",
            username
        ):
            raise ValidationError("Invalid SSH username.")

        if not command or len(command) > 2048:
            raise ValidationError("Invalid remote command.")

        if "\x00" in command:
            raise ValidationError("NUL byte in command.")

        if not 1 <= port <= 65535:
            raise ValidationError("Invalid SSH port.")

        arguments = [
            "ssh",
            "-p", str(port),
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=yes",
            "-o", "ConnectTimeout=10",
            f"{username}@{hostname}",
            command
        ]

        result = subprocess.run(
            arguments,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )

        if result.returncode != 0:
            raise ProtocolError(
                result.stderr.strip()
                or f"SSH exited with code {result.returncode}."
            )

        return {
            "hostname": hostname,
            "username": username,
            "output": result.stdout,
            "exit_code": result.returncode
        }


# ============================================================
# 7. Protocol registry and port identification
# ============================================================

@dataclass(frozen=True)
class ProtocolDefinition:
    name: str
    default_port: int
    transport: str
    encrypted: bool


PROTOCOLS = {
    "HTTP": ProtocolDefinition("HTTP", 80, "TCP", False),
    "HTTPS": ProtocolDefinition("HTTPS", 443, "TCP", True),
    "DNS": ProtocolDefinition("DNS", 53, "UDP/TCP", False),
    "SMTP": ProtocolDefinition("SMTP", 587, "TCP", True),
    "FTP": ProtocolDefinition("FTP", 21, "TCP", False),
    "SSH": ProtocolDefinition("SSH", 22, "TCP", True),
}


def inspect_protocols():
    for name, definition in PROTOCOLS.items():
        print(
            f"{name:8} "
            f"Port={definition.default_port:<4} "
            f"Transport={definition.transport:<7} "
            f"Encrypted={definition.encrypted}"
        )


def inspect_ip_address(address):
    ip = ipaddress.ip_address(address)

    return {
        "address": str(ip),
        "version": ip.version,
        "private": ip.is_private,
        "loopback": ip.is_loopback,
        "multicast": ip.is_multicast
    }


# ============================================================
# 8. Execution and validation
# ============================================================

def run_tests():
    # DNS input validation and cache.
    cache = DNSCache()

    cache.put(
        DNSRecord(
            "example.com",
            DNSRecordType.A,
            "93.184.216.34",
            300
        )
    )

    assert cache.get(
        "example.com",
        DNSRecordType.A
    ).value == "93.184.216.34"

    assert cache.get(
        "missing.example",
        DNSRecordType.A
    ) is None

    # DNS name encoding and decoding.
    encoded = DNSClient.encode_name("example.com")
    decoded, next_offset = DNSClient.decode_name(encoded, 0)

    assert decoded == "example.com"
    assert next_offset == len(encoded)

    # HTTP validation.
    request = HTTPRequest(
        method="GET",
        url="https://example.com/"
    )

    request.validate()

    # Protocol metadata.
    assert PROTOCOLS["HTTPS"].default_port == 443
    assert PROTOCOLS["SSH"].default_port == 22

    # IP classification.
    assert inspect_ip_address("127.0.0.1")["loopback"]

    try:
        validate_hostname("invalid hostname")
        raise AssertionError("Invalid hostname was accepted.")
    except ValidationError:
        pass

    print("All protocol validation tests passed.")


def main():
    print("=" * 60)
    print("APPLICATION LAYER PROTOCOL LAB")
    print("=" * 60)

    inspect_protocols()
    print()

    run_tests()
    print()

    print("IP inspection:")
    print(json.dumps(
        inspect_ip_address("192.168.1.10"),
        indent=2
    ))

    print("\nDNS cache demonstration:")

    cache = DNSCache()
    cache.put(
        DNSRecord(
            "service.example",
            DNSRecordType.A,
            "192.0.2.10",
            60
        )
    )

    print(cache.get(
        "service.example",
        DNSRecordType.A
    ))

    print("\nNetwork operations are available through their")
    print("respective client classes and require valid credentials")
    print("or reachable services.")


if __name__ == "__main__":
    main()
