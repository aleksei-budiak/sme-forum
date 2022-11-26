from enum import Enum
from typing import Any, Dict

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.api_gateway_authorizer_event import (
    APIGatewayAuthorizerTokenEvent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext


class Effect(Enum):
    ALLOW = "Allow"
    DENY = "Deny"


logger = Logger()


@event_source(data_class=APIGatewayAuthorizerTokenEvent)
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: APIGatewayAuthorizerTokenEvent, _: LambdaContext) -> dict[str, Any]:
    return authorize(event)


def authorize(event: APIGatewayAuthorizerTokenEvent):
    token = event.get("authorizationToken")
    if not token:
        raise_unauthorized()
    try:
        principal_id = verify_token(token)
        return generate_policy(principal_id, Effect.ALLOW.value, event["methodArn"])
    except Exception as e:
        logger.info("invalid authorization token", exc_info=e)
        raise_unauthorized()


def verify_token(credentials: str) -> str:
    return "hackforgood" if credentials.endswith("hackforgood") else raise_unauthorized()


def raise_unauthorized():
    # Note: This exception pattern tells API Gateway to respond with HTTP 401
    raise Exception("Unauthorized")  # NOSONAR


def generate_policy(principal_id: str, effect: Effect, resource: str) -> Dict[str, Any]:
    logger.info(f"returning {effect} access policy for {principal_id}")
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": resource,
                }
            ],
        },
    }
