import piexif
from PIL import Image

def encode_as_utf16le_null_terminated(text):
    """Encodes a string to UTF-16LE with a null terminator."""
    return text.encode('utf-16le') + b'\x00\x00'

# function to read and update meta data in the imagefile
def update_metadata(image, caption, filename):
    # Load the image
    image_path = image
    image = Image.open(image_path)

    # Load existing EXIF data
    exif_dict = piexif.load(image.info.get('exif', b''))

    # Ensure all IFDs are dictionaries and handle NoneType for thumbnail
    for ifd in ["0th", "Exif", "GPS", "1st"]:
        if exif_dict.get(ifd) is None:
            exif_dict[ifd] = {}

    # Set the XPSubject field with the correctly encoded value
    new_subject = caption
    new_title = filename
    exif_dict["0th"][piexif.ImageIFD.XPSubject] = encode_as_utf16le_null_terminated(new_subject)
    exif_dict["0th"][piexif.ImageIFD.XPTitle] = encode_as_utf16le_null_terminated(new_title)

    # Generate new EXIF bytes
    exif_bytes = piexif.dump(exif_dict)

    # Save the image with the updated EXIF data
    image.save(image_path, exif=exif_bytes)
