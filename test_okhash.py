import unittest
from os.path import exists, join
from os import makedirs, unlink, listdir
import hashlib
import random
import math
import okhash
import shutil

TEST_MODIFICATION_TYPES = ['appended', 'truncated']
TEST_SIZES = [1024, 1024 * 1024, 1024 * 1024 * 1024]
TEST_DIR = 'test_files'
BYTE_FLIP_TESTS = 100

hashes = dict()


def _calculate_hash(fp, K, force=False):
    global hashes
    if force or (fp, K) not in hashes:
        h = okhash.okhash_filepath(fp, K=K)
        print(f"Hash for {fp=} {K=} is {h.hex()}")
        hashes[(fp, K)] = h
    return hashes[(fp, K)]


def _generate_random_bytes(n):
    if n <= 0:
        raise ValueError("n must be a positive integer")

    random_bytes = bytes(random.randint(0, 255) for _ in range(n))
    return random_bytes


def _generate_modified_content(original_file_path, modification_type, filename, input_size):
    file_path = join(TEST_DIR, filename)

    # copy file
    shutil.copy(original_file_path, file_path)

    with open(file_path, 'rb+') as fou:
        if modification_type == 'byte_flip':
            index = random.randint(0, input_size - 1)
            fou.seek(index)
            data = _generate_random_bytes(1)
            fou.write(data)
            print(f"byte_flip: {filename=} {index=} {data=}")
        elif modification_type == 'appended':
            fou.seek(0, 2)
            fou.write(_generate_random_bytes(random.randint(1024, 2048)))
        elif modification_type == 'truncated':
            new_size = max(random.randint(input_size - 1024, input_size), 1000)
            fou.truncate(new_size)


def _byte_flip(filepath, input_size, index=None, data=None):
    index = random.randint(0, input_size - 1) if index is None else index
    data = _generate_random_bytes(1) if data is None else data

    # file_path = original_file_path + '._byte_flip.temp'

    # copy file
    # shutil.copy(original_file_path, file_path)

    with open(filepath, 'rb+') as fou:
        fou.seek(index)
        original_data = fou.read(1)
        fou.seek(index)
        fou.write(data)
        print(f"byte_flip: {filepath=} {index=} {original_data=} {data=}")

    # calculate hashes
    file_hashes = list()
    for K in range(1, 4):
        file_hashes.append(okhash.okhash_filepath(filepath, K=K))

    # restore file
    with open(filepath, 'rb+') as fou:
        fou.seek(index)
        fou.write(original_data)

    return file_hashes, index, data


def _generate_random_file(filename, size, block_size=None):
    filepath = join(TEST_DIR, filename)
    block_size = block_size or (1024 if size < 1024 * 1024 else 1024 * 1024)
    with open(filepath, 'wb') as fou:
        written_bytes = 0
        while written_bytes < size:
            fou.write(_generate_random_bytes(block_size))
            written_bytes += block_size
    return filepath


class TestOkhash(unittest.TestCase):
    def setUp(self):
        if not exists(TEST_DIR):
            print("mkdir ", TEST_DIR)
            makedirs(TEST_DIR)
            # self.test_files = {}
        for size in TEST_SIZES:
            for fn in (f'file1_{size}.bin', f'file2_{size}.bin'):
                if not exists(join(TEST_DIR, fn)):
                    print("Generating ", fn)
                    _generate_random_file(fn, size)

            file1_path = join(TEST_DIR, f'file1_{size}.bin')
            for modified_file_type in TEST_MODIFICATION_TYPES:
                fn = f'file1_{size}_{modified_file_type}.bin'
                if not exists(join(TEST_DIR, fn)):
                    print("Generating ", fn)
                    _generate_modified_content(file1_path, modified_file_type, fn,
                                               size)

    def tearDown(self) -> None:
        if exists(TEST_DIR):
            for f in listdir(TEST_DIR):
                if '_byte_flip' in f:
                    print(f"Deleting {f}..")
                    unlink(join(TEST_DIR, f))

    def test_file_hashes(self):
        for size in TEST_SIZES:
            for K in range(1, 5):
                fn = f'file1_{size}.bin'
                digest = okhash.okhash(join(TEST_DIR, fn), K=K)
                print(f"Hash for {fn=} {K=} is {digest.hex()=}")
                self.assertTrue(not not digest)

    def test_compare_okhashes(self):
        comparisons = list()
        for size in TEST_SIZES:
            comparisons.append((f'file1_{size}.bin', f'file2_{size}.bin'))
            comparisons.append((f'file2_{size}.bin', f'file2_{size}.bin'))
            comparisons.extend(
                (f'file1_{size}.bin', f'file1_{size}_{modified_file_type}.bin') for modified_file_type in
                TEST_MODIFICATION_TYPES
            )

        for fp1, fp2 in comparisons:
            for k1 in range(1, 4):
                for k2 in range(1, 4):
                    hash1, hash2 = _calculate_hash(join(TEST_DIR, fp1), k1), _calculate_hash(join(TEST_DIR, fp2), k2)
                    comparison_result = okhash.compare_okhashes(hash1, hash2)
                    expected_result = fp1 == fp2
                    print(f">> Comparing {fp1=} and {fp2=}, k={(k1, k2)}, {comparison_result=} {expected_result=}")
                    if comparison_result is not expected_result:
                        print("***")
                    self.assertTrue(comparison_result is expected_result)

    def test_hashes(self):
        for K in range(1, 5):
            for input_stream in [b'', b'\x00', 'Hello World!']:
                digest = okhash.okhash(input_stream, K=K)
                print(f">> Hash for {input_stream=} {K=} is {digest.hex()=}")
                self.assertTrue(not not digest)

    def test_byte_flip(self):
        for size in TEST_SIZES:
            fn1 = f'file1_{size}.bin'
            fp1 = join(TEST_DIR, fn1)
            temp_file = fp1 + '.copy.temp'
            shutil.copy(fp1, temp_file)
            byte_flip_hashes = list()
            # generating byte_filp files
            for ix in range(BYTE_FLIP_TESTS):
                file_hashes, index, data = _byte_flip(temp_file, size)
                byte_flip_hashes.append(file_hashes)

            unlink(temp_file)

            for K in range(1, 4):
                change_detected, total = 0, 0
                hash1 = _calculate_hash(join(TEST_DIR, fn1), K)

                for ix in range(BYTE_FLIP_TESTS):
                    fn2 = f'file1_{size}_byte_flip_{ix}.bin'
                    fp2 = join(TEST_DIR, fn2)

                    hash2 = byte_flip_hashes[ix][K - 1]
                    comparison_result = okhash.compare_okhashes(hash1, hash2)

                    print(f"Comparing {fp1=} and {fp2=}, {K= }, {comparison_result=}")

                    if comparison_result is False:
                        change_detected += 1
                    total += 1

                expected_result = min(TEST_SIZES[K - 1] / size, 1)
                result = change_detected / total
                success = result <= expected_result * 2
                print(f">> ByteFlip detection ratio for {fn1=} {K=}: "
                      f"{change_detected}/{total} = {int(result * 100)}% "
                      f"{expected_result=}")
                self.assertTrue(success)


if __name__ == '__main__':
    unittest.main()
