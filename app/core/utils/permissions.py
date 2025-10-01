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
                "product_additional:create",
                "product_additional:delete",
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

    # if role == RoleEnum.MANAGER:
    #     return permissions

    # Admin
    permissions = permissions.union(
        set(
            [
                "user:create",
                "user:delete",
                "organization:update",
                "billing:get",
                "organization_plan:get",
                "menu:create",
                "menu:delete",
                "section:create",
                "section:delete",
                "offer:create",
                "offer:delete",
                "pre-order:create",
                "pre-order:delete",
                "business_day:update",
            ]
        )
    )

    if role in [RoleEnum.ADMIN, RoleEnum.MANAGER]:
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
