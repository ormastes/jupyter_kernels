import requests
from xml.etree import ElementTree as ET
import os
import zipfile
from tqdm import tqdm

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

def get_dll_or_download(platform, file_name, extract_dir):
    extract_full_path = os.path.join(extract_dir, file_name)
    if os.path.exists(extract_full_path) and os.path.isfile(extract_full_path) and os.path.getsize(extract_full_path) > 0:
        return extract_full_path

    print("Downloading clang_repl binary from " + platform+" "+file_name)
    # URL of the file you want to download
    file_url = f"http://webdav.yoonhome.com/PublicShare/llvm_lib/{platform}/{file_name}"
    download_file = _download(extract_dir, file_name, file_url)

def is_done(extract_dir):
    done_file = os.path.join(extract_dir, "done")
    return os.path.exists(done_file)

def extract_with_progress(zip_path, extract_dir):
    print("Extracting", zip_path, "to", extract_dir)
    print("Reading zip file... Please wait.")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Get list of all file info objects in the zip
        members = zip_ref.infolist()
        # Iterate over each file with a progress bar
        for member in tqdm(members, desc="Extracting", unit="file"):
            zip_ref.extract(member, extract_dir)

def download(file_name, extract_dir):
    print("Downloading clang_repl binary from " + file_name)
    # URL of the file you want to download
    file_url = f"http://webdav.yoonhome.com/PublicShare/llvm/18.1.8/{file_name}"
    download_file = _download(extract_dir, file_name, file_url)

    # extract the downloaded file
    extract_with_progress(download_file, extract_dir)

    # Remove the zip file
    os.remove(download_file)

    # write done file
    done_file = os.path.join(extract_dir, "done")
    with open(done_file, "w") as f:
        f.write("done")

    return download_file


def _download(extract_dir, file_name, file_url):
    # Perform a GET request with streaming enabled (for large files)
    response = requests.get(file_url, auth=auth, stream=True)
    
    # Ensure the extraction directory exists
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)
    
    download_file = os.path.join(extract_dir, file_name)

    # delete the file if it already exists
    if os.path.exists(download_file):
        os.remove(download_file)
    
    if response.status_code == 200:
        total_size = int(response.headers.get('content-length', 0))
        # Open the file and wrap the write loop with tqdm for the progress bar
        with open(download_file, "wb") as f, tqdm(
            total=total_size, unit='B', unit_scale=True, desc=file_name
        ) as progress_bar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    progress_bar.update(len(chunk))
        print("Download completed:", download_file)
    else:
        print("Failed to download file:", response.status_code)
        print(response.text)
    
    return download_file

