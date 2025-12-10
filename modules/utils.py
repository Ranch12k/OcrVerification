import cv2
import base64
from io import BytesIO
from PIL import Image
import numpy as np


def extract_largest_face_base64(image_path, resize_width=400):
	"""Detect faces in the image and return the largest face cropped as a base64 PNG string.

	Returns None if no face is detected or on error.
	"""
	try:
		img = cv2.imread(image_path)
		if img is None:
			return None
	except Exception:
		return None

	# Resize for faster detection while keeping aspect ratio
	h, w = img.shape[:2]
	scale = 1.0
	if w > resize_width:
		scale = resize_width / float(w)
		img_small = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
	else:
		img_small = img.copy()

	gray = cv2.cvtColor(img_small, cv2.COLOR_BGR2GRAY)

	# Use OpenCV's haarcascade (bundled with opencv-python)
	try:
		cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
		face_cascade = cv2.CascadeClassifier(cascade_path)
	except Exception:
		return None

	faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
	if len(faces) == 0:
		return None

	# Choose the largest face by area
	faces = sorted(faces, key=lambda r: r[2] * r[3], reverse=True)
	x, y, fw, fh = faces[0]

	# Map back to original image coordinates
	if scale != 1.0:
		inv_scale = 1.0 / scale
		x = int(x * inv_scale)
		y = int(y * inv_scale)
		fw = int(fw * inv_scale)
		fh = int(fh * inv_scale)

	# Add a small margin
	margin = int(0.15 * max(fw, fh))
	x1 = max(0, x - margin)
	y1 = max(0, y - margin)
	x2 = min(img.shape[1], x + fw + margin)
	y2 = min(img.shape[0], y + fh + margin)

	face_crop = img[y1:y2, x1:x2]

	# Convert to PIL and encode as PNG base64
	try:
		face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
		pil_img = Image.fromarray(face_rgb)
		buffered = BytesIO()
		pil_img.save(buffered, format="PNG")
		b64 = base64.b64encode(buffered.getvalue()).decode('ascii')
		return b64
	except Exception:
		return None

