# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
"""The transport-agnostic rules: options, headers, retry decisions, decoding."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st

from crypto_service import ApiError, RetryOptions, TransportError, _core, types
from crypto_service._shape import check_shape

RETRY = RetryOptions(max_retries=3)
TRACEPARENT = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"


def config(**overrides: object) -> _core.Config:
    options: dict[str, object] = {
        "api_key": None,
        "token": None,
        "timeout": 30.0,
        "deadline": None,
        "retry": None,
        "traceparent": None,
    }
    options.update(overrides)
    return _core.Config.create("https://crypto.test/", **options)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "url",
    [
        "ftp://crypto.test",
        "crypto.test",
        "https://",
        "https://user:pw@crypto.test",
        "https://user@crypto.test",
        "https://crypto.test/?a=1",
        "https://crypto.test/#x",
    ],
)
def test_base_url_is_checked(url: str) -> None:
    with pytest.raises(ValueError, match="base_url"):
        _core.Config.create(
            url, api_key=None, token=None, timeout=1, deadline=None, retry=None, traceparent=None
        )


@pytest.mark.parametrize("name", ["api_key", "token", "traceparent"])
@pytest.mark.parametrize("value", ["", "a\r\nb", "a\nb", "a\0b"])
def test_header_values_are_checked(name: str, value: str) -> None:
    with pytest.raises(ValueError, match=name) as caught:
        config(**{name: value})
    assert value not in str(caught.value) or value == ""


@pytest.mark.parametrize(
    "value",
    [" synthetic", "synthetic ", "k\tey\x7f", "kl\u00fcssel", "\u043a\u043b\u044e\u0447", "a\x01b"],
)
def test_api_key_is_visible_ascii(value: str) -> None:
    with pytest.raises(ValueError, match="api_key") as caught:
        config(api_key=value)
    assert value not in str(caught.value)


@pytest.mark.parametrize("value", ["synthetic-api-key", "k!#$%&'*+-.^_`|~{}[]<>@", "a b\tc"])
def test_api_key_accepts_visible_ascii(value: str) -> None:
    assert config(api_key=value).api_key == value


@pytest.mark.parametrize("value", ["a b", "a,b", "a=b", "=", "eyJ.\u00e9", "a;b", "Bearer x"])
def test_token_is_token68(value: str) -> None:
    with pytest.raises(ValueError, match="token") as caught:
        config(token=value)
    assert value not in str(caught.value)


@pytest.mark.parametrize(
    "value", ["synthetic.jwt", "eyJhbGciOi.eyJzdWIiOi.c2lnbmF0dXJl-_", "a+/b~==", "abc="]
)
def test_token_accepts_token68(value: str) -> None:
    assert config(token=value).token == value


@pytest.mark.parametrize(
    "value",
    [
        "00-tp",
        "00-0AF7651916CD43DD8448EB211C80319C-b7ad6b7169203331-01",
        "00-00000000000000000000000000000000-b7ad6b7169203331-01",
        "00-0af7651916cd43dd8448eb211c80319c-0000000000000000-01",
        "ff-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01",
        "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01 ",
    ],
)
def test_traceparent_follows_w3c_trace_context(value: str) -> None:
    with pytest.raises(ValueError, match="traceparent"):
        config(traceparent=value)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "https://elsewhere.test/v2/hash"),
        ("GET", "//elsewhere.test/v2/hash"),
        ("GET", "elsewhere.test:443/v2/hash"),
        ("GET", "/v2/hash\r\nx: y"),
        ("GET", "/v2/has h"),
        ("GE T", "/v2/hash"),
        ("", "/v2/hash"),
        ("GET\n", "/v2/hash"),
    ],
)
def test_raw_request_target_is_checked(method: str, path: str) -> None:
    with pytest.raises(ValueError, match=r"^(method|path) "):
        _core.check_request_target(method, path)


@pytest.mark.parametrize(
    ("method", "path"),
    [("GET", "/v2/hash"), ("POST", "v2/hash"), ("PROPFIND", "/metrics?x=1"), ("GET", "/")],
)
def test_raw_request_target_accepts_relative_paths(method: str, path: str) -> None:
    _core.check_request_target(method, path)


@pytest.mark.parametrize(
    "headers",
    [{"x-h": "a\r\nb: c"}, {"x-h": "\u00e9"}, {"x h": "v"}, {"": "v"}, {"x-h:": "v"}],
)
def test_extra_headers_are_checked(headers: dict[str, str]) -> None:
    with pytest.raises(ValueError, match="header"):
        config().headers(auth=True, has_body=False, extra=headers)


@pytest.mark.parametrize(("timeout", "deadline"), [(0, None), (-1, None), (1, 0), (None, -2)])
def test_timeouts_must_be_positive(timeout: float | None, deadline: float | None) -> None:
    with pytest.raises(ValueError, match="positive"):
        config(timeout=timeout, deadline=deadline)


def test_retry_options_must_not_be_negative() -> None:
    with pytest.raises(ValueError, match="negative"):
        RetryOptions(max_retries=-1)


def test_config_defaults_and_repr() -> None:
    cfg = config(api_key="synthetic-key")
    assert cfg.base_url == "https://crypto.test"
    assert cfg.retry == RetryOptions()
    assert "synthetic" not in repr(cfg)
    assert cfg.describe("Client") == (
        "Client(base_url='https://crypto.test', api_key='***', token=None)"
    )


def test_headers() -> None:
    cfg = config(api_key="k", token="t", traceparent=TRACEPARENT)
    headers = cfg.headers(auth=True, has_body=True, extra={"x-extra": "1"})
    assert headers["x-api-key"] == "k"
    assert headers["authorization"] == "Bearer t"
    assert headers["traceparent"] == TRACEPARENT
    assert headers["content-type"] == "application/json"
    assert headers["x-extra"] == "1"
    public = cfg.headers(auth=False, has_body=False)
    assert "x-api-key" not in public
    assert "authorization" not in public
    assert "content-type" not in public


def test_generated_traceparent_is_valid() -> None:
    value = _core.generate_traceparent()
    version, trace_id, parent_id, flags = value.split("-")
    assert (version, flags) == ("00", "01")
    assert len(trace_id) == 32
    assert len(parent_id) == 16
    assert int(trace_id, 16) != 0
    assert int(parent_id, 16) != 0


@pytest.mark.parametrize(
    ("method", "path", "idempotent"),
    [
        ("GET", "/v2/keys/generate", True),
        ("POST", "/v2/hash", True),
        ("POST", "/v2/keys/export", True),
        ("POST", "/v2/keys/generate", False),
        ("POST", "/v2/keys/delete", False),
        ("POST", "/v2/pq/keygen", False),
        ("POST", "/v2/pq/hybrid/keygen", False),
        ("POST", "/v2/pq/dsa/keygen", False),
        ("POST", "/v2/pq/slh-dsa/keygen", False),
        ("POST", "/v2/hpke/keygen", False),
        ("POST", "/v2/kms/create-key", False),
        ("POST", "/v2/opaque/register/init", False),
        ("POST", "/v2/opaque/register/finish", False),
        ("POST", "/v2/opaque/login/init", True),
    ],
)
def test_retry_safety_table(method: str, path: str, idempotent: bool) -> None:
    assert _core.is_idempotent(method, path) is idempotent


@pytest.mark.parametrize(
    ("header", "seconds"),
    [
        (None, None),
        ("", None),
        ("  ", None),
        ("3", 3.0),
        ("0.5", 0.5),
        ("-1", None),
        ("inf", None),
        ("nan", None),
        ("soon", None),
    ],
)
def test_retry_after_values(header: str | None, seconds: float | None) -> None:
    assert _core.retry_after_seconds(header, time.time()) == seconds


def test_retry_after_http_dates() -> None:
    now = datetime(2026, 11, 15, 12, 0, tzinfo=UTC)
    later = format_datetime(now + timedelta(seconds=7), usegmt=True)
    earlier = format_datetime(now - timedelta(seconds=7), usegmt=True)
    assert _core.retry_after_seconds(later, now.timestamp()) == pytest.approx(7)
    assert _core.retry_after_seconds(earlier, now.timestamp()) == 0
    naive = "Sun, 15 Nov 2026 12:00:05 -0000"
    assert _core.retry_after_seconds(naive, now.timestamp()) == pytest.approx(5)


def test_backoff_is_full_jitter_under_a_cap() -> None:
    retry = RetryOptions(max_retries=10, initial_delay=0.2, max_delay=2.0)
    assert _core.backoff_delay(1, retry, rand=lambda: 1.0) == pytest.approx(0.2)
    assert _core.backoff_delay(3, retry, rand=lambda: 1.0) == pytest.approx(0.8)
    assert _core.backoff_delay(9, retry, rand=lambda: 1.0) == pytest.approx(2.0)
    assert _core.backoff_delay(10_000, retry, rand=lambda: 0.5) == pytest.approx(1.0)
    assert _core.backoff_delay(1, retry, "1") == 1.0
    assert _core.backoff_delay(1, retry, "3") is None


def test_retry_decisions() -> None:
    assert _core.delay_after_error(1, RETRY, idempotent=False) is None
    assert _core.delay_after_error(4, RETRY, idempotent=True) is None
    assert _core.delay_after_error(3, RETRY, idempotent=True) is not None
    assert _core.delay_after_status(503, None, 4, RETRY, idempotent=True) is None
    assert _core.delay_after_status(500, None, 1, RETRY, idempotent=True) is None
    assert _core.delay_after_status(504, None, 1, RETRY, idempotent=False) is None
    assert _core.delay_after_status(504, None, 1, RETRY, idempotent=True) is not None
    assert _core.delay_after_status(429, "0", 1, RETRY, idempotent=False) == 0


def test_unbounded_deadline() -> None:
    unbounded = _core.Deadline(None)
    assert unbounded.budget(30.0) == 30.0
    assert unbounded.budget(None) is None
    assert unbounded.allows(1e9)


def test_bounded_deadline() -> None:
    bounded = _core.Deadline(10.0)
    budget = bounded.budget(30.0)
    assert budget is not None
    assert 9 < budget <= 10
    assert bounded.budget(1.0) == 1.0
    no_timeout = bounded.budget(None)
    assert no_timeout is not None
    assert no_timeout <= 10
    assert bounded.allows(1.0)
    assert not bounded.allows(11.0)


def test_expired_deadline() -> None:
    expired = _core.Deadline(1e-9)
    time.sleep(0.001)
    with pytest.raises(TransportError) as caught:
        expired.budget(1.0)
    assert caught.value.timed_out


def test_blocking_scope_is_a_no_op() -> None:
    with _core.blocking_scope(1.0) as value:
        assert value is None


def test_encode_body_is_compact_utf8() -> None:
    assert _core.encode_body({"a": "é", "b": [1]}) == '{"a":"é","b":[1]}'.encode()
    with pytest.raises(ValueError, match="JSON"):
        _core.encode_body({"a": float("nan")})


def test_compact_drops_none_only() -> None:
    assert _core.compact({"a": None, "b": 0, "c": "", "d": False}) == {"b": 0, "c": "", "d": False}


def test_decode_success() -> None:
    assert _core.decode_success(b'{"data":"x"}', wrapped=True) == "x"
    assert _core.decode_success(b'{"a":1}', wrapped=False) == {"a": 1}
    for body in (b"", b"[", b"\xff", b"[" * 100_000):
        with pytest.raises(TransportError, match="not valid JSON"):
            _core.decode_success(body, wrapped=False)
    for body in (b"[]", b'{"other":1}'):
        with pytest.raises(TransportError, match="no data"):
            _core.decode_success(body, wrapped=True)


def test_decode_response() -> None:
    assert _core.decode_response(200, "OK", b'{"data":1}', wrapped=True) == 1
    with pytest.raises(TransportError, match="redirect"):
        _core.decode_response(301, "Moved", b"", wrapped=True)
    with pytest.raises(ApiError) as caught:
        _core.decode_response(500, "", b"", wrapped=True)
    assert caught.value.problem.title == "HTTP error"


@given(st.integers(min_value=1, max_value=200), st.floats(0, 10), st.floats(0, 10))
def test_backoff_never_exceeds_the_cap(attempt: int, initial: float, cap: float) -> None:
    retry = RetryOptions(max_retries=attempt, initial_delay=initial, max_delay=cap)
    delay = _core.backoff_delay(attempt, retry)
    assert delay is not None
    assert 0 <= delay <= cap


@given(st.text())
def test_retry_after_never_raises(header: str) -> None:
    seconds = _core.retry_after_seconds(header, time.time())
    assert seconds is None or seconds >= 0


SHAPES_OK = [
    (types.HealthResult, {"status": "ok", "statusCode": 200, "uptime": 3}),
    (types.HealthResult, {"status": "ok", "statusCode": 200, "uptime": 3.5, "newMember": [1]}),
    (types.SharedSecret, {"algorithm": "a", "sharedSecret": "00"}),
    (types.KmsEncryptResult, {"keyId": "k", "provider": "p", "ciphertext": "c", "context": {}}),
    (types.Cbom, {"bomFormat": "CycloneDX", "specVersion": "1.6", "serialNumber": "s",
                  "version": 1, "metadata": {"any": [None]}, "components": []}),
    (str, "text"),
]  # fmt: skip


@pytest.mark.parametrize(("expected", "value"), SHAPES_OK)
def test_check_shape_accepts_the_documented_types(expected: object, value: object) -> None:
    assert check_shape(value, expected) is value


SHAPES_BAD = [
    (types.HealthResult, [], "data"),
    (types.HealthResult, {"status": "ok", "statusCode": 200}, "data.uptime"),
    (types.HealthResult, {"status": "degraded", "statusCode": 200, "uptime": 1}, "data.status"),
    (types.HealthResult, {"status": "ok", "statusCode": True, "uptime": 1}, "data.statusCode"),
    (types.HealthResult, {"status": "ok", "statusCode": 200.0, "uptime": 1}, "data.statusCode"),
    (types.HealthResult, {"status": "ok", "statusCode": 200, "uptime": "1"}, "data.uptime"),
    (types.ReadyResult, {"status": "ready", "checks": {"accepting": 1, "keyStore": True}},
     "data.checks.accepting"),
    (types.SharedSecret, {"algorithm": "a", "sharedSecret": "00", "combiner": 7}, "data.combiner"),
    (types.AlgorithmCatalogue, {"encryption": [], "hashing": [], "kdf": [], "keyExchange": [],
                                "mac": [], "postQuantum": [], "signing": ["ed25519", 3]},
     "data.signing[1]"),
    (types.KmsEncryptResult, {"keyId": "k", "provider": "p", "ciphertext": "c",
                              "context": {"a": 1}}, "data.context.a"),
    (types.KmsEncryptResult, {"keyId": "k", "provider": "p", "ciphertext": "c", "context": []},
     "data.context"),
    (types.StreamSignResult, {"count": 1, "signatures": {}}, "data.signatures"),
    (types.StreamSignResult, {"count": 1, "signatures": ["x"]}, "data.signatures[0]"),
    (str, {"plaintext": "secret-plaintext"}, "data"),
]  # fmt: skip


@pytest.mark.parametrize(("expected", "value", "where"), SHAPES_BAD)
def test_check_shape_names_the_member_not_the_value(
    expected: object, value: object, where: str
) -> None:
    with pytest.raises(TransportError, match="does not match the API") as caught:
        check_shape(value, expected)
    message = str(caught.value)
    assert message.endswith(f"at {where}")
    assert "secret" not in message
    assert "degraded" not in message
