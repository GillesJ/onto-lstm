from __future__ import absolute_import
from keras import backend as K

from keras import activations, initializations, regularizers, constraints
from keras.layers.core import Layer, MaskedLayer

from keras.constraints import unitnorm


class HigherOrderEmbedding(Layer):
    '''Turn positive integer vectors (index vectors) into dense matrices of fixed size.
    Extenstion of Embedding layer in Keras to 3D.
    eg. [[[4, 5]], [[20, 4]]] -> [[[0.25, 0.1], [-0.62, 0.9]], [[0.6, -0.2], [0.25, 0.1]]]

    This layer can only be used as the first layer in a model.

    # Input shape
        3D tensor with shape: `(nb_samples, sequence_length1, sequence_length2)`.

    # Output shape
        4D tensor with shape: `(nb_samples, sequence_length1, sequence_length2, output_dim)`.

    '''
    input_ndim = 3

    def __init__(self, input_dim, output_dim,
                 init='uniform', input_length1=None, input_length2=None,
                 W_regularizer=None, activity_regularizer=None,
                 W_constraint=None,
                 mask_zero=False,
                 weights=None, **kwargs):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.init = initializations.get(init)
        self.input_length1 = input_length1
        self.input_length2 = input_length2
        self.mask_zero = mask_zero

        self.W_constraint = constraints.get(W_constraint)
        self.constraints = [self.W_constraint]

        self.W_regularizer = regularizers.get(W_regularizer)
        self.activity_regularizer = regularizers.get(activity_regularizer)

        self.initial_weights = weights
        kwargs['input_shape'] = (self.input_length2, self.input_dim)
        super(HigherOrderEmbedding, self).__init__(**kwargs)

    def build(self):
        self.input = K.placeholder(shape=(self.input_shape[0], self.input_length1, self.input_length2),
                                   dtype='int32')
        self.W = self.init((self.input_dim, self.output_dim))
        self.trainable_weights = [self.W]
        self.regularizers = []
        if self.W_regularizer:
            self.W_regularizer.set_param(self.W)
            self.regularizers.append(self.W_regularizer)

        if self.activity_regularizer:
            self.activity_regularizer.set_layer(self)
            self.regularizers.append(self.activity_regularizer)

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)

    def get_output_mask(self, train=None):
        X = self.get_input(train)
        if not self.mask_zero:
            return None
        else:
            return K.not_equal(X, 0)

    @property
    def output_shape(self):
        return (self.input_shape[0], self.input_length1, self.input_length2, self.output_dim)

    def get_output(self, train=False):
        X = self.get_input(train)
        X_ind = K.cast(X, 'int32')
        out = K.gather(self.W, X_ind)
        return out

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "input_dim": self.input_dim,
                  "output_dim": self.output_dim,
                  "init": self.init.__name__,
                  "input_length1": self.input_length1,
                  "input_length2": self.input_length2,
                  "mask_zero": self.mask_zero,
                  "activity_regularizer": self.activity_regularizer.get_config() if self.activity_regularizer else None,
                  "W_regularizer": self.W_regularizer.get_config() if self.W_regularizer else None,
                  "W_constraint": self.W_constraint.get_config() if self.W_constraint else None}
        base_config = super(HigherOrderEmbedding, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))