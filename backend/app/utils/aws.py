import boto3

from enum import Enum
from typing import Any

from redis.asyncio import Redis


class CacheMethod(str, Enum):
    GET = "GET"
    POST = "POST"


async def get_cached_presigned_obj(
    object_key: str, redis_client: Redis, method: CacheMethod
) -> tuple[str, Any]:
    cache_key = f"{object_key}:{method.value}"
    cached_obj = await redis_client.get(cache_key)

    return cache_key, cached_obj


async def generate_presigned_get_url(
    bucket_name: str, object_key: str, expire_in_secs: int, redis_client: Redis
) -> str:
    # cache -> {cache_key: GET url}
    cache_key = f"{object_key}:GET"

    session = boto3.Session(profile_name="saml-east")
    s3_client = session.client("s3")

    url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": bucket_name,
            "Key": object_key,
        },
        ExpiresIn=expire_in_secs,
    )

    await redis_client.set(cache_key, url, ex=(expire_in_secs - 2))

    # presigned url
    return url  # type: ignore


def delete_object(bucket_name: str, object_key: str) -> None:
    session = boto3.Session(profile_name="saml-east")
    s3_client = session.client("s3")

    s3_client.delete_object(Bucket=bucket_name, Key=object_key)
