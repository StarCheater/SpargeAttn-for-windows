#!/usr/bin/env python3

import os
import sys
import argparse
from pathlib import Path

def update_pyproject_version(pytorch_version, cuda_version):
    """Update pyproject.toml with version information."""
    
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("pyproject.toml not found!")
        return False
    
    # Read current content
    with open(pyproject_path, 'r') as f:
        content = f.read()
    
    # Set nightly URL if needed
    if "nightly" in pytorch_version.lower():
        nightly_url = f"https://download.pytorch.org/whl/nightly/cu{cuda_version.replace('.', '')}"
        if nightly_url not in content:
            # Add nightly URL to simpleindex section
            content = content.replace(
                '[[tool.simpleindex.distributions]]',
                f'[[tool.simpleindex.distributions]]\nnightly_url = "{nightly_url}"'
            )
    
    # Write updated content
    with open(pyproject_path, 'w') as f:
        f.write(content)
    
    print(f"Updated pyproject.toml for PyTorch {pytorch_version} with CUDA {cuda_version}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update pyproject.toml versions')
    parser.add_argument('--pytorch-version', required=True, help='PyTorch version')
    parser.add_argument('--cuda-version', required=True, help='CUDA version')
    
    args = parser.parse_args()
    
    success = update_pyproject_version(args.pytorch_version, args.cuda_version)
    sys.exit(0 if success else 1)
