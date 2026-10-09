import base64
import hashlib
import hmac


def generate_esewa_signature(message, secret_key):
    digest = hmac.new(
        secret_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    return base64.b64encode(digest).decode("utf-8")


def verify_esewa_signature(data, secret_key):
    signed_fields = data.get("signed_field_names", "")

    if not signed_fields:
        return False

    fields = signed_fields.split(",")

    if any(field not in data for field in fields):
        return False

    message = ",".join(
        f"{field}={data[field]}" for field in fields
    )

    expected_signature = generate_esewa_signature(
        message,
        secret_key,
    )

    return hmac.compare_digest(
        expected_signature,
        data.get("signature", ""),
    )