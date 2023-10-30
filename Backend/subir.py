import boto3
import subprocess

archivo_png="reporte.png"


aws_access_key_id = "AKIA5UETS3BYMABIGJVT"
aws_secret_access_key = "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"
bucket_name="mia-p2-202000544"

s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
s3.upload_file(archivo_png, bucket_name, archivo_png)
