import base64

from nacl.public import PrivateKey, SealedBox

from strategy.github_secrets import _encrypt


def test_encrypt_round_trips_with_the_matching_private_key():
    private_key = PrivateKey.generate()
    public_key_b64 = base64.b64encode(private_key.public_key.encode()).decode()

    encrypted = _encrypt(public_key_b64, "my-secret-value")

    decrypted = SealedBox(private_key).decrypt(base64.b64decode(encrypted))

    assert decrypted.decode() == "my-secret-value"


def test_encrypt_output_differs_from_plaintext():
    private_key = PrivateKey.generate()
    public_key_b64 = base64.b64encode(private_key.public_key.encode()).decode()

    encrypted = _encrypt(public_key_b64, "another-secret")

    assert "another-secret" not in encrypted
