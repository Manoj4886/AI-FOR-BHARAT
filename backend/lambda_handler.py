"""
AWS Lambda handler — wraps the FastAPI app using Mangum.

Deploy steps:
  1.  pip install -r requirements.txt -t ./package
  2.  cp -r *.py routers/ services/ package/
  3.  cd package && zip -r ../lambda.zip .
  4.  Upload lambda.zip → AWS Lambda (Python 3.11 runtime)
  5.  Set Handler: lambda_handler.handler
  6.  Set all environment variables (see .env.example)
  7.  Attach API Gateway (HTTP API) trigger
  8.  Add execution role with:
        - AmazonBedrockFullAccess (or bedrock:InvokeModel)
        - AmazonPollyFullAccess
        - AmazonS3ReadOnlyAccess (if serving avatar from S3)
"""

from mangum import Mangum
from main import app

# Mangum adapts ASGI (FastAPI) to Lambda's event/context interface
handler = Mangum(app, lifespan="off")
