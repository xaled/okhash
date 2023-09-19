# O(K)hash

## Introduction
**O(K)hash** (pronounced OK hash or oꭓash) is a hash function with $O(1)$ complexity based on SHA-256. It is designed to efficiently calculate hashes for large files by reading only a fixed subset of data from random positions within the file. The 'K' parameter denotes the strength of the hashing, with lower values reading less data. For example, a hash with K=1 reads only 1KiB of data, while a hash with K=2 reads 1MiB of data. The hash results are downgradable, meaning a hash of strength K=3 can validate a file hash calculated with K=1.

## Rational
Calculating the hash of a large file normally involves reading the entire file, which can be time-consuming, especially with slow I/O operations. O(K)hash addresses this issue by reading a fixed number of bytes from random positions inside the file, providing a constant time complexity of $O(1)$. This approach generates a reliable fingerprint for identifying duplicate files and validating files efficiently.

## Limitations
After all, it's just an OK hash:
- **Not Suitable for Detecting Corruptions:** O(K)hash is not suitable for detecting file corruptions that do not change the size of the file. In the case of a bit flip or small corruptions, the probability of detecting corruption is lower than: $\frac{base size}{file size}$.
- **Consider File Size Checking:** Depending on the nature and number of large files you are working with, it may be more effective to check the file size before calculating a conventional hash to ensure data integrity.

## Quickstart
### Installation

You can install O(K)hash using pip:

```bash
pip install okhash
```

### Usage
- **Calculate O(K)Hash of a String:**

   ```python
   import okhash

   data = "Hello, world!"
   checksum = okhash.okhash(data.encode('utf-8'), K=3)
   print(checksum.hex())
   ```

- **Calculate & compare O(K)Hash of Files:**

   ```python
   import okhash

   file1_checksum = okhash.okhash_filepath("file1.bin")
   file2_checksum = okhash.okhash_filepath("file2.bin")

   if okhash.compare_okhashes(file1_checksum, file2_checksum):
       print("Checksums match.")
   else:
       print("Checksums do not match.")
   ```


### Command Line Usage

- **Calculate Checksums:** To calculate checksums for a file with a specified K value (default is K=2), use the following command:

   ```bash
   python3 -m okhash -K 3 file.bin
   ```

- **Check Checksums:** The result of the previous command can be used to check checksums for multiple files:
   ```bash
   python3 -m okhash *.bin > okhashes.txt
   python3 -m okhash --check okhashes.txt
   ```

- **Additional Options:**

   ```bash
   python3 -m okhash --help
   ```

## The Strengths (K)
Here's a table describing the strengths (K) and their corresponding parameters:
| K   |  Base Size (Subset Data Size for Hash Calculation) | Block Size |
| --- | ------------- | --------- |
| 1   |  1024 B = 1 KiB   | 1024 B |
| 2   |  1048576 B = 1 MiB | 4096 B  |
| 3   |  1073741824 B = 1 GiB  | 262144 B  |
| 4   |  1099511627776 B = 1 TiB  | 16777216 B  |
| K  | $2^{10K}$ | $1024 \times \lceil \frac{2^{6K}}{1024} \rceil$  |

The minimum file size for a given K is equal to twice the base size; otherwise, the hash calculation will resort to SHA-256 for the entire file.


## License
O(K)hash is released under the [MIT License](/LICENSE).