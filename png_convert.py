import os
from tkinter import Tk, filedialog
from PIL import Image


def convert_jpeg_to_png(input_folder, output_folder, optimize=False, quality=85):
    # Check if the input folder exists
    if not os.path.exists(input_folder):
        print("The specified input folder does not exist.")
        return

    # Check if the output folder exists, if not, create it
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Iterate over all files in the input folder
    for filename in os.listdir(input_folder):
        # Check if the file is a JPEG image
        if filename.lower().endswith(('.jpg', '.jpeg')):
            # Construct full file path
            input_file_path = os.path.join(input_folder, filename)

            # Open the image
            with Image.open(input_file_path) as img:
                # Create new file name by changing the extension to .png
                png_filename = os.path.splitext(filename)[0] + '.png'
                output_file_path = os.path.join(output_folder, png_filename)

                # Save the image in PNG format with optimization
                img.save(output_file_path, 'PNG', optimize=optimize)
                print(f"Converted {filename} to {png_filename} with optimization={optimize}")


def select_folder(prompt):
    root = Tk()
    root.withdraw()  # Hide the root window
    folder_path = filedialog.askdirectory(title=prompt)
    root.destroy()
    return folder_path





