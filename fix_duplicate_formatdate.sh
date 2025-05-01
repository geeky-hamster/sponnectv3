#!/bin/bash

# Script to fix duplicate formatDate functions in Vue files
echo "Fixing duplicate formatDate functions in Vue files..."

# Directory containing Vue files
FRONTEND_DIR="/home/soham/sponnectv3/sponnect/frontend/src"

# Find files with potential duplicate formatDate functions
# Look for files that have two "if (!dateString) return" statements in different formatDate functions
grep -l "if (!dateString) return.*return" --include="*.vue" -r "$FRONTEND_DIR" | while read -r file; do
  echo "Checking file for duplicates: $file"
  
  # Create a temporary file
  tmp_file=$(mktemp)
  
  # Pattern to detect duplicate formatDate functions
  # This will find the first function definition, keep it, and remove the second one
  awk '
  BEGIN { in_function = 0; found_first = 0; }
  
  # Mark when we enter a formatDate function
  /const formatDate = \(dateString\)/ { 
    if (found_first == 0) {
      found_first = 1;
      in_function = 1;
      print;
    } else {
      # Skip the second function definition
      in_function = 2;
      next;
    }
    next;
  }
  
  # If in the first function, print normally
  in_function == 1 { print; next; }
  
  # When we exit the first function (detected by closing brace), mark it
  in_function == 1 && /^}/ { in_function = 0; print; next; }
  
  # When we are in the second function, skip until we find the closing brace
  in_function == 2 && /^}/ { in_function = 0; next; }
  in_function == 2 { next; }
  
  # Print everything else
  { print; }
  ' "$file" > "$tmp_file"
  
  # Compare the original and modified files
  if ! cmp -s "$file" "$tmp_file"; then
    echo "Fixed duplicate formatDate in: $file"
    mv "$tmp_file" "$file"
  else
    echo "No duplicates found in: $file"
    rm "$tmp_file"
  fi
done

echo "Done fixing duplicate formatDate functions!" 