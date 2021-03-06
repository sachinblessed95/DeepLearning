"""A simple ndarray data layer that wraps around numpy arrays."""

from sparse import base
from sparse.util import smalldata
from sparse.util import translator, transform
from os import walk
from os import listdir
from os.path import isfile, join
import numpy as np

_JEFFNET_FLIP = True
INPUT_DIM = 227


class ImageDataLayer(base.DataLayer):
    """This layer takes a bunch of data as a dictionary, and then emits
    them as Blobs.
    """
    
    def __init__(self, **kwargs):
        base.DataLayer.__init__(self, **kwargs)
        self.input_file = self.spec['train']
        self._image_files = None
        

    def load_input_file(self):
        self._image_files = []
        self._labels = {}
        self._num_labels = 0
        #reads the input file
        with open(self.input_file) as f:
            content = f.readlines()
            for row in content:
                image, label = row.split(" ")
                self._image_files.append(image)
                self._labels[image] = float(label)
                self._num_labels = max(self._num_labels, int(label))
        
        self._gen = self.image_gen()
        self._num_images = len(self._image_files)

    def get_num_images(self):
        if self._image_files is None:
            self.load_input_file()
        return self._num_images

    def get_next_image(self, top_blob):
        #get the image name
        try:
            img_name = self._gen.next()
        except StopIteration:
            self._gen = self.image_gen()
            img_name = self._gen.next()

        #load and resize the image
        img = smalldata.get_image(img_name)
        img_converted = self.convert(img)
        top_blob[0].mirror(img_converted)
        assert not np.isnan(top_blob[0].data().sum())
        #print img_name

        #creates the labels vector
        label = [1.0 if i == self._labels[img_name] else 0.0 for i in xrange(2)]
        #print label

        labels = [label for i in xrange(10)]
        top_blob[1]._data[:] = labels

        return top_blob[0], top_blob[1]

    def image_gen(self):
        for img_name in self._image_files:
            yield img_name

    def oversample(self, image, center_only=False):
        """Oversamples an image. Currently the indices are hard coded to the
            4 corners and the center of the image, as well as their flipped ones,
            a total of 10 images.

            Input:
            image: an image of size (256 x 256 x 3) and has data type uint8.
            center_only: if True, only return the center image.
            Output:
            images: the output of size (10 x 227 x 227 x 3)
        """
        indices = [0, 256 - INPUT_DIM]
        center = int(indices[1] / 2)
        if center_only:
            return np.ascontiguousarray(
                image[np.newaxis, center:center + INPUT_DIM,
                center:center + INPUT_DIM], dtype=np.float32)
        else:
            images = np.empty((10, INPUT_DIM, INPUT_DIM, 3),
                dtype=np.float32)
            curr = 0
            for i in indices:
                for j in indices:
                    images[curr] = image[i:i + INPUT_DIM,
                        j:j + INPUT_DIM]
                    curr += 1
            images[4] = image[center:center + INPUT_DIM,
            center:center + INPUT_DIM]
            # flipped version
            images[5:] = images[:5, ::-1]
            return images

    def convert(self, image, center_only=False):
        """Classifies an input image.

           Input:
            image: an image of 3 channels and has data type uint8. Only the
                center region will be used for classification.
           Output:
            scores: a numpy vector of size 1000 containing the
                predicted scores for the 1000 classes.
        """
        # first, extract the 256x256 center.
        image = transform.scale_and_extract(transform.as_rgb(image), 256)
        # convert to [0,255] float32
        image = image.astype(np.float32) * 255.
        if _JEFFNET_FLIP:
            # Flip the image if necessary, maintaining the c_contiguous order
            image = image[::-1, :].copy()
        # subtract the mean
        image -= np.mean(image)
        # oversample the images
        images = self.oversample(image, center_only)
        return images


    def forward(self, bottom, top):
        """Generates the data."""
        if self._image_files is None:
            self.load_input_file()

        top[1].init_data((10, 2,), np.float32)
        #top    --> output
        #bottom --> should be empty
        if len(bottom) > 0:
            raise ValueError("No input data required.")

        top[0], top[1] = self.get_next_image(top)

