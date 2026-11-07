"""Run the Terraform-defined one-off migration task; fail unless its container exits zero."""

import argparse
import json
import subprocess

import boto3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terraform-directory", default="infrastructure/terraform")
    parser.add_argument("--region", default="af-south-1")
    args = parser.parse_args()
    outputs = json.loads(
        subprocess.check_output(
            ["terraform", f"-chdir={args.terraform_directory}", "output", "-json"]
        )
    )

    def value(key):
        return outputs[key]["value"]

    client = boto3.client("ecs", region_name=args.region)
    response = client.run_task(
        cluster=value("cluster_name"),
        taskDefinition=value("migration_task_definition"),
        launchType="FARGATE",
        platformVersion="1.4.0",
        count=1,
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": value("private_subnet_ids"),
                "securityGroups": [value("task_security_group_id")],
                "assignPublicIp": "DISABLED",
            }
        },
    )
    if response.get("failures") or len(response.get("tasks", [])) != 1:
        raise SystemExit("Migration task could not start; inspect ECS service events.")
    arn = response["tasks"][0]["taskArn"]
    print(f"Waiting for migration task {arn}", flush=True)
    client.get_waiter("tasks_stopped").wait(
        cluster=value("cluster_name"), tasks=[arn], WaiterConfig={"Delay": 10, "MaxAttempts": 180}
    )
    task = client.describe_tasks(cluster=value("cluster_name"), tasks=[arn])["tasks"][0]
    containers = task.get("containers", [])
    if not containers or any(c.get("exitCode") != 0 for c in containers):
        raise SystemExit(
            "Migration failed; inspect the migrate stream in CloudWatch before deploying services."
        )
    print("Migration succeeded. Services can now be enabled with Terraform.")


if __name__ == "__main__":
    main()
