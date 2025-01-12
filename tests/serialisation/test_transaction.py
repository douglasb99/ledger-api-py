import io
import json
import unittest
from unittest import mock

from fetchai.ledger.serialisation.transaction import encode_payload

from fetchai.ledger.bitvector import BitVector
from fetchai.ledger.crypto import Entity, Identity
from fetchai.ledger.serialisation import encode_transaction, decode_transaction, bytearray, sha256_hash
from fetchai.ledger.transaction import Transaction

_PRIVATE_KEYS = (
    '1411d53f88e736eac7872430dbe5b55ac28c17a3e648c388e0bd1b161ab04427',
    '3436c184890d498b25bc2b5cb0afb6bad67379ebd778eae1de40b6e0f0763825',
    '4a56a19355f934174f6388b3c80598abb151af79c23d5a7af45a13357fb71253',
    'f9d67ec139eb7a1cb1f627357995847392035c1e633e8530de5ab5d04c6e9c33',
    '80f0e1c69e5f1216f32647c20d744c358e0894ebc855998159017a5acda208ba',
)

ENTITIES = [Entity.from_hex(x) for x in _PRIVATE_KEYS]
IDENTITIES = [Identity(x) for x in ENTITIES]


def _calculate_integer_stream_size(length: int) -> int:
    if length < 0x80:
        return 1
    elif length < 0x100:
        return 2
    elif length < 0x1000:
        return 4
    else:
        return 8


