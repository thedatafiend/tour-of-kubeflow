"""
Taken from: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-examples.html
"""
import logging
import boto3
from botocore.exceptions import ClientError
import os


def upload_blob(bucket_name, source_file_name, destination_blob_name=None):
    """Upload a file to an S3 bucket

    :param bucket: Bucket to upload to
    :param file_name: File to upload
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # If S3 object_name was not specified, use file_name
    if destination_blob_name is None:
        destination_blob_name = os.path.basename(source_file_name)

    # Upload the file
    s3_client = boto3.client("s3")
    try:
        response = s3_client.upload_file(
            source_file_name, bucket_name, destination_blob_name
        )
        logger.info(response)
    except ClientError as e:
        logger.error(e)
        return False
    return True


def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Download a file from an S3 bucket

    :param bucket: _description_
    :param source_blob_name: _description_
    param: destination_file_name: _description_
    :return: True if file was successfully downloaded, else False
    """
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    try:
        s3 = boto3.client("s3")
        s3.download_file(bucket_name, source_blob_name, destination_file_name)
    except ClientError as e:
        logger.error(e)
        return False
    return True
