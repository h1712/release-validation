import argparse
import requests
import os
import re 
import sys

# Function to download a file from a URL
def download_file(url):
    if not url.endswith('Packages'):
        if not url.endswith('/'):
            url += '/'
        url += 'Packages'
    
    local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_filename

# Function to parse the package dependencies file
def parse_dependencies(file_paths):
    package_dict = {}
    provides_dict = {}

    for file_path in file_paths:
        if file_path.startswith('http://') or file_path.startswith('https://'):
            try:
                print(f"Downloading file from {file_path}...")
                file_path = download_file(file_path)
                print(f"Downloaded to {file_path}")
            except Exception as e:
                print(f"Error downloading {file_path}: {e}")
                continue

        try:
            with open(file_path, 'r') as file:
                data = file.read()
        except FileNotFoundError:
            print(f"Error: The file {file_path} was not found.")
            continue

        package_data = data.split('\n\n')

        for package in package_data:
            lines = package.strip().split('\n')
            package_info = {}
            package_name = None
            for line in lines:
                if line.startswith('Package:'):
                    package_name = line.split(': ')[1].strip()
                    if package_name.startswith('lib32-'):
                        package_name = package_name[6:]  # strip 'lib32-' prefix
                elif line.startswith('Version:'):
                    package_info['Version'] = line.split(': ')[1].strip()
                elif line.startswith('Depends:'):
                    package_info['Depends'] = [dep.strip() for dep in line.split(': ')[1].split(',')]
                    package_info['Depends'] = [dep[6:] if dep.startswith('lib32-') else dep for dep in package_info['Depends']]  # strip 'lib32-' prefix
                elif line.startswith('Provides:'):
                    provided_names = [name.strip() for name in line.split(': ')[1].split(',')]
                    provided_names = [name[6:] if name.startswith('lib32-') else name for name in provided_names]  # strip 'lib32-' prefix
                    for provided_name in provided_names:
                        provides_dict[provided_name] = package_name

            if package_name:
                package_dict[package_name] = package_info

    return package_dict, provides_dict

# Function to check if dependencies of a given package exist
def check_dependencies(package_name, package_dict, provides_dict, checked_packages=None):
    if checked_packages is None:
        checked_packages = set()

    if package_name not in package_dict:
        print (f"No such package '{package_name}' exist, Please provide a valid name.")
        sys.exit(1)

    if package_name in checked_packages:
        return []

    checked_packages.add(package_name)

    missing_dependencies = []
    package_info = package_dict[package_name]
    dependencies = package_info.get('Depends', [])

    for dep in dependencies:
        dep_name = re.split(' ', dep.strip())[0].strip()
        resolved_dep_name = provides_dict.get(dep_name, dep_name)  # Resolve runtime name

        if resolved_dep_name not in package_dict:
            missing_dependencies.append(dep_name)
        else:
            missing_dependencies.extend(check_dependencies(resolved_dep_name, package_dict, provides_dict, checked_packages))

    return missing_dependencies
"""
# Usage example
file_paths = ['middleware-element-packages.txt', 'oss-packages.txt', 'vendor-element-packages.txt']
package_dict, provides_dict = parse_dependencies(file_paths)
package_name = 'packagegroup-middleware-layer'
missing_deps = check_dependencies(package_name, package_dict, provides_dict)

if missing_deps:
    unique_missing_deps = sorted(set(missing_deps))  # Remove duplicates and sort
    print(f"Missing dependencies for package '{package_name}': {', '.join(unique_missing_deps)}")
else:
    print(f"All dependencies for package '{package_name}' exist.")
"""


def check_and_print_dependencies(package_name, package_dict, provides_dict, allarch_dict):
    missing_deps = check_dependencies(package_name, package_dict, provides_dict)
    #Volatile-binds is in exception case as it is being built in all projects.
    missing_deps = [dep for dep in missing_deps if dep != 'volatile-binds']
    missing_allarch_deps = [dep for dep in missing_deps if dep in allarch_dict]

    if missing_deps:
        unique_missing_deps = sorted(set(missing_deps))  # Remove duplicates and sort
        print(f"Missing IPKs for package '{package_name}': {', '.join(sorted(unique_missing_deps))}")
        unique_missing_allarch_deps = sorted(set(missing_allarch_deps))  # Remove duplicates and sort
        if allarch_dict:
            if unique_missing_allarch_deps:
                print(f"Missing IPKs for package '{package_name}' but provided by 'all' arch: {', '.join(sorted(unique_missing_allarch_deps))}")
            else:
                print(f"Missing IPKs for package '{package_name}' but provided by 'all' arch: NIL")
        if set(unique_missing_deps) == set(unique_missing_allarch_deps):
            validation_result = 'PASS'
        else:
            validation_result = 'FAIL'
    else:
        print(f"Missing IPKs for package '{package_name}': NIL")
        validation_result = 'PASS'
    return validation_result

def main():
    parser = argparse.ArgumentParser(
        description="""Check package dependencies.

This script checks whether all the required dependencies specific to a given package exist in the provided package files or URLs. 
If not, it lists the missing dependencies.

Examples:
  python3 script.py -m middleware-packages.txt -v vendor-packages.txt -o oss-packages.txt
  python3 script.py -m https://example.com/middleware-packages.txt -v https://example.com/vendor-packages.txt -o oss-packages.txt""",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-i', '--input', type=str, help='Input package name')
    parser.add_argument('-m', '--middleware_layer', nargs='+', help='Middleware package files or URLs')
    parser.add_argument('-v', '--vendor_layer', nargs='+', help='Vendor package files or URLs')
    parser.add_argument('-o', '--oss_layer', nargs='+', help='OSS package files or URLs')
    parser.add_argument('-a', '--allarch_layer', nargs='+', help='allarch package files or URLs')

    args = parser.parse_args()


    file_paths = []
    allarch_path = []
    if args.middleware_layer:
        file_paths.extend(args.middleware_layer)
    if args.vendor_layer:
        file_paths.extend(args.vendor_layer)
    if args.oss_layer:
        file_paths.extend(args.oss_layer)
    if args.allarch_layer:
        allarch_path.extend(args.allarch_layer)
    

    if args.input:
        package_name = args.input
    else:
        validation_results = []
        if args.middleware_layer and args.vendor_layer and args.oss_layer:
            package_dict, provides_dict = parse_dependencies(file_paths)
            allarch_dict, allarch_provides_dict = parse_dependencies(allarch_path)
            for package_name in  ['packagegroup-middleware-layer', 'packagegroup-vendor-layer']:
                result = check_and_print_dependencies(package_name, package_dict, provides_dict, allarch_dict)
                validation_results.append(result)
            if 'FAIL' in validation_results:
                print(f"Validation result: FAIL")
                sys.exit(1)
            else:
                print(f"Validation result: PASS")
                sys.exit(0)

        elif args.vendor_layer and args.oss_layer:
            package_name = 'packagegroup-vendor-layer'
        else:
            print("Error: Package name cannot be determined. Please provide the package name explicitly with -i.")
            return

    package_dict, provides_dict = parse_dependencies(file_paths)
    allarch_dict, allarch_provides_dict = parse_dependencies(allarch_path)
    result = check_and_print_dependencies(package_name, package_dict, provides_dict, allarch_dict)
    print(f"Validation result: {result}")
    if 'FAIL' == result:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
