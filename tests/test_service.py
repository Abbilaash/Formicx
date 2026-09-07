from __future__ import annotations

import pytest
from pydantic import ValidationError

from formicx import Service


def test_service_creation_defaults():
    svc = Service(name="github")

    assert svc.service_id.startswith("svc_")
    assert svc.name == "github"
    assert svc.capabilities == []
    assert svc.permissions == []
    assert svc.status == "active"


def test_service_with_capabilities_and_permissions():
    svc = Service(
        name="mail",
        capabilities=["send_email", "read_inbox"],
        permissions=["mail.send"],
        status="active",
    )

    assert svc.capabilities == ["send_email", "read_inbox"]
    assert svc.permissions == ["mail.send"]


def test_service_invalid_empty_name():
    with pytest.raises(ValidationError):
        Service(name="")


def test_service_serialization():
    svc = Service(
        name="browser",
        capabilities=["navigate", "click", "scrape"],
        permissions=["browser.read"],
    )

    json_str = svc.model_dump_json()
    assert "browser" in json_str

    deserialized = Service.model_validate_json(json_str)
    assert deserialized.service_id == svc.service_id
    assert deserialized.capabilities == ["navigate", "click", "scrape"]
