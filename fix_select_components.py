#!/usr/bin/env python3
"""
Script to fix Select component onChange handlers in TypeScript files
"""

import os
import re
import glob

def fix_select_components():
    # Find all TypeScript files
    tsx_files = glob.glob('frontend/src/**/*.tsx', recursive=True)
    
    files_fixed = []
    
    for file_path in tsx_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Pattern to match Select components with incorrect onChange handlers
            # This matches: onChange={(e) => someFunction(e.target.value)}
            # where e.target.value is causing the TypeScript error
            
            # Fix pattern: onChange={(e) => handler(e.target.value)}
            # This pattern looks for Select components where e.target.value is used
            pattern = r'<Select([^>]*?)onChange=\{[^}]*?e\.target\.value[^}]*?\}'
            
            if re.search(pattern, content, re.DOTALL):
                print(f"Found Select component issues in: {file_path}")
                files_fixed.append(file_path)
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return files_fixed

if __name__ == "__main__":
    fixed_files = fix_select_components()
    print(f"\nFiles with Select component issues: {len(fixed_files)}")
    for file in fixed_files:
        print(f"  - {file}")