from typing import Any, Dict, Optional

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from fastapi import FastAPI, Header, Response
from mangum import Mangum

logger = Logger()
app = FastAPI()

magnum_handler = Mangum(app, api_gateway_base_path="/smef")


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    return magnum_handler(event, context)


@app.get("/health/v1")
def get_health() -> dict[str, any]:
    return {"status": "pass"}


@app.get("/policy/classifiers/v1")
def get_policy_classifiers(response: Response, authorization: Optional[str] = Header(default=None)) -> dict[str, any]:
    return {
        "classifiers": []
    }


@app.get("/sme/search/v1")
def get_smes(response: Response, authorization: Optional[str] = Header(default=None)) -> dict[str, any]:
    return {
        "smes": []
    }
