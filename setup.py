# !/usr/bin/env python3
from distutils.core import setup
from setuptools import find_packages
from okhash import VERSION

# def package_files(directory):
#     paths = []
#     for (path, directories, filenames) in os.walk(directory):
#         for filename in filenames:
#             if not path.endswith('__pycache__') and not filename.endswith(".pyc"):
#                 paths.append(os.path.relpath(os.path.join(path, filename), directory))
#     return paths


with open('README.md', 'r') as f:
    long_description = f.read()

with open('LICENSE', 'r') as f:
    license_text = f.read()

# error: does not get copied to the package tar.gz
# with open('requirements.txt') as f:
#     required = f.read().splitlines()

if __name__ == "__main__":
    # extra_files = package_files('rq_chains/')

    # print extra_files

    setup(
        name='okhash',
        version=VERSION,
        description='Library and CLI for computing O(K)Hash checksums.',
        long_description=long_description,
        long_description_content_type='text/markdown',
        keywords='library cli hash',
        author='Khalid Grandi',
        author_email='kh.grandi@gmail.com',
        classifiers=[
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
        ],

        license='MIT',
        url='https://github.com/xaled/okhash',
        install_requires=[],
        python_requires='>=3',
        py_modules=['okhash'],
        packages=find_packages(),
        package_data={'': ['LICENSE', 'README.md']},
        entry_points={
            'console_scripts': [
                'okhash=okhash:main',
            ],
        },
    )
