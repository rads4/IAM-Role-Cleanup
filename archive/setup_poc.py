import boto3
import json

iam = boto3.client("iam")
sts = boto3.client("sts")

ACCOUNT_ID = sts.get_caller_identity()["Account"]

# -------------------------------------------------
# OPERATOR ROLE
# -------------------------------------------------

role_name = "CKPOC-RoleDeletionOperator"

trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {
            "AWS": f"arn:aws:iam::{ACCOUNT_ID}:root"
        },
        "Action": "sts:AssumeRole"
    }]
}

try:
    iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy)
    )

    print(f"Created {role_name}")

except Exception:
    print(f"{role_name} already exists")

# -------------------------------------------------
# LEAST PRIVILEGE POLICY
# -------------------------------------------------

policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": [
            "iam:Get*",
            "iam:List*",
            "iam:DeleteRole",
            "iam:DeleteRolePolicy",
            "iam:DetachRolePolicy",
            "iam:RemoveRoleFromInstanceProfile"
        ],
        "Resource": "*"
    }]
}

iam.put_role_policy(
    RoleName=role_name,
    PolicyName="CKPOCDeleteRolesPolicy",
    PolicyDocument=json.dumps(policy)
)

roles = [
    "CKPOC-AppBackendRole",
    "CKPOC-EcsTaskRole",
    "CKPOC-LambdaExecutionRole",
    "CKPOC-AnalyticsRole",
    "CKPOC-ReadOnlyRole",
    "CKPOC-MonitoringRole",
    "CKPOC-DevOpsCIRole",
    "CKPOC-BatchProcessingRole",
    "CKPOC-DataEngineeringRole",
    "CKPOC-TemporaryRole"
]

managed = [
    "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
    "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess",
    "arn:aws:iam::aws:policy/AWSLambdaExecute",
    "arn:aws:iam::aws:policy/AmazonAthenaFullAccess",
    "arn:aws:iam::aws:policy/ReadOnlyAccess",
    "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess",
    "arn:aws:iam::aws:policy/AWSCodeBuildDeveloperAccess",
    "arn:aws:iam::aws:policy/AmazonSQSFullAccess",
    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
    "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
]

ec2_trust = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {
            "Service": "ec2.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
    }]
}

for role, policy_arn in zip(roles, managed):

    try:

        iam.create_role(
            RoleName=role,
            AssumeRolePolicyDocument=json.dumps(ec2_trust)
        )

        iam.attach_role_policy(
            RoleName=role,
            PolicyArn=policy_arn
        )

        if role in [
            "CKPOC-AppBackendRole",
            "CKPOC-AnalyticsRole",
            "CKPOC-DataEngineeringRole"
        ]:

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

        if role in [
            "CKPOC-EcsTaskRole",
            "CKPOC-LambdaExecutionRole",
            "CKPOC-MonitoringRole"
        ]:

            profile = role.replace("Role", "Profile")

            iam.create_instance_profile(
                InstanceProfileName=profile
            )

            iam.add_role_to_instance_profile(
                InstanceProfileName=profile,
                RoleName=role
            )

        print(f"Created {role}")

    except Exception as e:
        print(role, e)

print("POC setup completed")
