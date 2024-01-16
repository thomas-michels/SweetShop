-- name: create_user<!
INSERT INTO public.users
(first_name, last_name, email, "password", is_active, created_at, updated_at)
VALUES(:first_name, :last_name, :email, :password, true, NOW(), NOW())
RETURNING id, first_name, last_name, email, "password", is_active, created_at, updated_at;

-- name: select_users
SELECT
	id,
	first_name,
	last_name,
	email,
	"password",
	is_active,
	created_at,
	updated_at
FROM
	public.users
WHERE
	is_active is true;

-- name: select_user_by_id^
SELECT
	id,
	first_name,
	last_name,
	email,
	"password",
	is_active,
	created_at,
	updated_at
FROM
	public.users u
WHERE
	u.id = :id
	AND is_active is true;

-- name: update_user_by_id<!
UPDATE
	public.users
SET
	first_name = :first_name,
	last_name = :last_name,
	email = :email,
	updated_at = NOW()
WHERE
	id = :id
	AND is_active is true
RETURNING id, first_name, last_name, email, "password", is_active, created_at, updated_at;

-- name: delete_user_by_id<!
UPDATE
	public.users
SET
	is_active = false,
	updated_at = NOW()
WHERE
	id = :id
	AND is_active is true
RETURNING id, first_name, last_name, email, "password", is_active, created_at, updated_at;
