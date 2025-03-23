from typing import Set

from app.crud.shared_schemas.roles import RoleEnum


def get_role_permissions(role: RoleEnum) -> Set[str]:
    # Only superusers
    # user:get

    # Everyone 
    # organization:create

    # Member permissions
    permissions = set(
        [
            "tag:get",
            "product:get",
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
        ]
    )

    if role == RoleEnum.MEMBER:
        return permissions

    # Manager roles
    permissions = permissions.union(
        set(
            [
                "tag:create",
                "tag:delete",
                "product:create",
                "product:delete",
                "file:create",
                "file:delete",
                "payment:create",
                "payment:delete",
                "member:add",
                "member:remove",
                "order:delete",
                "invite:create",
                "invite:get",
                "fast_order:delete",
                "expense:delete",
                "customer:delete"
            ]
        )
    )

    if role == RoleEnum.MANAGER:
        return permissions

    # Admin
    permissions = permissions.union(
        set(
            [
                "user:create",
                "user:delete",
                "organization:update",
                "billing:get",
                "organization_plan:get"
            ]
        )
    )

    if role == RoleEnum.ADMIN:
        return permissions

    # Owner
    permissions = permissions.union(
        set(
            [
                "organization:delete",
                "organization_plan:create",
                "organization_plan:delete",
                "subscription:create",
                "subscription:delete",
            ]
        )
    )

    return permissions
