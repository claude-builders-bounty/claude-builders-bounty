from pydantic import BaseModel, validator

def validate_input(data: dict, schema: type[BaseModel]):
    try:
        return schema(**data)
    except Exception as e:
        return {"error": str(e)}