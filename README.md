# O(K)hash

## Introduction
**O(K)hash** (pronounced OK hash or oꭓash) is a hash function with O(1) complexity based on SHA-256. It is designed to efficiently calculate hashes for large files by reading only a fixed subset of data from random positions within the file. The 'K' parameter denotes the strength of the hashing, with lower values reading less data. For example, a hash with K=1 reads only 1KB of data, while a hash with K=2 reads 1MB of data. The hash results are downgradable, meaning a hash of strength K=3 can validate a file hash calculated with K=1.

## Rational
Calculating the hash of a large file normally involves reading the entire file, which can be time-consuming, especially with slow I/O operations. O(K)hash addresses this issue by reading a fixed number of bytes from random positions inside the file, providing a constant time complexity of O(1). This approach generates a reliable fingerprint for identifying duplicate files and validating files efficiently.

## Quickstart
### Installation

You can install O(K)hash using pip:

```bash
pip install okhash
```

### Usage
(todo)

### Command Line Usage

- **Calculate Checksums:** To calculate checksums for a file with a specified K value (default is K=2), use the following command:

   ```bash
   python3 -m okhash -K 3 file.bin
   ```

- **Check Checksums:** To check checksums for multiple files and save them to a text file (okhashes.txt), and then verify them, use the following commands:

   ```bash
   python3 -m okhash *.bin > okhashes.txt
   python3 -m okhash --check okhashes.txt
   ```

- **Additional Options:** You can explore additional options by running:

   ```bash
   python3 -m okhash --help
   ```

## The Strengths (K)
Here's a table describing the strengths (K) and their corresponding parameters:
1. Min File Size:
   $\text{min file size} = 2^{10K} \times 2$

2. Base Size (Size of Read Data):
   $\text{base\_size} = 2^{10K}$

3. Block Size:
   \[ \text{block size} = 1024 \times \lceil \frac{2^{6K}}{1024} \rceil \]

4. Block Count:
   \[ \text{block count} = \lceil \frac{\text{base\_size}}{\text{block size}} \rceil \]


| K   | Min File Size | Base Size (subset of data which hash is calculated) | Block Size | Blocks Read for K=1,2,3,4 |
| --- | ------------- | --------- | ---------- | --------------------------- |
| 1   | 0 bytes    | 1024 bytes| 1024 bytes | 1                           |
| 2   | 2097152 bytes | 1048576 bytes| 16384 bytes | 64                        |
| 3   | 2147483648 bytes | 1073741824 bytes | 1048576 bytes | 1024                 |
| 4   | 2199023255552 bytes | 1099511627776 bytes | 16777216 bytes | 64              |

## Limitations
After all, it's just an OK hash:
- **Not Suitable for Detecting Corruptions:** O(K)hash is not suitable for detecting file corruptions that do not change the size of the file. In the case of a bit flip or small corruptions, the probability of detecting corruption is lower than the formula: $\frac{base\_size}{file\_size}$.
- **Consider File Size Checking:** Depending on the nature and number of large files you are working with, it may be more effective to check the file size before calculating a conventional hash to ensure data integrity.

## License
RQ Chains is released under the [MIT License](/LICENSE).