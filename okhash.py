import hashlib
import math
from io import BytesIO

DEFAULT_K = 2
SHA256_DIGEST_LEN = 32


def _calculate_next_position(m, size):
    # Calculate the address bits size
    address_len = int(math.log2(size)) + 1

    # Get the current digest of m as bytes
    digest_bytes = m.digest()

    # Calculate the number of bytes needed to reach the address_len
    bytes_needed = (address_len + 7) // 8  # Ceiling division

    # Calculate the number of bytes in the current digest
    current_bytes_len = len(digest_bytes)

    # Keep adding more bytes to the digest until it's long enough
    while (current_bytes_len * 8) < address_len:
        # Create a new hash based on the previous hash and size
        m = hashlib.sha256(digest_bytes.hex().encode('utf-8') + str(size).encode('utf-8'))
        digest_bytes += m.digest()
        current_bytes_len += len(m.digest())

    # Extract the address bytes and convert to an integer
    address_bytes = digest_bytes[:bytes_needed]
    address = int.from_bytes(address_bytes, byteorder='big')

    # Return the address modulo size
    return address % size


def _sub_okhash(k, input_stream, input_size, base_size):
    input_stream.seek(0)
    if input_size <= base_size * 2:
        return sha256(input_stream)
    block_size = 1024 * math.ceil(2 ** (6 * k) / 1024)
    count = math.ceil(base_size / block_size)

    m = hashlib.sha256()
    m.update(str(input_size).encode('utf-8'))

    for _ in range(count):
        position = _calculate_next_position(m, input_size)
        input_stream.seek(position)
        data = input_stream.read(block_size)
        m.update(data)

    return m.digest()


def okhash(input_stream, input_size=None, K=DEFAULT_K):
    if K < 1:
        raise ValueError("K must be at least 1")

    if input_stream is None:
        raise ValueError("Input stream cannot be None")

    if isinstance(input_stream, (str, bytes)):
        if isinstance(input_stream, str):
            input_stream = bytes(input_stream, encoding='utf-8')
        input_size = len(input_stream)
        input_stream = BytesIO(input_stream)

    elif not (hasattr(input_stream, 'read') and hasattr(input_stream, 'seek') and hasattr(input_stream, 'tell')):
        raise ValueError("Input stream must be a bytes-like file object, str, or bytes")

    if input_size is None:
        input_stream.seek(0, 2)
        input_size = input_stream.tell()
        input_stream.seek(0)

    # downgrade K
    base_sizes = [2 ** (10 * k) for k in range(1, K + 1)]
    K = _downgrade_k(input_size, K, base_sizes)

    return b''.join(_sub_okhash(k, input_stream, input_size, base_sizes[k - 1]) for k in range(1, K + 1))


def _downgrade_k(input_size, K, base_sizes):
    for i, base_size in enumerate(base_sizes):
        if input_size <= base_size:
            return i + 1
    return K


def okhash_filepath(filepath, K=DEFAULT_K):
    with open(filepath, 'rb') as fin:
        return okhash(fin, K=K)


def compare_okhashes(hash1, hash2):  # , K=None):
    # how to check with the same K level, and check if K is downgradable?
    # if K is None:
    # Deduce K from the size of the smallest hash
    K = min(len(hash1), len(hash2)) // SHA256_DIGEST_LEN

    digest_len = K * SHA256_DIGEST_LEN

    if len(hash1) < digest_len or len(hash2) < digest_len:
        return False

    # Crop the first K * SHA256_DIGEST_LEN bytes from both hashes
    cropped_hash1 = hash1[:digest_len]
    cropped_hash2 = hash2[:digest_len]

    # Compare the cropped hashes
    return cropped_hash1 == cropped_hash2


def sha256(input_stream, chunk_size=8192):
    sha256_hash = hashlib.sha256()

    while True:
        data = input_stream.read(chunk_size)
        if not data:
            break
        sha256_hash.update(data)

    return sha256_hash.digest()
