from PIL import Image
from pyzbar.pyzbar import decode
import cv2
import numpy as np


def _pil_to_cv2(img_pil):
    arr = np.array(img_pil.convert('RGB'))
    # PIL gives RGB, OpenCV uses BGR
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def _try_pyzbar(pil_img):
    decoded = decode(pil_img)
    if not decoded:
        return None
    return decoded[0].data.decode('utf-8')


def _try_cv2(img_cv):
    try:
        detector = cv2.QRCodeDetector()
        data, points, _ = detector.detectAndDecode(img_cv)
        if data:
            return data
    except Exception:
        pass
    return None


def extract_qr_data(image_path):
    """Attempt to decode QR/barcode data from an image using multiple strategies.

    Strategy order:
    1. pyzbar on original image
    2. OpenCV QRCodeDetector on original image
    3. Preprocessed grayscale/threshold + rotations with both decoders

    Returns the first payload string found, or None.
    """
    try:
        pil_img = Image.open(image_path)
    except Exception:
        return None

    # 1) Try pyzbar on the original image
    result = _try_pyzbar(pil_img)
    if result:
        return result

    # 2) Try OpenCV detector on original image
    cv_img = _pil_to_cv2(pil_img)
    result = _try_cv2(cv_img)
    if result:
        return result

    # 3) Try stronger preprocessing: denoise, adaptive threshold, contour-based warp
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

    # Denoise and equalize
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)
    equalized = cv2.equalizeHist(denoised)

    # Attempt to find a quadrilateral that could be the QR area and warp it
    def _order_points(pts):
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    def _find_and_warp(src_gray, src_color):
        # Edge detection and contour search
        edged = cv2.Canny(src_gray, 50, 200)
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        for cnt in contours:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            if len(approx) == 4:
                pts = approx.reshape(4, 2)
                rect = _order_points(pts)
                (tl, tr, br, bl) = rect
                widthA = np.linalg.norm(br - bl)
                widthB = np.linalg.norm(tr - tl)
                maxWidth = max(int(widthA), int(widthB))
                heightA = np.linalg.norm(tr - br)
                heightB = np.linalg.norm(tl - bl)
                maxHeight = max(int(heightA), int(heightB))

                dst = np.array([
                    [0, 0],
                    [maxWidth - 1, 0],
                    [maxWidth - 1, maxHeight - 1],
                    [0, maxHeight - 1]], dtype="float32")

                M = cv2.getPerspectiveTransform(rect, dst)
                warped = cv2.warpPerspective(src_color, M, (maxWidth, maxHeight))
                return warped

        return None

    warped = _find_and_warp(equalized, cv_img)
    if warped is not None:
        # try detectors on the warped area (and a resized version)
        for scale in (1.0, 1.5, 2.0):
            try:
                h, w = warped.shape[:2]
                resized = cv2.resize(warped, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LINEAR)
            except Exception:
                resized = warped

            # Try pyzbar
            try:
                pil_candidate = Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
                result = _try_pyzbar(pil_candidate)
                if result:
                    return result
            except Exception:
                pass

            # Try OpenCV detector
            result = _try_cv2(resized)
            if result:
                return result

    # 4) Fallback: try adaptive threshold + rotations
    for proc in (equalized, denoised, gray):
        try:
            proc_thresh = cv2.adaptiveThreshold(proc, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                cv2.THRESH_BINARY, 11, 2)
        except Exception:
            proc_thresh = proc

        for angle in (0, 90, 180, 270):
            if angle != 0:
                (h, w) = proc_thresh.shape[:2]
                M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
                rotated = cv2.warpAffine(proc_thresh, M, (w, h))
            else:
                rotated = proc_thresh

            try:
                pil_rot = Image.fromarray(cv2.cvtColor(rotated, cv2.COLOR_GRAY2RGB))
            except Exception:
                pil_rot = Image.fromarray(rotated)

            result = _try_pyzbar(pil_rot)
            if result:
                return result

            result = _try_cv2(cv2.cvtColor(np.array(pil_rot), cv2.COLOR_RGB2BGR))
            if result:
                return result

    return None
