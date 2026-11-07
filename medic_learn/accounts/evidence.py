"""Private student evidence: no public URLs or user-controlled storage paths."""

import io
import uuid
import warnings

import boto3
from botocore.config import Config
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from PIL import Image
from pypdf import PdfReader

from .domain import AccountError
from .models import Evidence


def validate(file):
    data = file.read(10 * 1024 * 1024 + 1)
    if not data or len(data) > 10 * 1024 * 1024:
        raise AccountError("invalid_file", "Upload an image or PDF no larger than 10 MB.")
    try:
        if data.startswith(b"%PDF-"):
            pdf = PdfReader(io.BytesIO(data), strict=True)
            if pdf.is_encrypted or not 1 <= len(pdf.pages) <= 10:
                raise ValueError()
            # Reject embedded active content; documents are served only as downloads.
            for marker in (
                b"/JavaScript",
                b"/JS",
                b"/Launch",
                b"/EmbeddedFile",
                b"/OpenAction",
                b"/AA",
            ):
                if marker in data:
                    raise ValueError()
            return data, "application/pdf"
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            image = Image.open(io.BytesIO(data))
            if image.format not in {"JPEG", "PNG"}:
                raise ValueError()
            image.verify()
            # Re-encode images to discard metadata and appended content.
            image = Image.open(io.BytesIO(data))
            output = io.BytesIO()
            image.convert("RGB").save(output, format="JPEG")
            return output.getvalue(), "image/jpeg"
    except Exception as exc:
        raise AccountError(
            "invalid_file", "Upload a valid JPEG, PNG, or unencrypted PDF card."
        ) from exc


def local_storage():
    return FileSystemStorage(location=settings.EVIDENCE_ROOT)


def upload(user, file):
    data, content_type = validate(file)
    key = f"cards/{uuid.uuid4()}"
    # Create a cleanup-addressable record before remote I/O; never lose track of an object.
    record = Evidence.objects.create(user=user, key=key, content_type=content_type, available=False)
    try:
        if settings.EVIDENCE_BUCKET:
            boto3.client(
                "s3",
                region_name=settings.AWS_REGION,
                config=Config(connect_timeout=5, read_timeout=10, retries={"max_attempts": 1}),
            ).put_object(
                Bucket=settings.EVIDENCE_BUCKET,
                Key=key,
                Body=data,
                ContentType=content_type,
                ServerSideEncryption="AES256",
            )
        else:
            local_storage().save(key, ContentFile(data))
        record.available = True
        record.save(update_fields=["available"])
        return record
    except Exception as exc:
        from .models import Operation

        Operation.objects.create(user=user, kind="delete_evidence", payload={"id": str(record.pk)})
        raise AccountError(
            "storage_unavailable", "The upload could not be saved. Try again.", 503
        ) from exc


def read(record):
    if settings.EVIDENCE_BUCKET:
        return boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            config=Config(connect_timeout=5, read_timeout=10, retries={"max_attempts": 1}),
        ).get_object(Bucket=settings.EVIDENCE_BUCKET, Key=record.key)["Body"]
    return local_storage().open(record.key, "rb")


def delete(record):
    if settings.EVIDENCE_BUCKET:
        boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            config=Config(connect_timeout=5, read_timeout=10, retries={"max_attempts": 1}),
        ).delete_object(Bucket=settings.EVIDENCE_BUCKET, Key=record.key)
    else:
        local_storage().delete(record.key)
