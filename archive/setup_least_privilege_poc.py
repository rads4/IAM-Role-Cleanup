import boto3
import json

iam = boto3.client("iam")
sts = boto3.client("sts")

account_id = sts.get_caller_identity()["Account"]

ROLE_NAME = "CKPOC-LeastPrivilegeOperator"

trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {
            "AWS": f"arn:aws:iam::{account_id}:user/admin"
        },
        "Action": "sts:AssumeRole"
    }]
}

least_privilege_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Sid": "RoleDeletionOperations",
        "Effect": "Allow",
        "Action": [
            "iam:GetRole",
            "iam:ListRoles",
            "iam:ListAttachedRolePolicies",
            "iam:DetachRolePolicy",
            "iam:ListRolePolicies",
            "iam:DeleteRolePolicy",
            "iam:ListInstanceProfilesForRole",
            "iam:RemoveRoleFromInstanceProfile",
            "iam:DeleteRole"
        ],
        "Resource": "*"
    }]
}

try:
    iam.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument=json.dumps(trust_policy)
    )
    print(f"Created role: {ROLE_NAME}")

except Exception:
    print(f"{ROLE_NAME} already exists")

iam.put_role_policy(
    RoleName=ROLE_NAME,
    PolicyName="CKPOCLeastPrivilegePolicy",
    PolicyDocument=json.dumps(least_privilege_policy)
)

print("Attached least privilege policy")

roles = [
    "CKPOC-LP-AppRole",
    "CKPOC-LP-AnalyticsRole",
    "CKPOC-LP-MonitoringRole"
]

policy_arns = [
    "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
    "arn:aws:iam::aws:policy/ReadOnlyAccess",
    "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess"
]

trust = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {
            "Service": "ec2.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
    }]
}

for role, policy in zip(roles, policy_arns):

    try:

        iam.create_role(
            RoleName=role,
            AssumeRolePolicyDocument=json.dumps(trust)
        )

        iam.attach_role_policy(
            RoleName=role,
            PolicyArn=policy
        )

        iam.put_role_policy(
            RoleName=role,
            PolicyName="CKPOCInlinePolicy",
            PolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": "s3:ListBucket",
                    "Resource": "*"
                }]
            })
        )

        print(f"Created {role}")

    except Exception as e:
        print(role, e)

print("Least privilege validation setup complete")