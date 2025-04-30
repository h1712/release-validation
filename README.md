Release Validator
This script is a utility designed to validate package dependencies for CI/CD workflows. It checks whether all required dependencies specific to a given package exist in the provided package files or URLs. If any dependencies are missing, it lists them and provides validation results.

Features
Download package dependency files from URLs or use local files.
Parse package dependency files to extract package information, including dependencies and provided packages.
Validate dependencies for specific packages and identify missing dependencies.
Handle exceptions for packages that are universally built across projects.
Output validation results as PASS or FAIL based on the presence of missing dependencies.
Requirements
Python 3.x
The following Python libraries:
argparse
requests
os
re
sys
Usage
Command-line Arguments
The script accepts the following command-line arguments:

Argument	Description
-i, --input	(Optional) The name of the package to validate.
-m, --middleware_layer	Middleware package files or URLs.
-v, --vendor_layer	Vendor package files or URLs.
-o, --oss_layer	OSS package files or URLs.
-a, --allarch_layer	(Optional) allarch package files or URLs, representing packages provided by the "all" architecture.
Examples
Example 1: Validate a specific package
bash
python3 release_validator.py -i packagegroup-middleware-layer -m middleware-packages.txt -v vendor-packages.txt -o oss-packages.txt
Example 2: Validate multiple layers
bash
python3 release_validator.py -m middleware-packages.txt -v vendor-packages.txt -o oss-packages.txt
Example 3: Use URLs for dependency files
bash
python3 release_validator.py -m https://example.com/middleware-packages.txt -v https://example.com/vendor-packages.txt -o oss-packages.txt
Output
The script provides the following output:

Lists missing dependencies for the specified package, if any.
Identifies missing dependencies that are provided by the "all" architecture.
Outputs a validation result as either PASS or FAIL.
Return Codes
0: Validation passed.
1: Validation failed.
How It Works
Download Dependency Files: The script can download dependency files from provided URLs if needed.
Parse Dependency Files: It extracts information about packages, including their versions, dependencies, and provided features.
Validate Dependencies: It checks whether all dependencies of the given package exist in the provided files or URLs.
Handle Exceptions: The script excludes specific packages (e.g., volatile-binds) from missing dependencies as they are universally built.
Output Results: It prints missing dependencies and provides a validation result (PASS or FAIL).
Functions
download_file(url)
Downloads a file from a URL and saves it locally.

parse_dependencies(file_paths)
Parses package dependency files and returns dictionaries for package information and provided features.

check_dependencies(package_name, package_dict, provides_dict, checked_packages=None)
Checks if all dependencies for the given package exist and lists any missing dependencies.

check_and_print_dependencies(package_name, package_dict, provides_dict, allarch_dict)
Validates dependencies for a given package and handles packages provided by the "all" architecture.

main()
Handles command-line arguments, orchestrates parsing, validation, and outputs results.

Notes
The script assumes that package files follow a specific format with fields such as Package, Version, Depends, and Provides.
For runtime dependencies, the script resolves names using the Provides field to account for aliasing.
