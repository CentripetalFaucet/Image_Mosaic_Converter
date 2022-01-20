from tkinter import *
from PIL import Image
from os import *
import time
import numpy as np
import math


class MosaicCreator:
    def __init__(self, block_size=5, size_reduction_factor=1, alpha_adjustment=0.0):
        # -------------------
        # Adjust this value to change the resolution of the final image
        self.block_size = block_size
        self.size_reduction_factor = size_reduction_factor
        self.alpha_adjustment = max(0.0, min(1.0, alpha_adjustment))  # Range of 0-1

        self.image_width = None
        self.image_height = None
        self.micro_block_size = 0

    def create_mosaic(self, micro_images, main_image):
        # Open image files
        opened_images = self.open_images(micro_images)
        main_image = Image.open(main_image)

        # Resize images based on dimensions of small and large images
        self.image_width, self.image_height = main_image.size
        smallest_image, opened_images = self.resize_images(opened_images)

        # Divide the large image into segments and find which micro image best matches each segment
        print("Getting pixel colours of main image")
        colour_array = self.get_pixel_colours(main_image)
        blocked_micro_images = self.get_micro_image_blocks(opened_images)
        image_array = self.find_closest_image(colour_array, blocked_micro_images)

        # Create new blank image with dimensions to fit all images in collage
        # Image.new cannot handle any width/height higher than ~100,000px
        print("Creating blank canvas")
        mini_image_width, mini_image_height = smallest_image.size
        width_ratio = int(mini_image_width / self.block_size)
        height_ratio = int(mini_image_height / self.block_size)

        output_height = self.image_width * width_ratio
        output_width = self.image_height * height_ratio
        new_im = Image.new('RGB', (output_height, output_width))

        # Paste images into collage
        print("Pasting images into collage")
        for index, row in enumerate(image_array):
            for column_index, image in enumerate(row):
                new_im.paste(image, (column_index * mini_image_width, index * mini_image_height))
        new_im.save("Output/Updated_Collage.jpg")

    def open_images(self, images):
        """
        Opens all of the micro-images.

        :param images: Array of the micro-images
        :return: The opened micro-images.
        """

        opened_images = []
        for image in images:
            print(image)
            opened_image = Image.open(image)
            opened_images.append(opened_image)
        return opened_images

    def resize_images(self, images):
        """
        Resizes all of the micro-images to conform to a collage-able format.
        First, crops all images to a square.
        Second, clips any excess pixels that would not be divisible by the block size.
        Third, if the image is too large for PIL to handle, shrinks the image to the largest it can be within PIL's
        limits.
        Finally, resizes all images to match the smallest image in the images array.

        :param images: Array of all of the micro-images
        :return: Array of the resized micro-images.
        """

        print("Resizing Images")
        if self.size_reduction_factor != 1:
            for index, image in enumerate(images):
                reduced_width = int(image.width / self.size_reduction_factor)
                reduced_height = int(image.height / self.size_reduction_factor)
                images[index] = image.resize(
                    (reduced_width, reduced_height))

        for index, image in enumerate(images):
            image = self.crop_to_square(image)
            excess = image.height % self.block_size
            if not(excess == 0):
                image = image.resize((image.width - excess, image.height - excess))

            # Resize the image if it is larger than PIL can manage when creating a new image
            max_pil_image_size = 100000
            max_image_size = max(max_pil_image_size / self.image_height, max_pil_image_size / self.image_width)
            max_within_block_size = int(max_image_size - max_image_size % self.block_size)
            image_size = min(max_within_block_size, image.height)
            image = image.resize((image_size, image_size))
            images[index] = image

        smallest_image = min(images, key=lambda p: p.size)
        for index, image in enumerate(images):  # Used to say opened_images[1:], unsure why
            if image.size[0] != image.size[1]:
                images[index] = self.crop_to_square(image)
                print("Not redundant")
            if image.size != smallest_image.size:
                images[index] = image.resize(smallest_image.size)

        return smallest_image, images

    def find_closest_image(self, colour_array, micro_images):
        """
        Iterates through each block of the main image and finds the closest matching micro-image, based on the colours
        of each pixel.

        :param colour_array: The main image, with each pixel represented as an RBG tuple.
        :param micro_images: Array of all of the micro-images
        :return: An array representing the finished collage, with image objects in place of the blocks.
        """

        print("Finding the closest matching micro-image for each block of the image")
        image_array = []
        row_count = 0

        block_size = self.block_size

        while row_count < len(colour_array) - block_size + 1:
            image_array.append([])
            column_count = 0
            while column_count < len(colour_array[0]) - block_size + 1:
                block_pixels = []
                for rowPlus in range(block_size):
                    block_pixels.append([])
                    for columnPlus in range(block_size):
                        current_pixel = colour_array[row_count + rowPlus][column_count + columnPlus]
                        block_pixels[-1].append(current_pixel)
                closest_image = self.find_matching_micro(block_pixels, micro_images)
                # print(closest_image)
                # closest_image = self.apply_alpha_adjustment(block_pixels, closest_image)
                image_array[-1].append(closest_image)

                column_count += block_size
            row_count += block_size
            print("Processed row", row_count)
        return image_array

    # def apply_alpha_adjustment(self, block_pixels, closest_image):
    #     # closest_image_blocked = self.get_micro_image_blocks([closest_image])[0][1]
    #     closest_image_blocked = self.get_pixel_colours(closest_image)
    #     # print(block_pixels)
    #     # print(closest_image_blocked)
    #     flattened_image = []
    #
    #     for row_index, row in enumerate(block_pixels):
    #         for column_index, pixel in enumerate(row):
    #             for rowPlus in range(self.micro_block_size):
    #                 for columnPlus in range(self.micro_block_size):
    #                     image_segment = closest_image_blocked[row_index + rowPlus][column_index + columnPlus]
    #
    #                     red_adjustment = round(image_segment[0] - (self.alpha_adjustment * (image_segment[0] - pixel[0])))
    #                     green_adjustment = round(image_segment[1] - (self.alpha_adjustment * (image_segment[1] - pixel[1])))
    #                     blue_adjustment = round(image_segment[2] - (self.alpha_adjustment * (image_segment[2] - pixel[2])))
    #                     # closest_image_blocked[row_index][pixel_index] = (red_adjustment, green_adjustment, blue_adjustment)
    #                     flattened_image.append((red_adjustment, green_adjustment, blue_adjustment))
    #     # print(closest_image_blocked)
    #     image_size = (len(closest_image_blocked), len(closest_image_blocked))
    #     closest_image_with_alpha = Image.new("RGB", image_size)
    #     closest_image_with_alpha.putdata(flattened_image)
    #     # print(closest_image_with_alpha)
    #     return closest_image_with_alpha



    def get_micro_image_blocks(self, micro_images):
        """
        Divides all micro-images into segments based on self.block_size to compare each segment against main image.
        Segment size is determines by the height and width of the micro-image being divided by the block size.
        For example, a block size of 5 will result in 25 segments for each image, which correspond to the 25 pixels in
        each block of the larger image.

        :param micro_images: Array of all images to be segmented
        :return: The average colour of each segment, for each image in the micro_images array
        """

        # print("Dividing micro-images into segments to compare against larger image pixels")
        micro_block_colours = []
        count = 1

        for image in micro_images:
            self.micro_block_size = image.height // self.block_size
            colour_array = self.get_pixel_colours(image)
            colour_array = self.get_average_pixels(colour_array, self.micro_block_size)

            micro_block_colours.append((image, colour_array))

            count += 1

        return micro_block_colours

    def find_matching_micro(self, block_pixels, micro_images):
        """
        Finds the micro-image which best matches the pixels of the block in the main image to the segments of the
        micro-image.
        This is done by comparing the total RBG difference for each pixel, and finding the micro-image which has the
        least difference to the original image.

        :param block_pixels: An array of the colour values of all of the pixel in a block of the main image.
        :param micro_images: Array of all of the micro-images
        :return: The closest matching image to the block
        """
        differences = []
        for micro_image in micro_images:
            image_colours = micro_image[1]
            colour_difference = 0
            for row_index, row in enumerate(block_pixels):
                for column_index, pixel in enumerate(row):
                    difference = self.get_pixel_difference(pixel, image_colours[row_index][column_index])
                    colour_difference += difference
            differences.append((micro_image[0], colour_difference))
        closest_image = min(differences, key=lambda x: x[1])
        return closest_image[0]

    def get_pixel_difference(self, pixel, micro_image_pixel):
        """
        Gets the total RBG difference between the pixel from the main image and the segment from the micro-image.

        :param pixel: The RBG colour values of a pixel in the main image.
        :param micro_image_pixel: The average RBG colour values in the corresponding segment of a micro-image.
        :return: The total RBG difference between the two colour values.
        """

        difference = 0
        for i in range(2):
            difference += abs(pixel[i] - micro_image_pixel[i])
        return difference

    def crop_to_square(self, image):
        """
        Crops an image to be completely square, based on the smallest side of the image.

        :param image: Image to be cropped.
        :return: The cropped image.
        """

        small_side = min(image.size)
        center = (image.size[0] / 2, image.size[1] / 2)
        half_side = small_side / 2
        crop_box = (center[0] - half_side, center[1] - half_side, center[0] + half_side, center[1] + half_side)
        return image.crop(crop_box)

    def get_pixel_colours(self, image):
        """
        Gets the colour matrix for each pixel of an image, and returns an array of colour matrices.
        Each sub-array corresponds to a row of pixels in the original image.

        :param image: Image for which to retrieve the colour values.
        :return: An array of arrays of RGB colour matrices, where each matrix = one pixel.
        """

        pixel_array = []
        image_width, image_height = image.size
        for i in range(image_height):
            pixel_array.append([])
            for j in range(image_width):
                coordinates = j, i
                pixel_colour = image.getpixel(coordinates)
                pixel_array[i].append(pixel_colour)
        return pixel_array

    # noinspection DuplicatedCode
    def get_average_pixels(self, colour_array, set_block_size=-1):
        """
        Gets the average brightness of each square of pixels for the entire image.
        Square size is based on self.block_size, so if block_size is 5, square is 5x5.

        :param colour_array: An array of arrays of RGB colour matrices
                            Each matrix = one pixel on the original image.
        :param set_block_size: Enables the function to use custom block sizes.
                                Default value of -1 means that the function will use self.block_size.
        :return: An array of arrays of average brightnesses. Each sub-array corresponds to a row of the image.
        """

        pixel_array = []
        row_count = 0

        # Allows custom block size, but default is class attribute
        if set_block_size == -1:
            block_size = self.block_size
        else:
            block_size = set_block_size

        while row_count < len(colour_array) - block_size + 1:
            pixel_array.append([])
            column_count = 0
            while column_count < len(colour_array[0]) - block_size + 1:
                red_total = 0
                green_total = 0
                blue_total = 0
                for rowPlus in range(block_size):
                    for columnPlus in range(block_size):
                        current_pixel = colour_array[row_count + rowPlus][column_count + columnPlus]
                        red_total += current_pixel[0]
                        green_total += current_pixel[1]
                        blue_total += current_pixel[2]
                red_average = red_total / (block_size * block_size)
                green_average = green_total / (block_size * block_size)
                blue_average = blue_total / (block_size * block_size)
                average = (red_average, green_average, blue_average)

                if set_block_size == -1:
                    addition = None
                    for index, threshold in enumerate(self.light_thresholds):
                        if average < threshold:
                            addition = index
                            break
                        else:
                            addition = -1
                    pixel_array[row_count // block_size].append(addition)
                else:
                    pixel_array[row_count // block_size].append(average)
                column_count += block_size
            row_count += block_size
        return pixel_array


def list_directory(basepath):
    """Retrieves all java files in the directory and yields the full path"""

    for root, dirs, files in walk(basepath, topdown=False):
        for name in files:
            yield path.join(root, name)


def main():
    start = time.process_time()
    mosaic_creator = MosaicCreator(block_size=3, size_reduction_factor=1, alpha_adjustment=0.2)

    mini_image_folder = r"Source_Images/Micro_Images/Random_Images"
    big_image = r"Source_Images/Main_Images/Example.jpg"

    mini_images = []
    for file in list_directory(mini_image_folder):
        mini_images.append(file)

    mosaic_creator.create_mosaic(mini_images, big_image)
    time_taken = time.process_time() - start
    print("Completed in " + str(time_taken) + " seconds")


if __name__ == '__main__':
    main()

# TODO: Add colour adjustment
# TODO: Create UI
