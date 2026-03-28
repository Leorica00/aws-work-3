from urllib.request import urlopen
import io
import os
import mimetypes
from hashlib import md5
from time import localtime

# მინიმალური ნაწილის ზომა multipart upload-ისთვის (5 MB — AWS მინიმუმი)
PART_BYTES = 5 * 1024 * 1024


def get_objects(aws_s3_client, bucket_name):
    for key in aws_s3_client.list_objects(Bucket=bucket_name)["Contents"]:
        print(f" {key['Key']}, size: {key['Size']}")


def download_file_and_upload_to_s3(
    aws_s3_client, bucket_name, url, keep_local=False
) -> str:
    file_name = f'image_file_{md5(str(localtime()).encode("utf-8")).hexdigest()}.jpg'
    with urlopen(url) as response:
        content = response.read()
        aws_s3_client.upload_fileobj(
            Fileobj=io.BytesIO(content),
            Bucket=bucket_name,
            ExtraArgs={"ContentType": "image/jpg"},
            Key=file_name,
        )
    if keep_local:
        with open(file_name, mode="wb") as jpg_file:
            jpg_file.write(content)

    # public URL
    return "https://s3-{0}.amazonaws.com/{1}/{2}".format(
        "us-west-2", bucket_name, file_name
    )


def upload_file(aws_s3_client, filename, bucket_name):
    # upload_file() returns None on success and raises on failure
    key = os.path.basename(filename)
    aws_s3_client.upload_file(filename, bucket_name, key)
    return True
 
def upload_file_obj(aws_s3_client, filename, bucket_name):
    with open(filename, "rb") as file:
        aws_s3_client.upload_fileobj(file, bucket_name, "hello_obj.txt")


def upload_file_put(aws_s3_client, filename, bucket_name):
    with open(filename, "rb") as file:
        aws_s3_client.put_object(
            Bucket=bucket_name, Key="hello_put.txt", Body=file.read()
        )

def validate_mimetype(filename: str) -> str:
    mime, _ = mimetypes.guess_type(filename)
    if mime is None:
        mime = "application/octet-stream"
    return mime

def multipart_upload(aws_s3_client, filename, bucket_name):
    mime = validate_mimetype(filename)
    key = os.path.basename(filename)
    total_bytes = os.stat(filename).st_size
 
    print(f"[INFO] Multipart upload → s3://{bucket_name}/{key}")
    print(f"[INFO] ზომა: {total_bytes:,} bytes | ნაწილი: {PART_BYTES:,} bytes")
 
    mpu = aws_s3_client.create_multipart_upload(
        Bucket=bucket_name,
        Key=key,
        ContentType=mime,
    )
    mpu_id = mpu["UploadId"]
 
    parts = []
    uploaded_bytes = 0
 
    try:
        with open(filename, "rb") as f:
            i = 1
            while True:
                data = f.read(PART_BYTES)
                if not data:
                    break
                part = aws_s3_client.upload_part(
                    Body=data,
                    Bucket=bucket_name,
                    Key=key,
                    UploadId=mpu_id,
                    PartNumber=i,
                )
                parts.append({"PartNumber": i, "ETag": part["ETag"]})
                uploaded_bytes += len(data)
 
                pct = uploaded_bytes / total_bytes * 100
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                print(f"\r  [{bar}] {pct:5.1f}%", end="", flush=True)
                i += 1
 
        print()
 
        result = aws_s3_client.complete_multipart_upload(
            Bucket=bucket_name,
            Key=key,
            UploadId=mpu_id,
            MultipartUpload={"Parts": parts},
        )
        return result
 
    except Exception as exc:
        print(f"\n[ERROR] {exc}")
        aws_s3_client.abort_multipart_upload(
            Bucket=bucket_name, Key=key, UploadId=mpu_id
        )
        raise
 