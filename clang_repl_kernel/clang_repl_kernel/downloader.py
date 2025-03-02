import requests
from xml.etree import ElementTree as ET
import os

# The WebDAV URL to list files from
url = "http://webdav.yoonhome.com/PublicShare/llvm/18.1.8"

# PROPFIND headers; Depth "1" lists files and directories in the current folder.
headers = {
    "Depth": "1",
    "Content-Type": "application/xml"
}

auth = ("cdoctest", "cdoctest")

def list():
    # Send a PROPFIND request with basic authentication
    response = requests.request("PROPFIND", url, headers=headers, auth=auth)

    if response.status_code == 207:
        # Parse the multistatus XML response
        tree = ET.fromstring(response.content)
        # Define the DAV namespace
        ns = {"d": "DAV:"}

        print("Listing items in:", url)
        # Iterate over all <d:response> elements
        for resp in tree.findall("d:response", ns):
            href_elem = resp.find("d:href", ns)
            if href_elem is not None:
                print(href_elem.text)
    else:
        print("Error:", response.status_code)
        print(response.text)

def download(file_name, extract_dir):
    print("Downloading clang_repl binary from " + file_name)
    # URL of the file you want to download
    file_url = f"http://webdav.yoonhome.com/PublicShare/llvm/18.1.8/{file_name}"
    # Perform a GET request with streaming enabled (for large files)
    response = requests.get(file_url, auth=auth, stream=True)

    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)

    download_file = os.path.join(extract_dir, file_name)
    if response.status_code == 200:
        with open(download_file, "wb") as f:
            # Write the file in chunks to avoid loading the entire file into memory
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print("Download completed:", download_file)
    else:
        print("Failed to download file:", response.status_code)
        print(response.text)


    # extract the downloaded file
    import zipfile
    with zipfile.ZipFile(download_file, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    # Remove the zip file
    os.remove(download_file)
