import os
import re
import exif


def get_unique_filename(base_name, extension, existing_names, directory):
	"""Generate a unique filename by appending a counter if needed."""
	candidate_name = f"{base_name}{extension}"
	candidate_path = os.path.join(directory, candidate_name)

	if candidate_name not in existing_names and not os.path.exists(candidate_path):
		return candidate_name

	counter = 1
	while True:
		candidate_name = f"{base_name}-{counter}{extension}"
		candidate_path = os.path.join(directory, candidate_name)
		if candidate_name not in existing_names and not os.path.exists(candidate_path):
			return candidate_name
		counter += 1


def update_image_metadata(image_path, caption, filename):
    """Update the subject field in the image's metadata to match the caption."""
    try:
        exif.update_metadata(image_path, caption, filename)
    except Exception as e:
        print(f"Failed to update metadata for {image_path}: {e}")


def rename_files(captions_file):
	existing_names = set()

	with open(captions_file, 'r') as file:
		lines = file.readlines()

		base_directory = lines[0].replace('Source URL:', '').strip()
		base_directory = os.path.normpath(base_directory)

		for existing_file in os.listdir(base_directory):
			existing_names.add(existing_file)

		for line in lines[1:]:
			line = line.strip()
			if not line or "Original:" not in line or "New File Name:" not in line:
				continue

			try:
				original_match = re.search(r"Original:(\S+)", line)
				new_name_match = re.search(r"New File Name:\('([^']*)', '([^']*)'\)", line)
				caption_match = re.search(r"Caption:(.+)", line)

				if not (original_match and new_name_match and caption_match):
					print(f"Skipping line due to unexpected format: {line}")
					continue

				original_file = original_match.group(1).strip()
				original_file_path = os.path.join(base_directory, original_file)
				original_file_path = os.path.normpath(original_file_path)

				new_base_name = new_name_match.group(1)
				extension = new_name_match.group(2)
				caption = caption_match.group(1).strip()

				new_file_name = get_unique_filename(new_base_name, extension, existing_names, base_directory)
				new_file_path = os.path.join(base_directory, new_file_name)
				new_file_path = os.path.normpath(new_file_path)

				existing_names.add(new_file_name)

				if os.path.exists(original_file_path):
					os.rename(original_file_path, new_file_path)
					print(f"Renamed {original_file_path} to {new_file_path}")

					# Update metadata with the caption
					update_image_metadata(new_file_path, caption, new_base_name)
				else:
					print(f"File {original_file_path} not found. Skipping.")
			except Exception as e:
				print(f"Skipping line due to error: {line}")
				print(f"Error details: {e}")
