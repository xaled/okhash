import hashlib
import math
import re
import sys
from io import BytesIO
import argparse
from os.path import exists
from typing import BinaryIO

VERSION = '1.0'
DEFAULT_K = 2
SHA256_DIGEST_LEN = 32
status_code = 0
format_errors, file_errors, checksum_errors = 0, 0, 0
args: argparse.Namespace | None = None


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


def okhash(
        input_stream: BinaryIO | str | bytes,
        input_size=None,
        K=DEFAULT_K  # noqa
):
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


def _downgrade_k(
        input_size,
        K,  # noqa
        base_sizes
):
    for i, base_size in enumerate(base_sizes):
        if input_size <= base_size:
            return i + 1
    return K


def okhash_filepath(  # noqa
        filepath,
        K=DEFAULT_K  # noqa
):
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


def load_hash_files(filepath):
    global status_code, format_errors
    try:
        with open(filepath) as fin:
            lines = fin.readlines()
    except PermissionError as e:
        print(f"okhash.py: {filepath}: Permission denied", file=sys.stderr)
        status_code = 1
        return []

    result = list()

    def _validate_hash(_hash):
        hex_pattern = re.compile(r'^[0-9a-fA-F]+$')

        if not hex_pattern.match(_hash):
            return False

        if not _hash or len(_hash) % 64 != 0:
            return False

        return True

    for ix, line in enumerate(lines):
        skip, error = False, False
        if not line.strip():
            continue

        splits = line.split()
        if len(splits) != 2:
            error = True

        if not len(splits) >= 2 or not _validate_hash(splits[0]):
            error, skip = True, True

        if error:
            format_errors += 1
            if not args.quiet:
                print(f"okhash.py: {filepath}: {ix + 1}: improperly formatted O(K)hash checksum line",
                      file=sys.stderr)
            if args.strict:
                status_code = 1

        if not skip:
            result.append((bytes.fromhex(splits[0]), splits[1]))

    return result


def parse_args():
    global args
    parser = argparse.ArgumentParser(
        description="Print or check O(K)Hash checksums.",
        usage="python3 -m okhash [OPTION]... [FILE]...",
        epilog="""The hashes are computed as described in https://github.com/xaled/okhash.  When checking, the input
should be a former output of this program.  The default mode is to print a
line with checksum, a space, and name for each FILE.
"""
    )

    parser.add_argument(
        '-K',
        type=int,
        default=2,
        help='Strength of the Hash'
    )

    parser.add_argument(
        '-c', '--check',
        action='store_true',
        help='read O(K)Hash sums from the FILEs and check them'
    )

    parser.add_argument(
        '-z', '--zero',
        action='store_true',
        help='end each output line with NUL, not newline, and disable file name escaping'
    )

    verify_group = parser.add_argument_group(title='Useful only when verifying checksums')
    verify_group.add_argument(
        '--ignore-missing',
        action='store_true',
        help="don't fail or report status for missing files"
    )

    verify_group.add_argument(
        '--quiet',
        action='store_true',
        help="don't print OK for each successfully verified file"
    )

    verify_group.add_argument(
        '--status',
        action='store_true',
        help="don't output anything, status code shows success"
    )

    verify_group.add_argument(
        '--strict',
        action='store_true',
        help="exit non-zero for improperly formatted checksum lines"
    )

    verify_group.add_argument(
        '-w', '--warn',
        action='store_true',
        help="warn about improperly formatted checksum lines"
    )

    parser.add_argument(
        '--version',
        action='version',
        version='O(K)hash version ' + VERSION,
        help='output version information and exit'
    )

    parser.add_argument(
        'files',
        metavar='FILE',
        nargs='*',
        default=['-'],
        help='Files to compute or check O(K)hashes (default: stdin)'
    )

    return parser.parse_args()


def main():
    global status_code, args, format_errors, file_errors, checksum_errors

    def _read_stdin():
        data = b''
        while True:
            chunk = sys.stdin.buffer.read(1024 * 1024)
            if not chunk:
                break
            data += chunk

        return data

    def _print_result(_filepath, _result):
        if args.status:
            return

        if args.quiet and _result == 'OK':
            return

        print(f"{_filepath}: {_result}")

    args = parse_args()
    filepaths = args.files

    for filepath in filepaths:
        format_errors, file_errors, checksum_errors = 0, 0, 0

        if not exists(filepath):
            print(f"okhash.py: {filepath}: No such file or directory", file=sys.stderr)
            status_code = 1
            continue

        if args.check:
            entries = load_hash_files(filepath)

            for expected_hash, entry_filepath in entries:
                if not exists(entry_filepath):
                    print(f"okhash.py: {entry_filepath}: No such file or directory", file=sys.stderr)
                    if not args.ignore_missing:
                        _print_result(entry_filepath, 'FAILED open or read')
                        file_errors += 1
                    status_code = 1
                    continue

                try:
                    calculated_hash = okhash_filepath(entry_filepath, K=args.K)

                    if compare_okhashes(expected_hash, calculated_hash):
                        _print_result(entry_filepath, 'OK')
                    else:
                        _print_result(entry_filepath, 'FAILED')
                        checksum_errors += 1
                        status_code = 1
                except PermissionError as e:
                    print(f"okhash.py: {entry_filepath}: Permission denied", file=sys.stderr)
                    _print_result(entry_filepath, 'FAILED open or read')
                    file_errors += 1
                    status_code = 1

                # test_files/file2_1024.bin: FAILED open or read

            if not args.status:
                if format_errors:
                    # okhash.py: WARNING: 1 line is improperly formatted
                    print(f"okhash.py: WARNING: {format_errors} lines is improperly formatted", file=sys.stderr)

                if file_errors:
                    # okhash.py: WARNING: 1 listed file could not be read
                    print(f"okhash.py: WARNING: {file_errors} listed files could not be read", file=sys.stderr)

                if checksum_errors and not args.ignore_missing:
                    # okhash.py: WARNING: 1 computed checksum did NOT match (std err, status_code=1)
                    print(f"okhash.py: WARNING: {checksum_errors} computed checksums did NOT match", file=sys.stderr)

        else:
            if filepath == '-':
                digest = okhash(_read_stdin(), K=args.K)
            else:
                try:
                    digest = okhash_filepath(filepath, K=args.K)
                except PermissionError as e:
                    print(f"okhash.py: {filepath}: Permission denied", file=sys.stderr)
                    status_code = 1
                    continue

            print(f"{digest.hex()}  {filepath}", end='\x00' if args.zero else '\n')

    sys.exit(status_code)


if __name__ == "__main__":
    main()