class TransactionSerialisation(unittest.TestCase):
    EXPECTED_SIGNATURE_BYTE_LEN = 64
    EXPECTED_SIGNATURE_LENGTH_FIELD_LEN = _calculate_integer_stream_size(EXPECTED_SIGNATURE_BYTE_LEN)
    EXPECTED_SERIAL_SIGNATURE_LENGTH = EXPECTED_SIGNATURE_BYTE_LEN + EXPECTED_SIGNATURE_LENGTH_FIELD_LEN

    def test_simple_transfer(self):
        EXPECTED_DIGEST = "7fff24ca77fbb23b9b3c460104ab1a74011bafe3965e15dc6ea6f25a4ac44392"
        EXPECTED_PAYLOAD = \
            "a1440000532398dd883d1990f7dad3fde6a53a53347afc2680a04748f7f15ad03cadc4d44235130ac5aab442e39f" \
            "9aa27118956695229212dd2f1ab5b714e9f6bd581511c1010000000000000000000000000418c2a33af8bd2cba7f" \
            "a714a840a308a217aa4483880b1ef14b4fdffe08ab956e3f4b921cec33be7c258cfd7025a2b9a942770e5b17758b" \
            "cc4961bbdc75a0251c"

        # build the payload bytes for the transaction
        with mock.patch('random.getrandbits') as mock_counter:
            mock_counter.side_effect = [0]
            payload = Transaction()
        payload.from_address = IDENTITIES[0]
        payload.add_transfer(IDENTITIES[1], 256)
        payload.add_signer(IDENTITIES[0])

        # sign the final transaction
        transaction_bytes = encode_transaction(payload, [ENTITIES[0]])

        self.assertIsExpectedTx(payload, transaction_bytes, EXPECTED_PAYLOAD)

        # attempt to decode a transaction from the generated bytes
        buffer = io.BytesIO(transaction_bytes)
        success, tx = decode_transaction(buffer)

        self.assertTrue(success)
        self.assertTxAreEqual(payload, tx)

        # Check payload digest
        buffer = io.BytesIO()
        encode_payload(buffer, payload)
        self.assertEqual(sha256_hash(buffer.getvalue()), EXPECTED_DIGEST)

    def test_multiple_transfers(self):
        EXPECTED_DIGEST = "7e6a95a8c773755d349209d8f3bb60ec2a5f3c683075540f953863f124eb1250"
        EXPECTED_PAYLOAD = \
            "a1460000532398dd883d1990f7dad3fde6a53a53347afc2680a04748f7f15ad03cadc4d4014235130ac5aab442e3" \
            "9f9aa27118956695229212dd2f1ab5b714e9f6bd581511c1010020f478c7f74b50c187bf9a8836f382bd62977bae" \
            "eaf19625608e7e912aa60098c10200da2e9c3191e3768d1c59ea43f6318367ed9b21e6974f46a60d0dd8976740af" \
            "6dc2000186a000000000000000000000000418c2a33af8bd2cba7fa714a840a308a217aa4483880b1ef14b4fdffe" \
            "08ab956e3f4b921cec33be7c258cfd7025a2b9a942770e5b17758bcc4961bbdc75a0251c"

        # build the payload bytes for the transaction
        with mock.patch('random.getrandbits') as mock_counter:
            mock_counter.side_effect = [0]
            payload = Transaction()
        payload.from_address = IDENTITIES[0]
        payload.add_transfer(IDENTITIES[1], 256)
        payload.add_transfer(IDENTITIES[2], 512)
        payload.add_transfer(IDENTITIES[3], 100000)
        payload.add_signer(IDENTITIES[0])

        # sign the final transaction
        transaction_bytes = encode_transaction(payload, [ENTITIES[0]])

        self.assertIsExpectedTx(payload, transaction_bytes, EXPECTED_PAYLOAD)

        # attempt to decode a transaction from the generated bytes
        buffer = io.BytesIO(transaction_bytes)
        success, tx = decode_transaction(buffer)

        self.assertTrue(success)
        self.assertTxAreEqual(payload, tx)

        # Check payload digest
        buffer = io.BytesIO()
        encode_payload(buffer, payload)
        self.assertEqual(sha256_hash(buffer.getvalue()), EXPECTED_DIGEST)

    def test_synergetic_data_submission(self):
        EXPECTED_DIGEST = "9397fd490b60a394ea0af5526435608a1e853e2cb6b09bc7cafec8f6a0aa2cf6"
        EXPECTED_PAYLOAD = \
            "a140c000532398dd883d1990f7dad3fde6a53a53347afc2680a04748f7f15ad03cadc4d4c1271001c3000000e8d4" \
            "a5100080da2e9c3191e3768d1c59ea43f6318367ed9b21e6974f46a60d0dd8976740af6de6672a9d98da667e5dc2" \
            "5b2bca8acf9644a7ac0797f01cb5968abf39de011df204646174610f7b2276616c7565223a20313233347d000000" \
            "00000000000418c2a33af8bd2cba7fa714a840a308a217aa4483880b1ef14b4fdffe08ab956e3f4b921cec33be7c" \
            "258cfd7025a2b9a942770e5b17758bcc4961bbdc75a0251c"

        # build the payload bytes for the transaction
        with mock.patch('random.getrandbits') as mock_counter:
            mock_counter.side_effect = [0]
            payload = Transaction()
        payload.from_address = IDENTITIES[0]
        payload.valid_until = 10000
        payload.target_contract(IDENTITIES[3], IDENTITIES[4], BitVector())
        payload.charge_rate = 1
        payload.charge_limit = 1000000000000
        payload.action = 'data'
        payload.synergetic_data_submission = True
        payload.data = json.dumps({'value': 1234}).encode('ascii')
        payload.add_signer(IDENTITIES[0])

        # sign the final transaction
        transaction_bytes = encode_transaction(payload, [ENTITIES[0]])

        self.assertIsExpectedTx(payload, transaction_bytes, EXPECTED_PAYLOAD)

        # attempt to decode a transaction from the generated bytes
        buffer = io.BytesIO(transaction_bytes)
        success, tx = decode_transaction(buffer)

        self.assertTrue(success)
        self.assertTxAreEqual(payload, tx)

        # Check payload digest
        buffer = io.BytesIO()
        encode_payload(buffer, payload)
        self.assertEqual(sha256_hash(buffer.getvalue()), EXPECTED_DIGEST)

    def test_chain_code(self):
        EXPECTED_DIGEST = "7032dd625b0a93aec85fa03696d0ecbc9de19d834ce3fd1d1ed9cf8a56d9f62e"
        EXPECTED_PAYLOAD = \
            "a1408000532398dd883d1990f7dad3fde6a53a53347afc2680a04748f7f15ad03cadc4d400c103e8c2000f424080" \
            "0b666f6f2e6261722e62617a066c61756e636802676f00000000000000000418c2a33af8bd2cba7fa714a840a308" \
            "a217aa4483880b1ef14b4fdffe08ab956e3f4b921cec33be7c258cfd7025a2b9a942770e5b17758bcc4961bbdc75" \
            "a0251c"

        # build the payload bytes for the transaction
        with mock.patch('random.getrandbits') as mock_counter:
            mock_counter.side_effect = [0]
            payload = Transaction()
        payload.from_address = IDENTITIES[0]
        payload.add_signer(IDENTITIES[0])
        payload.charge_rate = 1000
        payload.charge_limit = 1000000
        payload.target_chain_code('foo.bar.baz', BitVector())
        payload.action = 'launch'
        payload.data = 'go'.encode('ascii')

        # sign the final transaction
        transaction_bytes = encode_transaction(payload, [ENTITIES[0]])

        self.assertIsExpectedTx(payload, transaction_bytes, EXPECTED_PAYLOAD)

        # attempt to decode a transaction from the generated bytes
        buffer = io.BytesIO(transaction_bytes)
        success, tx = decode_transaction(buffer)

        self.assertTrue(success)
        self.assertTxAreEqual(payload, tx)

        # Check payload digest
        buffer = io.BytesIO()
        encode_payload(buffer, payload)
        self.assertEqual(sha256_hash(buffer.getvalue()), EXPECTED_DIGEST)

    def test_smart_contract(self):
        EXPECTED_DIGEST = "032a72029ae2ac5cdbf9e07cf57d9ecab97a6de34ed5cdf785d1d98037cd5dcd"
        EXPECTED_PAYLOAD = \
            "a1404000532398dd883d1990f7dad3fde6a53a53347afc2680a04748f7f15ad03cadc4d400c103e8c2000f424080" \
            "da2e9c3191e3768d1c59ea43f6318367ed9b21e6974f46a60d0dd8976740af6de6672a9d98da667e5dc25b2bca8a" \
            "cf9644a7ac0797f01cb5968abf39de011df2066c61756e636802676f00000000000000000418c2a33af8bd2cba7f" \
            "a714a840a308a217aa4483880b1ef14b4fdffe08ab956e3f4b921cec33be7c258cfd7025a2b9a942770e5b17758b" \
            "cc4961bbdc75a0251c"

        # build the payload bytes for the transaction
        with mock.patch('random.getrandbits') as mock_counter:
            mock_counter.side_effect = [0]
            payload = Transaction()
        payload.from_address = IDENTITIES[0]
        payload.add_signer(IDENTITIES[0])
        payload.charge_rate = 1000
        payload.charge_limit = 1000000
        payload.target_contract(IDENTITIES[3], IDENTITIES[4], BitVector())
        payload.action = 'launch'
        payload.data = 'go'.encode('ascii')

        # sign the final transaction
        transaction_bytes = encode_transaction(payload, [ENTITIES[0]])

        self.assertIsExpectedTx(payload, transaction_bytes, EXPECTED_PAYLOAD)

        # attempt to decode a transaction from the generated bytes
        buffer = io.BytesIO(transaction_bytes)
        success, tx = decode_transaction(buffer)

        self.assertTrue(success)
        self.assertTxAreEqual(payload, tx)

        # Check payload digest
        buffer = io.BytesIO()
        encode_payload(buffer, payload)
        self.assertEqual(sha256_hash(buffer.getvalue()), EXPECTED_DIGEST)

    def test_validity_ranges(self):
        EXPECTED_DIGEST = "98f10e8aa0bf4507db9eca66f0ff0b6a3eff35fe4def9ed86150c7ce72e71e80"
        EXPECTED_PAYLOAD = \
            "a1470000532398dd883d1990f7dad3fde6a53a53347afc2680a04748f7f15ad03cadc4d4024235130ac5aab442e3" \
            "9f9aa27118956695229212dd2f1ab5b714e9f6bd581511c103e820f478c7f74b50c187bf9a8836f382bd62977bae" \
            "eaf19625608e7e912aa60098c103e8da2e9c3191e3768d1c59ea43f6318367ed9b21e6974f46a60d0dd8976740af" \
            "6dc103e8e6672a9d98da667e5dc25b2bca8acf9644a7ac0797f01cb5968abf39de011df2c103e864c0c8c103e8c2" \
            "000f424000000000000000000418c2a33af8bd2cba7fa714a840a308a217aa4483880b1ef14b4fdffe08ab956e3f" \
            "4b921cec33be7c258cfd7025a2b9a942770e5b17758bcc4961bbdc75a0251c"

        # build the payload bytes for the transaction
        with mock.patch('random.getrandbits') as mock_counter:
            mock_counter.side_effect = [0]
            payload = Transaction()
        payload.from_address = IDENTITIES[0]
        payload.add_transfer(IDENTITIES[1], 1000)
        payload.add_transfer(IDENTITIES[2], 1000)
        payload.add_transfer(IDENTITIES[3], 1000)
        payload.add_transfer(IDENTITIES[4], 1000)
        payload.add_signer(IDENTITIES[0])
        payload.charge_rate = 1000
        payload.charge_limit = 1000000
        payload.valid_from = 100
        payload.valid_until = 200

        # sign the final transaction
        transaction_bytes = encode_transaction(payload, [ENTITIES[0]])


        self.assertIsExpectedTx(payload, transaction_bytes, EXPECTED_PAYLOAD)

        # attempt to decode a transaction from the generated bytes
        buffer = io.BytesIO(transaction_bytes)
        success, tx = decode_transaction(buffer)

        self.assertTrue(success)
        self.assertTxAreEqual(payload, tx)

        # Check payload digest
        buffer = io.BytesIO()
        encode_payload(buffer, payload)
        self.assertEqual(sha256_hash(buffer.getvalue()), EXPECTED_DIGEST)

    def test_contract_with_2bit_shard_mask(self):
        EXPECTED_DIGEST = "8dbbee60c084b8ef88de39c961dec10df493c62623035972b28d1c5f1a3802a9"
        EXPECTED_PAYLOAD = \
            "a1418000532398dd883d1990f7dad3fde6a53a53347afc2680a04748f7f15ad03cadc4d464c0c8c103e8c2000f42" \
            "40010b666f6f2e6261722e62617a066c61756e63680000000000000000000418c2a33af8bd2cba7fa714a840a308" \
            "a217aa4483880b1ef14b4fdffe08ab956e3f4b921cec33be7c258cfd7025a2b9a942770e5b17758bcc4961bbdc75" \
            "a0251c"

        mask = BitVector(2)
        mask.set(0, 1)

        # build the payload bytes for the transaction
        with mock.patch('random.getrandbits') as mock_counter:
            mock_counter.side_effect = [0]
            payload = Transaction()
        payload.from_address = IDENTITIES[0]
        payload.add_signer(IDENTITIES[0])
        payload.charge_rate = 1000
        payload.charge_limit = 1000000
        payload.valid_from = 100
        payload.valid_until = 200
        payload.target_chain_code('foo.bar.baz', mask)
        payload.action = 'launch'

        # sign the final transaction
        transaction_bytes = encode_transaction(payload, [ENTITIES[0]])


        self.assertIsExpectedTx(payload, transaction_bytes, EXPECTED_PAYLOAD)

        # attempt to decode a transaction from the generated bytes
        buffer = io.BytesIO(transaction_bytes)
        success, tx = decode_transaction(buffer)

        self.assertTrue(success)
        self.assertTxAreEqual(payload, tx)

        # Check payload digest
        buffer = io.BytesIO()
        encode_payload(buffer, payload)
        self.assertEqual(sha256_hash(buffer.getvalue()), EXPECTED_DIGEST)

    def test_contract_with_4bit_shard_mask(self):
        EXPECTED_DIGEST = "7915d6393fb07dbb4ff6896ef0f57025e5153b744d3a652b0f4815f129a9033c"
        EXPECTED_PAYLOAD = \
            "a1418000532398dd883d1990f7dad3fde6a53a53347afc2680a04748f7f15ad03cadc4d464c0c8c103e8c2000f42" \
            "401c0b666f6f2e6261722e62617a066c61756e63680000000000000000000418c2a33af8bd2cba7fa714a840a308" \
            "a217aa4483880b1ef14b4fdffe08ab956e3f4b921cec33be7c258cfd7025a2b9a942770e5b17758bcc4961bbdc75" \
            "a0251c"

        mask = BitVector(4)
        mask.set(3, 1)
        mask.set(2, 1)

        # build the payload bytes for the transaction
        with mock.patch('random.getrandbits') as mock_counter:
            mock_counter.side_effect = [0]
            payload = Transaction()
        payload.from_address = IDENTITIES[0]
        payload.add_signer(IDENTITIES[0])
        payload.charge_rate = 1000
        payload.charge_limit = 1000000
        payload.valid_from = 100
        payload.valid_until = 200
        payload.target_chain_code('foo.bar.baz', mask)
        payload.action = 'launch'

        # sign the final transaction
        transaction_bytes = encode_transaction(payload, [ENTITIES[0]])


        self.assertIsExpectedTx(payload, transaction_bytes, EXPECTED_PAYLOAD)

        # attempt to decode a transaction from the generated bytes
        buffer = io.BytesIO(transaction_bytes)
        success, tx = decode_transaction(buffer)

        self.assertTrue(success)
        self.assertTxAreEqual(payload, tx)

        # Check payload digest
        buffer = io.BytesIO()
        encode_payload(buffer, payload)
        self.assertEqual(sha256_hash(buffer.getvalue()), EXPECTED_DIGEST)

    def test_contract_with_large_shard_mask(self):
        EXPECTED_DIGEST = "a4eff45d0374d29f259aba25fb06dd67394149b636927d199062102d91c0f7bf"
        EXPECTED_PAYLOAD = \
            "a1418000532398dd883d1990f7dad3fde6a53a53347afc2680a04748f7f15ad03cadc4d464c0c8c103e8c2000f42" \
            "4041eaab0b666f6f2e6261722e62617a066c61756e63680000000000000000000418c2a33af8bd2cba7fa714a840" \
            "a308a217aa4483880b1ef14b4fdffe08ab956e3f4b921cec33be7c258cfd7025a2b9a942770e5b17758bcc4961bb" \
            "dc75a0251c"

        mask = BitVector(16)
        mask.set(15, 1)
        mask.set(14, 1)
        mask.set(13, 1)
        mask.set(11, 1)
        mask.set(9, 1)
        mask.set(7, 1)
        mask.set(5, 1)
        mask.set(3, 1)
        mask.set(1, 1)
        mask.set(0, 1)

        # build the payload bytes for the transaction
        with mock.patch('random.getrandbits') as mock_counter:
            mock_counter.side_effect = [0]
            payload = Transaction()
        payload.from_address = IDENTITIES[0]
        payload.add_signer(IDENTITIES[0])
        payload.charge_rate = 1000
        payload.charge_limit = 1000000
        payload.valid_from = 100
        payload.valid_until = 200
        payload.target_chain_code('foo.bar.baz', mask)
        payload.action = 'launch'

        # sign the final transaction
        transaction_bytes = encode_transaction(payload, [ENTITIES[0]])


        self.assertIsExpectedTx(payload, transaction_bytes, EXPECTED_PAYLOAD)

        # attempt to decode a transaction from the generated bytes
        buffer = io.BytesIO(transaction_bytes)
        success, tx = decode_transaction(buffer)

        self.assertTrue(success)
        self.assertTxAreEqual(payload, tx)

        # Check payload digest
        buffer = io.BytesIO()
        encode_payload(buffer, payload)
        self.assertEqual(sha256_hash(buffer.getvalue()), EXPECTED_DIGEST)

    def test_invalid_magic(self):
        encoded = bytes([0x00])
        buffer = io.BytesIO(encoded)
        with self.assertRaises(RuntimeError):
            _, _ = decode_transaction(buffer)

    def test_invalid_version(self):
        encoded = bytes([0xA1, 0xEF, 0xFF])
        buffer = io.BytesIO(encoded)
        with self.assertRaises(RuntimeError):
            _, _ = decode_transaction(buffer)

    def assertIsExpectedTx(self, payload: Transaction, transaction_bytes: bytes, expected_hex_payload: str):
        # a payload needs at least one signee
        self.assertGreater(len(payload.signers), 0)

        # calculate the serial length of the signatures (so that we can extract the payload)
        signatures_serial_length = self.EXPECTED_SERIAL_SIGNATURE_LENGTH * len(payload.signers)

        # sanity check
        self.assertGreater(len(transaction_bytes), signatures_serial_length)

        expected_payload_end = len(transaction_bytes) - signatures_serial_length

        # extract and verify the payload
        payload_bytes = transaction_bytes[:expected_payload_end]
        self.assertEqual(expected_hex_payload, payload_bytes.hex())

        # loop through and verify all the signatures
        buffer = io.BytesIO(transaction_bytes[expected_payload_end:])
        for signee in payload.signers:
            # extract the signature from the stream
            signature = bytearray.decode(buffer)

            # validate the signature is correct for the payload
            self.assertTrue(signee.verify(payload_bytes, signature))

    def assertTxAreEqual(self, reference: Transaction, other: Transaction):
        self.assertEqual(reference.from_address, other.from_address)
        self.assertEqual(reference.transfers, other.transfers)
        self.assertEqual(reference.valid_from, other.valid_from)
        self.assertEqual(reference.valid_until, other.valid_until)
        self.assertEqual(reference.charge_rate, other.charge_rate)
        self.assertEqual(reference.charge_limit, other.charge_limit)
        self.assertEqual(reference.contract_digest, other.contract_digest)
        self.assertEqual(reference.contract_address, other.contract_address)
        self.assertEqual(reference.chain_code, other.chain_code)
        self.assertEqual(reference.action, other.action)
        self.assertEqual(reference.shard_mask, other.shard_mask)
        self.assertEqual(reference.data, other.data)
        self.assertEqual(reference.signers.keys(), other.signers.keys())
