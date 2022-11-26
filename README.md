# sme-forum

# sme-forum app

## Prerequisites

1. [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) installed

## Build

```bash
make install build
```

## Verify
```bash
make check
```

## Deploy

1. Configure 'smef' aws profile using access key and token (from Miro)
```bash
aws configure --profile smef
```

2. Provision stack using sam
```bash
sam deploy --guided --profile smef
```
... using the following attributes

- Stack Name [sam-app]
- AWS Region [eu-west-2]
- default for the rest