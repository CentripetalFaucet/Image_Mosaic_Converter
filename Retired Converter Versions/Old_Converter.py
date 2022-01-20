from tkinter import *
from PIL import Image
from os import *


class MosaicCreator:
    def __init__(self, block_size=5):
        # -------------------
        # Adjust this value to change the resolution of the final image
        self.block_size = block_size

        # -------------------
        # Adjust these to change the colour thresholds
        self.base_threshold = 460
        self.light_thresholds = []
        self.increment_scaling = 10

        self.image_width = None
        self.image_height = None

    def create_mosaic(self, micro_images, main_image):

        # Region - Pull into function
        opened_images = []
        for image in micro_images:
            opened_image = Image.open(image)
            opened_images.append(opened_image)

        smallest_image = min(opened_images, key=lambda p: p.size)
        for index, image in enumerate(opened_images[1:]):
            if image.size[0] != image.size[1]:
                opened_images[index] = self.crop_to_square(image)
            if image.size != smallest_image.size:
                opened_images[index] = image.resize(smallest_image.size)

        sorted_images = self.sort_images_by_shade(opened_images)


        # End Region

        mini_image_width, mini_image_height = smallest_image.size

        width_ratio = int(mini_image_width / self.block_size)
        height_ratio = int(mini_image_height / self.block_size)

        main_image = Image.open(main_image)
        self.adjust_base_threshold(main_image)
        self.set_light_thresholds(micro_images)
        colour_array = self.get_pixel_colours(main_image)
        colour_array = self.get_average_pixels(colour_array)

        new_im = Image.new('RGB', (self.image_width * width_ratio, self.image_height * height_ratio))

        for index, row in enumerate(colour_array):
            for cIndex, column in enumerate(row):
                image = sorted_images[column]
                print(image)
                new_im.paste(image, (cIndex * mini_image_width, index * mini_image_height))
        new_im.save("Output/Old_Collage.jpg")

    def adjust_base_threshold(self, image):
        square_image = self.crop_to_square(image)
        pixel_array = self.get_pixel_colours(square_image)
        average_shade = self.get_average_pixels(pixel_array, square_image.size[0])[0][0]
        minimum_shade = self.get_darkest_block(pixel_array)
        maximum_shade = self.get_brightest_block(pixel_array)
        self.increment_scaling = (abs(average_shade - minimum_shade) + abs(average_shade - maximum_shade)) / 40

        self.base_threshold = (self.base_threshold + maximum_shade + minimum_shade + average_shade) / 4

    def get_darkest_block(self, pixel_array):
        block_array = self.get_average_pixels(pixel_array, self.block_size)
        darkest_block = min(min(row for row in block_array))
        return darkest_block

    def get_brightest_block(self, pixel_array):
        block_array = self.get_average_pixels(pixel_array, self.block_size)
        brightest_block = max(max(row for row in block_array))
        return brightest_block

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

    def set_light_thresholds(self, micro_images):
        """
        Sets the shade thresholds at which different micro-images are used, based on the number of micro-images.

        :param micro_images: a list of images that the picture will be made up of.
        """

        # TODO: Change base threshold based on big image colour
        base_reduction = 4 * self.increment_scaling
        increment = 8 * self.increment_scaling
        self.light_thresholds.append(self.base_threshold - base_reduction * (len(micro_images) - 1))
        for i in range(len(micro_images[1:-1])):
            self.light_thresholds.append(self.light_thresholds[0] + increment * (i + 1))

    def sort_images_by_shade(self, images):
        """
        Sorts the list of images by their shade.

        :param images: An unsorted list of images.
        :return: The sorted list of images, with the darkest images at the start of the list.
        """

        sorted_list = []
        sorted_shades = []

        for image in images:
            pixel_array = self.get_pixel_colours(image)
            average_shade = self.get_average_pixels(pixel_array, image.size[0])[0][0]
            self.adjust_images_towards_averages(image, average_shade)
            average_shade = self.get_average_pixels(pixel_array, image.size[0])[0][0]

            add_index = -1
            for index, shade in enumerate(sorted_shades):
                if average_shade < shade:
                    add_index = index
                    break
            if add_index != -1:
                sorted_list.insert(add_index, image)
                sorted_shades.insert(add_index, average_shade)
            else:
                sorted_list.append(image)
                sorted_shades.append(average_shade)

        return sorted_list

    def get_pixel_colours(self, image):
        """
        Gets the colour matrix for each pixel of an image, and returns an array of colour matrices.
        Each sub-array corresponds to a row of pixels in the original image.

        :param image: Image for which to retrieve the colour values.
        :return: An array of arrays of RGB colour matrices, where each matrix = one pixel.
        """

        pixel_array = []
        self.image_width, self.image_height = image.size
        for i in range(self.image_height):
            pixel_array.append([])
            for j in range(self.image_width):
                coordinates = j, i
                pixel_colour = image.getpixel(coordinates)
                pixel_array[i].append(pixel_colour)
        return pixel_array

    # def get_total_block_colour(self, colour_array, set_block_size=-1, block_setting=BlockSetting.average):
    #     block_array = []
    #     row_count = 0
    #
    #     # Allows custom block size, but default is class attribute
    #     if set_block_size == -1:
    #         block_size = self.block_size
    #     else:
    #         block_size = set_block_size
    #
    #     while row_count < len(colour_array):
    #         block_array.append([])
    #         column_count = 0
    #         while column_count < len(colour_array[0]):
    #             total = 0
    #             for rowPlus in range(block_size):
    #                 for columnPlus in range(block_size):
    #                     current_pixel = colour_array[row_count][column_count]
    #                     total += (current_pixel[0] + current_pixel[1] + current_pixel[2])
    #
    #             if block_setting == BlockSetting.average:
    #                 average = total / (block_size * block_size)
    #                 if set_block_size == -1:
    #                     addition = None
    #                     for index, threshold in enumerate(self.light_thresholds):
    #                         if average < threshold:
    #                             addition = index
    #                             break
    #                         else:
    #                             addition = -1
    #                     block_array[row_count // block_size].append(addition)
    #                 else:
    #                     block_array[row_count // block_size].append(average)
    #
    #             column_count += block_size
    #         row_count += block_size
    #     return block_array

    def adjust_images_towards_averages(self, image, average):
        loaded_image = image.load()
        average_colour = average / 3
        for x in range(image.width):
            for y in range(image.height):
                colours = []
                for colour_value in loaded_image[x, y]:
                    colour_diff = abs(colour_value - average_colour)
                    # if colour_diff > 100:
                        # print(colour_value)
                    colour_value -= (colour_value - average_colour) / 2
                        # print(colour_value)
                    colours.append(int(colour_value))
                loaded_image[x, y] = tuple(colours)
        #         loaded_image[x, y] = (0,255,0)

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
                total = 0
                for rowPlus in range(block_size):
                    for columnPlus in range(block_size):
                        current_pixel = colour_array[row_count + rowPlus][column_count + columnPlus]
                        total += (current_pixel[0] + current_pixel[1] + current_pixel[2])
                average = total / (block_size * block_size)

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


