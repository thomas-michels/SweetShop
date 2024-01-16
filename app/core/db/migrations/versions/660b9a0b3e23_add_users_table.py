"""add-users-table

Revision ID: 660b9a0b3e23
Revises: 
Create Date: 2024-01-07 23:56:02.137277

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.configs import get_environment

_env = get_environment()


# revision identifiers, used by Alembic.
revision: str = '660b9a0b3e23'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(f"""
CREATE TABLE {_env.ENVIRONMENT}.users (
	id serial4 NOT NULL,
	first_name varchar(30) NOT NULL,
	last_name varchar(50) NOT NULL,
	email varchar(50) NOT NULL,
	"password" varchar(100) NOT NULL,
	created_at timestamp with time zone NOT NULL,
	updated_at timestamp with time zone NOT NULL,
    is_active boolean NOT NULL;
	CONSTRAINT users_pk PRIMARY KEY (id),
	CONSTRAINT users_un UNIQUE (email)
);
""")


def downgrade() -> None:
    pass
