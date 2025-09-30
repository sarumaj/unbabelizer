#!/bin/bash

# Create licenses directory if it doesn't exist
LICENSES_DIR="$(dirname "$(dirname "$0")")/licenses"
mkdir -p "$LICENSES_DIR"

# Function to download a license file
fetch_license() {
    local name=$1
    local url=$2
    local output_file="$LICENSES_DIR/$name.txt"

    if curl -s -f "$url" > "$output_file"; then
        echo "✓ Downloaded $name license"
    else
        echo "✗ Failed to download $name license"
    fi
}

echo "Downloading license files..."

# Download licenses
fetch_license "asciinema" "https://raw.githubusercontent.com/asciinema/asciinema/refs/heads/develop/LICENSE"
fetch_license "babel" "https://raw.githubusercontent.com/python-babel/babel/refs/heads/master/LICENSE"
fetch_license "googletrans" "https://raw.githubusercontent.com/ssut/py-googletrans/refs/heads/main/LICENSE"
fetch_license "jmespath" "https://raw.githubusercontent.com/jmespath/jmespath.py/refs/heads/develop/LICENSE"
fetch_license "polib" "https://raw.githubusercontent.com/izimobil/polib/refs/heads/master/LICENSE"
fetch_license "pydantic" "https://raw.githubusercontent.com/pydantic/pydantic/main/LICENSE"
fetch_license "textual" "https://raw.githubusercontent.com/Textualize/textual/refs/heads/main/LICENSE"

echo -e "\nDone! License files are in the 'licenses' directory."
