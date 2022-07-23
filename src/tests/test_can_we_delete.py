import lambda_function

snapshot = {
    "Snapshots": [
        {
            "Description": "Fake snapshot",
            "SnapshotId": "snap-0151drtr",
            "StartTime": "2022-06-29T06:01:18.671000+00:00",
            "Tags": [
                {
                    "Key": "persistence",
                    "Value": "do-not-delete"
                }
            ],
        },
        {
            "Description": "Fake snapshot",
            "SnapshotId": "snap-03ddas12645012ce",
            "StartTime": "2022-06-29T06:01:18.671000+00:00",
            "Tags": [],
        },
        {
            "Description": "Fake snapshot",
            "SnapshotId": "snap-03ddas12645012ce",
            "StartTime": "2020-06-29T06:01:18.671000+00:00",
            "Tags": [],
        },
    ]
}

snapshots = snapshot["Snapshots"]



def test_cannot_delete_tag():
  # There is do-not-delete tag and age >= 365 should not delete
  assert lambda_function.can_we_delete(snapshots[0], 366) is False

  # no do-not-delete-tag and age >= 365 should not delete
  assert lambda_function.can_we_delete(snapshots[1], 364) is False


def test_can_delete():
  # no do-not-delete-tag and age >= 365 should delete
  assert lambda_function.can_we_delete(snapshots[1], 366) is True
