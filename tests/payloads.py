import jwt
from datetime import timedelta

from app.core.utils.utc_datetime import UTCDateTime
from app.crud.users.schemas import UserInDB


MOCKED_AUTH_RESULT: dict = {
    "iat":  int(UTCDateTime.now().timestamp()),
    "exp": int((UTCDateTime.now() + timedelta(hours=1)).timestamp()),
    "given_name":"Test",
    "family_name":"User",
    "nickname":"test-user",
    "name":"Test User",
    "picture":None,
    "updated_at":"2025-06-29T00:57:27.621Z",
    "email":"test@email.com",
    "email_verified": True,
    "iss":"https://test.com/",
    "aud":"WER6ZuDFJUqQiCjSlqVfhhNVAk4QGi4a",
    "sub":"google-oauth2|1235462",
    "sid":"_LyKmwgnBlG3R3wLoN4NUFkDRAlBzvAW",
    "token": "token"
}


MOCKED_JWT_TOKEN = jwt.encode(MOCKED_AUTH_RESULT, key="test", algorithm="HS256")


USER_IN_DB: UserInDB = UserInDB(
    user_id="google-oauth2|1235462",
    name="Test User",
    nickname="Test User",
    email="test@email.com",
    created_at=UTCDateTime.now(),
    updated_at=UTCDateTime.now(),
)
