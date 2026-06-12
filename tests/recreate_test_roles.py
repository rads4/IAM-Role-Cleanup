import boto3
import json

iam = boto3.client("iam")

roles = [
    (
        "CFN-Test-AppRole",
        "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
    ),
    (
        "CFN-Test-AnalyticsRole",
        "arn:aws:iam::aws:policy/ReadOnlyAccess"
    ),
    (
        "CFN-Test-MonitoringRole",
        "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess"
    )
]

trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {
            "Service": "ec2.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
    }]
}

inline_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": "s3:ListBucket",
        "Resource": "*"
    }]
}

for role_name, managed_policy in roles:

    try:

        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(
                trust_policy
            )
        )

        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn=managed_policy
        )

        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="TestInlinePolicy",
            PolicyDocument=json.dumps(
                inline_policy
            )
        )

        print(
            f"Created {role_name}"
        )

    except Exception as e:

        print(
            f"{role_name}: {e}"
        )