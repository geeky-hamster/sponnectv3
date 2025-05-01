#!/bin/bash

# Script to fix all date formatting issues in the frontend
echo "Fixing date formatting in Vue files..."

# Directory containing Vue files
FRONTEND_DIR="/home/soham/sponnectv3/sponnect/frontend/src"

# 1. Fix all toLocaleDateString instances
echo "Fixing toLocaleDateString locale usage..."
grep -l "toLocaleDateString" --include="*.vue" -r "$FRONTEND_DIR" | while read -r file; do
  echo "Processing file: $file"
  # Replace 'en-US' with 'en-IN'
  sed -i "s/toLocaleDateString('en-US'/toLocaleDateString('en-IN'/g" "$file"
  sed -i 's/toLocaleDateString("en-US"/toLocaleDateString("en-IN"/g' "$file"
  
  # Replace any undefined locales with 'en-IN'
  sed -i "s/toLocaleDateString(/toLocaleDateString('en-IN', /g" "$file"
  
  # Fix any double locale specifications that might have been created
  sed -i "s/toLocaleDateString('en-IN', 'en-IN'/toLocaleDateString('en-IN'/g" "$file"
done

# 2. Fix all toLocaleString instances
echo "Fixing toLocaleString locale usage..."
grep -l "toLocaleString" --include="*.vue" -r "$FRONTEND_DIR" | while read -r file; do
  echo "Processing file: $file"
  # Replace 'en-US' with 'en-IN'
  sed -i "s/toLocaleString('en-US'/toLocaleString('en-IN'/g" "$file"
  sed -i 's/toLocaleString("en-US"/toLocaleString("en-IN"/g' "$file"
  
  # Replace any undefined locales with 'en-IN'
  sed -i "s/toLocaleString(/toLocaleString('en-IN', /g" "$file"
  
  # Fix any double locale specifications that might have been created
  sed -i "s/toLocaleString('en-IN', 'en-IN'/toLocaleString('en-IN'/g" "$file"
done

# 3. Update formatDate functions to explicitly format DD-MM-YYYY
echo "Updating local formatDate functions to use explicit DD-MM-YYYY format..."
grep -l "const formatDate.*dateString" --include="*.vue" -r "$FRONTEND_DIR" | while read -r file; do
  echo "Updating formatDate in: $file"
  
  # Create a temporary file
  tmp_file=$(mktemp)
  
  # Process the file, handling duplicate formatDate functions properly
  awk '
  BEGIN { in_function = 0; found_first = 0; }
  
  # Mark when we enter a formatDate function
  /const formatDate = \(dateString\)/ || /const formatDate = \(dateString,/ { 
    if (found_first == 0) {
      found_first = 1;
      in_function = 1;
      
      # Replace with our consistent explicit format function
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
    } else {
      # Skip any duplicate formatDate function
      in_function = 2;
    }
    next;
  }
  
  # When in a function we want to replace, skip until closing brace
  in_function > 0 && /^}/ { in_function = 0; next; }
  in_function > 0 { next; }
  
  # Print all other lines
  { print; }
  ' "$file" > "$tmp_file"
  
  # Replace the original file with the modified content
  mv "$tmp_file" "$file"
done

echo "Date formatting fixes completed!" 