# mosaic_creator = MosaicCreator(block_size=3)
#
# # mini_images = ["/home/cosc/student/hwm26/Pictures/Fabian_Darker.jpg",
# #                "/home/cosc/student/hwm26/Pictures/Moffat_Darker.jpg",
# #                "/home/cosc/student/hwm26/Pictures/Miguel_Darker.jpg"]
#
# mini_images = ["/home/cosc/student/hwm26/Pictures/Shades/Black.jpg",
#                "/home/cosc/student/hwm26/Pictures/Shades/Light.jpg",
#                "/home/cosc/student/hwm26/Pictures/Shades/Mid_Squashed.jpg",
#                "/home/cosc/student/hwm26/Pictures/Shades/MidDark.jpg",
#                "/home/cosc/student/hwm26/Pictures/Shades/Dark.jpg",
#                "/home/cosc/student/hwm26/Pictures/Shades/White_small.jpg"]
# big_image = "/home/cosc/student/hwm26/Pictures/Matthias_A4.jpg"
# mosaic_creator.create_mosaic(mini_images, big_image)

def list_directory(basepath):
    """Retrieves all java files in the directory and yields the full path"""

    for root, dirs, files in walk(basepath, topdown=False):
        for name in files:
            yield path.join(root, name)


def main():
    mosaic_creator = MosaicCreator(block_size=5)

    # mini_images = ["/home/cosc/student/hwm26/Pictures/Fabian_Darker.jpg",
    #                "/home/cosc/student/hwm26/Pictures/Moffat_Darker.jpg",
    #                "/home/cosc/student/hwm26/Pictures/Miguel_Darker.jpg"]

    mini_images = []
    for file in list_directory("Source_Images/Micro_Images/Shades"):
        mini_images.append(file)

    # mini_images = ["/home/cosc/student/hwm26/Pictures/Shades/Black.jpg",
    #                "/home/cosc/student/hwm26/Pictures/Shades/Light.jpg",
    #                "/home/cosc/student/hwm26/Pictures/Shades/Mid_Squashed.jpg",
    #                "/home/cosc/student/hwm26/Pictures/Shades/MidDark.jpg",
    #                "/home/cosc/student/hwm26/Pictures/Shades/Dark.jpg",
    #                "/home/cosc/student/hwm26/Pictures/Shades/White_small.jpg"]
    big_image = "Source_Images/Main_Images/Fabian_Gilson.jpg"
    # big_image = "/home/cosc/student/hwm26/Pictures/Matthias_A4.jpg"
    # big_image = "/home/cosc/student/hwm26/Pictures/greyscale.jpeg"
    # big_image = "/home/cosc/student/hwm26/Pictures/pexels-photo-333850.jpeg"
    # big_image = "/home/cosc/student/hwm26/Pictures/bright_light.jpg"
    # big_image = "/home/cosc/student/hwm26/Pictures/clouds.jpg"
    mosaic_creator.create_mosaic(mini_images, big_image)
    #
    # window = Tk()
    # window.geometry("500x500")
    #
    # window_frame = Frame(window)
    # window.title("Mosaic")
    # # window_frame.pack(side=TOP)
    # window_frame.grid(row=0)
    # window_frame.configure(height=500, width=500)
    # window_frame.grid_propagate(0)
    #
    # for i in range(5):
    #     Frame(window_frame, width=100, height=100, background='#CCCCFF').grid(row=0, column=i)
    #
    # for j in range(5):
    #     Frame(window_frame, width=100, height=100, background='#CCCCFF').grid(column=0, row=j)
    #
    # add_big_image = Label(window_frame, text="Add Main Image", borderwidth=2, relief="sunken", height=9, width=19)
    # add_big_image.grid(row=0, column=2)
    #
    # window.mainloop()


if __name__ == '__main__':
    main()

# TODO: Add colour adjustment
# TODO Maybe? Adjust micro-images to remove extremes/change extremes
#       For all pixels in the image, if the pixel has x difference to the average, add y to colour
#       Could be v slow
# TODO: Create UI
