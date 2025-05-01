#!/bin/bash

# Find all Vue files with 'en-US' date formatting and replace with 'en-IN'
echo "Fixing date locale in Vue files..."

grep -l "toLocaleDateString('en-US'" --include="*.vue" -r /home/soham/sponnectv3/sponnect/frontend/src | while read -r file; do
  echo "Fixing file: $file"
  sed -i "s/toLocaleDateString('en-US'/toLocaleDateString('en-IN'/g" "$file"
done

grep -l 'toLocaleDateString("en-US"' --include="*.vue" -r /home/soham/sponnectv3/sponnect/frontend/src | while read -r file; do
  echo "Fixing file: $file"
  sed -i 's/toLocaleDateString("en-US"/toLocaleDateString("en-IN"/g' "$file"
done

echo "Done!" 