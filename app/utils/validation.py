from typing import Any, List

from fastapi import Request
from pydantic import BaseModel


class ValidationError(BaseModel):
    type: str
    value: str
    msg: str
    path: str
    location: str


def validate_body_dict(body: Any, required_fields: List[str]) -> List[ValidationError]:
    """
    Validate a parsed JSON object against required fields and field rules.
    Use with Request.json() or with Pydantic model_dump() so OpenAPI can still
    document the body via schema parameters.
    """
    errors: List[ValidationError] = []

    if not isinstance(body, dict):
        errors.append(
            ValidationError(
                type="body",
                value="",
                msg="Invalid JSON body",
                path="body",
                location="body",
            )
        )
        return errors

    # Check required fields
    for field in required_fields:
        if field not in body or not body[field]:
            errors.append(
                ValidationError(
                    type="field",
                    value="",
                    msg=f"{field.capitalize()} is required",
                    path=field,
                    location="body",
                )
            )

    # Validate email format if email is present
    if "email" in required_fields and "email" in body and body["email"]:
        email = body["email"]
        if "@" not in email or "." not in email:
            errors.append(
                ValidationError(
                    type="field",
                    value=email,
                    msg="Please enter a valid email address",
                    path="email",
                    location="body",
                )
            )

    # Validate password length if password is present
    if "password" in required_fields and "password" in body and body["password"]:
        password = body["password"]
        if len(password) < 6:
            errors.append(
                ValidationError(
                    type="field",
                    value="",  # Don't return password for security
                    msg="Password must be at least 6 characters long",
                    path="password",
                    location="body",
                )
            )

    return errors


async def validate_request_body(request: Request, required_fields: List[str]) -> List[ValidationError]:
    """
    Validate request body against required fields.
    Returns a list of validation errors if any.
    """
    try:
        body = await request.json()
    except Exception:
        return [
            ValidationError(
                type="body",
                value="",
                msg="Invalid JSON body",
                path="body",
                location="body",
            )
        ]

    return validate_body_dict(body, required_fields)
