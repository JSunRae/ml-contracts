from tools.export_manifest_hash import compute_manifest_hash


def test_manifest_hash_matches_expected():
    assert compute_manifest_hash() == "5ecfc0f11c556ae30c6286dbef1bd0c1791a6e021d5aa2221f6ee440a36ded14"
