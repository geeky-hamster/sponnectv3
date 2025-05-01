#!/bin/bash

# Script to fix all date formatting and comments issues in Vue files
echo "Fixing all Vue date formatting issues..."

# Directory containing Vue files
FRONTEND_DIR="/home/soham/sponnectv3/sponnect/frontend/src"

# Fix duplicate comments
echo "Step 1: Fixing duplicate comments..."
for file in $(find "$FRONTEND_DIR" -name "*.vue"); do
  # Check if file contains duplicate date formatting comments
  if grep -q "Format date with explicit DD-MM-YYYY format.*Format date with explicit DD-MM-YYYY format" "$file" || 
     grep -q "Format date for.*Format date with explicit DD-MM-YYYY format" "$file"; then
    
    echo "Fixing duplicate comments in: $file"
    # Create temporary file
    tmp_file=$(mktemp)
    
    # Process file to remove duplicate comments
    awk '
    {
      # Skip duplicate comment line
      if ($0 ~ /\/\/ Format date with explicit DD-MM-YYYY format/ && prev_line ~ /\/\/ Format date/) {
        # Skip this line
      }
      else {
        print $0
      }
      prev_line = $0
    }
    ' "$file" > "$tmp_file"
    
    # Replace original file with fixed version
    mv "$tmp_file" "$file"
  fi
done

# Fix duplicate or malformed formatDate functions
echo "Step 2: Fixing formatDate functions..."
for file in $(find "$FRONTEND_DIR" -name "*.vue"); do
  # Check if file contains a formatDate function
  if grep -q "const formatDate" "$file"; then
    echo "Checking formatDate in: $file"
    
    # Create temporary file
    tmp_file=$(mktemp)
    
    # Process file to fix formatDate function
    awk '
    BEGIN { in_function = 0; skip_broken = 0; }
    
    # Fix malformed function
    /if \(!dateString\) return.*[^{]$/ && !in_function {
      skip_broken = 1
      next
    }
    
    # Skip other parts of broken functions
    skip_broken && /year:/ { skip_broken = 0; next }
    skip_broken && /month:/ { next }
    skip_broken && /day:/ { next }
    skip_broken && /\)\)/ { skip_broken = 0; next }
    
    # Track when we are inside a formatDate function
    /const formatDate = \(dateString/ {
      in_function = 1
      
      # Print the proper formatDate implementation
      print "// Format date with explicit DD-MM-YYYY format"
      print "const formatDate = (dateString) => {"
      print "  if (!dateString) return \"N/A\""
      print "  "
      print "  try {"
      print "    const date = new Date(dateString)"
      print "    "
      print "    // Use explicit formatting to avoid locale differences"
      print "    const day = date.getDate().toString().padStart(2, \"0\")"
      print "    const month = (date.getMonth() + 1).toString().padStart(2, \"0\") // Months are 0-indexed"
      print "    const year = date.getFullYear()"
      print "    "
      print "    // Format as DD-MM-YYYY"
      print "    return `${day}-${month}-${year}`"
      print "  } catch (e) {"
      print "    console.error(\"Error formatting date:\", e)"
      print "    return \"Invalid date\""
      print "  }"
      print "}"
      
      # Skip the existing implementation
      found_closing = 0
      while (!found_closing) {
        if (getline <= 0) break
        if ($0 ~ /^}/) {
          found_closing = 1
        }
      }
      
      in_function = 0
      next
    }
    
    # Print all other lines
    { print }
    ' "$file" > "$tmp_file"
    
    # Replace original file with fixed version if changes were made
    if ! cmp -s "$file" "$tmp_file"; then
      echo "Fixed formatDate in: $file"
      mv "$tmp_file" "$file"
    else
      echo "No changes needed in: $file"
      rm "$tmp_file"
    fi
  fi
done

echo "All Vue date formatting issues fixed!" 