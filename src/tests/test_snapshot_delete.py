import boto3

import pytest, sure
import lambda_function
from botocore.exceptions import ClientError
from moto import mock_ec2

@mock_ec2
def test_lambda_handler():
    client = boto3.client("ec2", region_name="us-east-1")
    ec2 = boto3.resource("ec2", region_name="us-east-1")
    volume = ec2.create_volume(Size=80, AvailabilityZone="us-east-1a")

    snapshot = volume.create_snapshot(Description="a test snapshot")
    snapshot.reload()
    snapshot.state.should.equal("completed")

    #Snapshot is 1day old, it should not be deleted by lambda_handler
    lambda_function.lambda_handler(None, None)
    current_snapshots = client.describe_snapshots()["Snapshots"]
    [s["SnapshotId"] for s in current_snapshots].should.contain(snapshot.id)

    # Test dry run
    with pytest.raises(ClientError) as ex:
        lambda_function.delete_snapshot(current_snapshots[0]["SnapshotId"], client, True)
    ex.value.response["Error"]["Code"].should.equal("DryRunOperation")
    ex.value.response["Error"]["Message"].should.equal(
        "An error occurred (DryRunOperation) when calling the DeleteSnapshot operation: Request would have succeeded, but DryRun flag is set"
    )



@mock_ec2
def test_delete_snapshot():
    client = boto3.client("ec2", region_name="us-east-1")
    ec2 = boto3.resource("ec2", region_name="us-east-1")
    volume = ec2.create_volume(Size=80, AvailabilityZone="us-east-1a")

    snapshot = volume.create_snapshot(Description="a test snapshot")
    snapshot.reload()
    snapshot.state.should.equal("completed")

    #Snapshot can be deleted by delete_snapshot
    lambda_function.delete_snapshot(snapshot.id, client)
    current_snapshots = client.describe_snapshots()["Snapshots"]
    [s["SnapshotId"] for s in current_snapshots].shouldnt.contain(snapshot.id)

    with pytest.raises(ClientError) as ex:
        lambda_function.delete_snapshot(snapshot.id, client)
    ex.value.response["Error"]["Code"].should.equal("InvalidSnapshot.NotFound")

    with pytest.raises(ClientError) as ex:
        lambda_function.delete_snapshot(current_snapshots[0]["SnapshotId"], client)
    ex.value.response["Error"]["Code"].shouldnt.equal("InvalidSnapshot.NotFound")
