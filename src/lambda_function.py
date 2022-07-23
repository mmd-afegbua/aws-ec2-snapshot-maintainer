import os
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

# ALL SNAPSHOTS OLDER THAN NUMBER OF DAYS WILL BE DELETED
SNAPSHOT_RETENTION_DEFAULT = int(os.getenv("SNAPSHOT_RETENTION", default="365"))

dryrun = bool(eval(os.getenv("DRYRUN", default="False")))

# AWS_REGIONS - list of regions to process
AWS_REGIONS_DEFAULT = 'us-east-1,us-west-2'
regions = [region.strip() for region in os.getenv('AWS_REGIONS', default=AWS_REGIONS_DEFAULT).split(',')]


def can_we_delete(snapshot, age):
    if 'Tags' in snapshot and [tag for tag in snapshot['Tags'] if tag['Key'] == 'persistence' and tag['Value'] == 'do-not-delete']:
        return False
    if age<=SNAPSHOT_RETENTION_DEFAULT:
        return False
    return True


def lambda_handler(event, context):
    # Boto3 client for ec2
    for region in regions:
        ec2 = boto3.client('ec2',region_name=region)

        # Get snapshots
        snapshots = ec2.describe_snapshots(OwnerIds=['self'])

        for snapshot in snapshots['Snapshots']:
            # If it has a do-not-delette tag, skip it.
            age=datetime.now().date() - snapshot['StartTime'].date()
            if not can_we_delete(snapshot, age.days):
                continue

            print(f"The snapshot: {snapshot['SnapshotId']} is {str(age.days)} old and will be deleted.")
            delete_snapshot(snapshot['SnapshotId'], ec2, dryrun)
            continue

def delete_snapshot(snapshotid, ec2, is_dryrun=False):
    try:
        ec2.delete_snapshot(SnapshotId=snapshotid, DryRun=is_dryrun)
        print(f"Snapshot: {snapshotid} has been deleted^^^^^^")
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "InvalidSnapshot.InUse":
            print(f"{snapshotid} Is in use. Skipping it.")
            raise
        elif error_code == "InvalidSnapshot.NotFound":
            print(f"Unexpected error: {snapshotid} NotFound. Ensure you are running as owner ")
            raise
        elif error_code == "DryRunOperation":
            print("Unexpected error: {}".format(e))
            raise
        else:
            print("Unexpected error: {}".format(e))
            raise

if __name__ == "__main__":
  lambda_handler(None, None)
