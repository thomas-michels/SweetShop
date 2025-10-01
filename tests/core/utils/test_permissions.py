from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.core.utils.permissions import get_role_permissions
from app.crud.shared_schemas.roles import RoleEnum


@pytest.fixture(scope="module")
def base_permissions() -> set[str]:
    return {
        "tag:get",
        "product:get",
        "product_additional:get",
        "user:me",
        "payment:get",
        "order:create",
        "order:get",
        "fast_order:create",
        "fast_order:get",
        "expense:create",
        "expense:get",
        "customer:create",
        "customer:get",
        "subscription:get",
        "calendar:get",
        "section:get",
        "pre-order:get",
        "business_day:get",
    }


def test_member_has_only_base_permissions(base_permissions: set[str]) -> None:
    assert get_role_permissions(RoleEnum.MEMBER) == base_permissions


def test_manager_inherits_manager_and_admin_permissions(base_permissions: set[str]) -> None:
    permissions = get_role_permissions(RoleEnum.MANAGER)

    assert base_permissions.issubset(permissions)
    assert "tag:create" in permissions
    assert "user:create" in permissions  # admin-level permission shared with managers
    assert "organization:delete" not in permissions


def test_admin_has_management_permissions_but_not_owner_specific() -> None:
    permissions = get_role_permissions(RoleEnum.ADMIN)

    assert "tag:create" in permissions
    assert "organization:update" in permissions
    assert "organization:delete" not in permissions


def test_owner_has_full_permission_set_including_owner_specific() -> None:
    permissions = get_role_permissions(RoleEnum.OWNER)

    assert "organization:delete" in permissions
    assert "subscription:create" in permissions
    assert "subscription:delete" in permissions
