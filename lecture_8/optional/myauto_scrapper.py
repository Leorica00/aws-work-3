import asyncio
import aiohttp
import os
import zipfile
import argparse
import boto3
from botocore.exceptions import ClientError

# Specify the endpoint URL
def auto_page_n(nth_page):
    return (f"https://api2.myauto.ge/ka/products?TypeID=0&ForRent=&Mans=&CurrencyID=3&MileageType=1&Page={nth_page}")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Language": "en-US,en;q=0.9",
}


async def download_image(session, url, save_directory):
    try:
        async with session.get(url) as response:
            response.raise_for_status()

            # Extract the filename from the URL
            filename = os.path.basename(url)

            # Save the image to the specified directory
            save_path = os.path.join(save_directory, filename)
            with open(save_path, "wb") as file:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    file.write(chunk)

            print(f"Downloaded: {filename}")
    except aiohttp.ClientError as e:
        print(f"Error downloading image: {e}")


def upload_to_s3(local_directory, bucket_name, s3_prefix=""):
    """
    Upload all files from a local directory to an S3 bucket
    """
    s3_client = boto3.client("s3")

    for root, _, files in os.walk(local_directory):
        for file in files:
            local_path = os.path.join(root, file)
            # Create S3 key by joining prefix and relative path
            relative_path = os.path.relpath(local_path, local_directory)
            s3_key = os.path.join(s3_prefix, relative_path)

            try:
                s3_client.upload_file(local_path, bucket_name, s3_key)
                print(f"Uploaded {local_path} to s3://{bucket_name}/{s3_key}")
            except ClientError as e:
                print(f"Error uploading {local_path}: {e}")


async def main(args):
    image_urls = []  # List to store image URLs

    async with aiohttp.ClientSession(headers=headers) as session:
        for page_n in range(args.pages):
            response = await session.get(auto_page_n(page_n))
            response.raise_for_status()

            data = await response.json()

            for item in data["data"]["items"]:
                car_id = item["car_id"]
                photo = item["photo"]
                picn = item["pic_number"]
                print(f"Car ID: {car_id}")
                print("Image URLs:")
                for id in range(1, picn + 1):
                    image_url = f"https://static.my.ge/myauto/photos/{photo}/large/{car_id}_{id}.jpg"
                    image_urls.append(image_url)
                    print(image_url)
                print()

        # Create a folder to store downloaded images
        save_directory = args.output_dir
        os.makedirs(save_directory, exist_ok=True)

        # Download images asynchronously
        tasks = []
        async with aiohttp.ClientSession() as session:
            for url in image_urls:
                task = asyncio.ensure_future(
                    download_image(session, url, save_directory)
                )
                tasks.append(task)

            await asyncio.gather(*tasks)

        # Zip the downloaded images if requested
        if args.zip:
            zip_filename = f"{save_directory}.zip"
            with zipfile.ZipFile(zip_filename, "w") as zip_file:
                for root, _, files in os.walk(save_directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zip_file.write(file_path, arcname=file)

            print(f"\nAll images downloaded and zipped successfully.")
            zip_file_size_mb = os.path.getsize(zip_filename) / (1024 * 1024)
            print(f"ZIP file size: {zip_file_size_mb:.2f} MB")

        total_images = sum(len(files) for _, _, files in os.walk(save_directory))
        print(f"Total number of downloaded images: {total_images}")

        # Upload to S3 if bucket is specified
        if args.s3_bucket:
            print(f"\nUploading images to S3 bucket: {args.s3_bucket}")
            upload_to_s3(save_directory, args.s3_bucket, args.s3_prefix)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download images from myauto.ge and optionally upload to S3"
    )
    parser.add_argument(
        "--pages", type=int, default=1, help="Number of pages to scrape (default: 1)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="downloaded_images",
        help="Directory to save images (default: downloaded_images)",
    )
    parser.add_argument(
        "--zip", action="store_true", help="Create a zip file of downloaded images"
    )
    parser.add_argument("--s3-bucket", type=str, help="S3 bucket name to upload images")
    parser.add_argument(
        "--s3-prefix",
        type=str,
        default="",
        help="S3 prefix/folder path (default: root of bucket)",
    )

    args = parser.parse_args()
    asyncio.run(main(args))
