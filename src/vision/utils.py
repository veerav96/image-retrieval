from io import BytesIO
import cv2
import numpy as np
import uuid
from fastapi import UploadFile
from hydra import compose

cfg = compose(config_name='config')


def preprocess_image(image_content: bytes, coordinates, minio_client):
    image_bytes = np.frombuffer(image_content, np.uint8)
    image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)

    pts = np.array(coordinates, dtype='float32')
    warped_image = perspective_transform(image, pts)

    is_success, buffer = cv2.imencode('.jpg', warped_image)
    if not is_success:
        raise ValueError('Failed to encode image')

    image_bytes_io = BytesIO(buffer)
    filename = f'papyrus_{uuid.uuid4()}.jpg'

    bucket_name = cfg.storage.buckets[0]
    minio_client.client.put_object(bucket_name, filename, image_bytes_io, len(buffer), content_type='image/jpeg')

    return filename


def read_image_file(image_file: UploadFile):
    image_bytes = np.frombuffer(image_file.file.read(), np.uint8)
    image_file.file.seek(0)  # Reset file pointer to the beginning
    image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
    return image


def order_points(pts):
    rect = np.zeros((4, 2), dtype='float32')
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # Top-left
    rect[2] = pts[np.argmax(s)]  # Bottom-right
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # Top-right
    rect[3] = pts[np.argmax(diff)]  # Bottom-left
    return rect


def perspective_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # Compute the width of the new image
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = int(max(widthA, widthB))

    # Compute the height of the new image
    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = int(max(heightA, heightB))

    # Create a destination matrix for the new image size
    dst = np.array([[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]], dtype='float32')

    # Compute the perspective transform matrix
    M = cv2.getPerspectiveTransform(rect, dst)

    # Warp the image to the new perspective
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight), borderMode=cv2.BORDER_TRANSPARENT)

    return warped
