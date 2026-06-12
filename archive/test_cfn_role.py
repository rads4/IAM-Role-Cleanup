import boto3

sts = boto3.client("sts")

response = sts.assume_role(
    RoleArn="arn:aws:iam::851043415728:role/IAMRoleCleanup",
    RoleSessionName="cfn-test"
)

creds = response["Credentials"]

session = boto3.Session(
    aws_access_key_id=creds["AccessKeyId"],
    aws_secret_access_key=creds["SecretAccessKey"],
    aws_session_token=creds["SessionToken"]
)

caller = session.client("sts")

print(
    caller.get_caller_identity()
)