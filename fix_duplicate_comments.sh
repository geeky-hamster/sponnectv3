#!/bin/bash

# Script to fix duplicate comments in Vue files
echo "Fixing duplicate comments in Vue files..."

# Directory containing Vue files
FRONTEND_DIR="/home/soham/sponnectv3/sponnect/frontend/src"

# Fix duplicate comments
echo "Fixing duplicate date formatting comments..."
grep -l "Format date with explicit DD-MM-YYYY format.*Format date with explicit DD-MM-YYYY format" --include="*.vue" -r "$FRONTEND_DIR" | while read -r file; do
  echo "Fixing duplicate comments in: $file"
  
  # Replace duplicate comments with a single comment
  sed -i 's/\/\/ Format date with explicit DD-MM-YYYY format\n\/\/ Format date with explicit DD-MM-YYYY format/\/\/ Format date with explicit DD-MM-YYYY format/g' "$file"
  
  # Another pattern that might occur
  sed -i 's/\/\/ Format date for.*\n\/\/ Format date with explicit DD-MM-YYYY format/\/\/ Format date with explicit DD-MM-YYYY format/g' "$file"
done

echo "Done fixing duplicate comments!" 