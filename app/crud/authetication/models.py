from pydantic import Field, BaseModel, EmailStr, SecretStr


class UserSignin(BaseModel):
    email: EmailStr = Field(example="email@mail.com")
    password: SecretStr = Field(example="abc@1234#", exclude=True)
