from pydantic import ConfigDict, BaseModel


def convert_field_to_camel_case(string: str) -> str:
    return "".join(
        word if index == 0 else word.capitalize()
        for index, word in enumerate(string.split("_"))
    )


class GenericModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=convert_field_to_camel_case
    )
