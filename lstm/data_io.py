import os
import json

import numpy as np
from numpy import inf
import theano


def prepare_data(batch_features, batch_labels, maximum_sequence_length=None):
    """Create a matrix from multiple sequences.
    This pads/cuts each sequence to the same length, which is the length of the longest sequence or
    maximum_sequence_length. Note: the the axes are swapped!
    """
    # x: a list of sentences
    lengths = [s.shape[0] for s in batch_features]
    feat_dim = batch_features[0].shape[1]

    if maximum_sequence_length is not None:
        new_seqs = []
        new_labels = []
        new_lengths = []
        for l, s, y in zip(lengths, batch_features, batch_labels):
            if l < maximum_sequence_length:
                new_seqs.append(s)
                new_labels.append(y)
                new_lengths.append(l)
        lengths = new_lengths
        batch_labels = new_labels
        batch_features = new_seqs

        if len(lengths) < 1:
            return None, None, None

    n_samples = len(batch_features)
    maximum_sequence_length = np.max(lengths)

    x = np.zeros((maximum_sequence_length, n_samples, feat_dim)).astype(theano.config.floatX)
    x_mask = np.zeros((maximum_sequence_length, n_samples)).astype(theano.config.floatX)
    for idx, s in enumerate(batch_features):
        x[:lengths[idx], idx, :] = s
        x_mask[:lengths[idx], idx] = 1.

    return x, x_mask, batch_labels


class SequenceDataset(object):
    """
    Represents a set of sequences, where each sequence time step is represented by a vector of features.
    Each sequences has a label associated with it.
    Meta information is just the way the sequence was represented in the file.
    """

    def __init__(self, sequence_features, sequence_labels, meta_information, weights=None):
        self.features = sequence_features
        self.labels = sequence_labels
        self.meta_information = meta_information
        if len(self.features) != len(self.labels) or len(self.features) != len(self.meta_information):
            raise ValueError("Expecting same numbers of features, labels, and meta data. " +
                             "Got: {:d}, {:d}, and {:d}, respectively."
                             .format(len(self.features), len(self.labels), len(self.meta_information)))
        self.weights = weights
        if weights is not None:
            if len(self.features) != len(weights):
                raise ValueError("Expecting the same number of weights as the number of samples. " +
                                 "Got {:d} and {:d}, respectively.".format(len(self.weights), len(self.features)))

    def __len__(self):
        return len(self.features)


def compute_train_set_weights(n_categories, train_set_y):
    # compute weights
    sample_counts_per_label = np.zeros(n_categories, np.int32)
    for label in train_set_y:
        sample_counts_per_label[label] += 1

    weights_by_label = len(train_set_y) / (np.count_nonzero(sample_counts_per_label) * sample_counts_per_label)
    weights_by_label[weights_by_label == inf] = 0
    train_set_weights = [weights_by_label[y] for y in train_set_y]
    return train_set_weights


def helper_load_datasets(datasets, base_work_folder):
    features_by_sample = []
    labels_by_sample = []
    meta_by_sample = []

    for dataset in datasets:
        base_data_path = os.path.join(base_work_folder, 'data')
        dataset_path = os.path.join(base_data_path, '{:s}_labels.json'.format(dataset))
        print('  loading labels from: %s' % (dataset_path,))
        with open(dataset_path, 'r') as f:
            label_entries = json.load(f)

        print('  dataset length: ', len(label_entries))

        # load the image features into memory
        features_path = os.path.join(base_data_path, "{:s}_features.npz".format(dataset))
        print('  loading features from: %s' % (features_path,))
        archive = np.load(features_path)
        all_features = archive["features"]

        for entry in label_entries:
            sample_features = all_features[entry['start']:entry['end'] + 1, :]
            if len(sample_features) == 0:
                raise ValueError("Got input sequence length 0: {:s}".format(str(entry)))

            sample_label = entry['label']

            features_by_sample.append(sample_features)
            labels_by_sample.append(sample_label)
            entry['source'] = dataset
            meta_by_sample.append(entry)

    features_by_sample = np.array(features_by_sample)
    labels_by_sample = np.array(labels_by_sample)

    unique_labels = np.unique(labels_by_sample)
    n_categories = len(unique_labels)
    return features_by_sample, labels_by_sample, meta_by_sample, n_categories


def get_label_distribution(label_set, n_categories):
    counts = np.zeros(n_categories, dtype=np.float64)
    for label in label_set:
        counts[label] += 1
    return counts / len(label_set)


def load_test_data(datasets, base_work_folder):
    features_by_sample, labels_by_sample, meta_by_sample, n_categories = \
        helper_load_datasets(datasets, base_work_folder)
    n_features = len(features_by_sample[0][0])
    return SequenceDataset(features_by_sample, labels_by_sample, meta_by_sample), n_categories, n_features


def load_data(datasets, base_work_folder, validation_ratio=0.2, test_ratio=0.2, randomization_seed=None):
    """Loads the dataset
    :type datasets: list[str]
    :param datasets: names of the datasets
    :type base_work_folder: str
    :param base_work_folder: The folder containing all datasets
    :type validation_ratio: float
    :param validation_ratio: The fraction of the full train set used for the validation set.
    :type test_ratio: float
    :param test_ratio: The fraction of the full train set used for the test set.
    :rtype: (lstm.data_io.SequenceDataset, lstm.data_io.SequenceDataset, lstm.data_io.SequenceDataset, int, int)
    :return training, validation, and testing dataset, the category and the feature counts
    """

    features_by_sample, labels_by_sample, meta_by_sample, n_categories = \
        helper_load_datasets(datasets, base_work_folder)
    print("Overall label distribution: {:s}".format(str(get_label_distribution(labels_by_sample, n_categories))))

    # split features into test, training, and validation set
    n_samples = len(features_by_sample)
    if randomization_seed is not None:
        np.random.seed(randomization_seed)
    randomized_index = np.random.permutation(n_samples)
    train_ratio = 1.0 - test_ratio - validation_ratio
    test_count = int(np.round(n_samples * test_ratio))
    train_count = int(np.round(n_samples * train_ratio))
    start_train = test_count
    end_train = test_count + train_count
    start_valid = end_train

    train_set_x = [features_by_sample[s] for s in randomized_index[start_train:end_train]]
    train_set_y = [labels_by_sample[s] for s in randomized_index[start_train:end_train]]
    train_set_meta = [meta_by_sample[s] for s in randomized_index[start_train:end_train]]

    print("Training set label distribution: {:s}".format(str(get_label_distribution(train_set_y, n_categories))))

    train_set_weights = compute_train_set_weights(n_categories, train_set_y)

    test_set_x = [features_by_sample[s] for s in randomized_index[0:test_count]]
    test_set_y = [labels_by_sample[s] for s in randomized_index[0:test_count]]
    test_set_meta = [meta_by_sample[s] for s in randomized_index[0:test_count]]

    validation_set_x = [features_by_sample[s] for s in randomized_index[start_valid:]]
    validation_set_y = [labels_by_sample[s] for s in randomized_index[start_valid:]]
    validation_set_meta = [meta_by_sample[s] for s in randomized_index[start_valid:]]

    print("Validation set label distribution: {:s}".format(str(get_label_distribution(validation_set_y, n_categories))))
    print("Test set label distribution: {:s}".format(str(get_label_distribution(test_set_y, n_categories))))

    training_set = SequenceDataset(train_set_x, train_set_y, train_set_meta, train_set_weights)
    validation_set = SequenceDataset(validation_set_x, validation_set_y, validation_set_meta)
    test_set = SequenceDataset(test_set_x, test_set_y, test_set_meta)

    n_features = len(test_set_x[0][0])

    return training_set, validation_set, test_set, n_categories, n_features


class SequenceSet(object):
    def __init__(self, sequence_feature_set, sequence_meta_set, group_label):
        self.features = sequence_feature_set
        self.contributions = None
        if len(self.features) > 0:
            total_frame_count = 0
            sample_lengths = []
            for sample in sequence_feature_set:
                sl = len(sample)
                sample_lengths.append(sl)
                total_frame_count += sl
            self.contributions = np.array(sample_lengths, dtype=np.float64) / total_frame_count
        self.meta = sequence_meta_set
        self.label = group_label

    def empty(self):
        return len(self.features) == 0


def break_up_groups(groups, randomize=False):
    sample_features = []
    sample_labels = []
    sample_meta = []
    for group in groups:
        for sequence_set in group:
            for sequence_features, sequence_meta in zip(sequence_set.features, sequence_set.meta):
                sample_features.append(sequence_features)
                sample_labels.append(sequence_set.label)
                sample_meta.append(sequence_meta)
    if randomize:
        random_index = np.random.permutation(len(sample_features))
        sample_features = [sample_features[ix] for ix in random_index]
        sample_labels = [sample_labels[ix] for ix in random_index]
        sample_meta = [sample_meta[ix] for ix in random_index]
    return sample_features, sample_labels, sample_meta


def load_multiview_data_helper(datasets, base_work_folder, multiview_label_filename):
    base_data_path = os.path.join(base_work_folder, "data")
    multiview_labels_file = os.path.join(base_data_path, multiview_label_filename)
    multiview_label_entries = json.load(open(multiview_labels_file, 'r'))
    multiview_features = []
    # load features for each view
    for obj in datasets:
        features_path = os.path.join(base_data_path, "{:s}_features.npz".format(obj))
        print('  loading features from: %s' % (features_path,))
        archive = np.load(features_path)
        multiview_features.append(archive["features"])

    groups = []
    sample_count = 0

    for group_entry in multiview_label_entries:
        group = []
        group_label = None
        empty_count = 0
        for sequence_set, view_features, dataset in zip(group_entry, multiview_features, datasets):
            sequence_feature_set = []
            sequence_meta_set = []
            for sequence_entry in sequence_set:
                if sequence_entry['label'] is not None:
                    sequence_entry['source'] = dataset
                    remaining_features = view_features[sequence_entry['start']:sequence_entry['end'] + 1, :]
                    sequence_feature_set.append(remaining_features)
                    group_label = sequence_entry['label']
                    sequence_meta_set.append(sequence_entry)
                    sample_count += 1
                else:
                    empty_count += 1
            sequence_set = SequenceSet(sequence_feature_set, sequence_meta_set, group_label)
            group.append(sequence_set)
        for sequence_set in group:
            sequence_set.label = group_label
        if empty_count < len(datasets):
            groups.append(group)

    return groups, sample_count


def load_multiview_test_data(datasets, base_work_folder, multiview_label_filename):
    groups, sample_count = load_multiview_data_helper(datasets, base_work_folder, multiview_label_filename)
    test_set_x, test_set_y, test_set_meta = break_up_groups(groups, randomize=True)
    unique_labels = np.unique(test_set_y)
    n_categories = len(unique_labels)
    n_features = len(test_set_x[0][0])
    test_set = SequenceDataset(test_set_x, test_set_y, test_set_meta)
    return test_set, groups, n_categories, n_features


def load_multiview_data(datasets, base_work_folder, multiview_label_filename, validation_ratio=0.2, test_ratio=0.2,
                        randomization_seed=None):
    groups, sample_count = load_multiview_data_helper(datasets, base_work_folder, multiview_label_filename)

    n_groups = len(groups)
    print("Total number of groups: {:d}, total number of samples: {:d}".format(n_groups, sample_count))
    if randomization_seed is not None:
        np.random.seed(randomization_seed)
    randomized_index = np.random.permutation(n_groups)
    train_ratio = 1.0 - test_ratio - validation_ratio
    test_count = int(round(n_groups * test_ratio))
    train_count = int(round(n_groups * train_ratio))
    validation_count = n_groups - test_count - train_count

    train_and_validation_groups = [groups[ix] for ix in randomized_index[0:train_count + validation_count]]
    test_groups = [groups[ix] for ix in randomized_index[train_count + validation_count:]]

    # break up the train & validation groups into individual sequence samples

    test_set_x, test_set_y, test_set_meta = break_up_groups(test_groups, randomize=True)
    remaining_features, remaining_labels, remaining_meta = break_up_groups(train_and_validation_groups)

    train_ratio /= (train_ratio + validation_ratio)
    n_samples = len(remaining_features)
    randomized_index = np.random.permutation(n_samples)
    train_count = int(round(n_samples) * train_ratio)

    train_set_x = [remaining_features[s] for s in randomized_index[0:train_count]]
    train_set_y = [remaining_labels[s] for s in randomized_index[0:train_count]]
    train_set_meta = [remaining_meta[s] for s in randomized_index[0:train_count]]

    validation_set_x = [remaining_features[s] for s in randomized_index[train_count:]]
    validation_set_y = [remaining_labels[s] for s in randomized_index[train_count:]]
    validation_set_meta = [remaining_meta[s] for s in randomized_index[train_count:]]

    labels_by_sample = train_set_y + validation_set_y + test_set_y
    unique_labels = np.unique(labels_by_sample)

    n_categories = len(unique_labels)

    train_set_weights = compute_train_set_weights(n_categories, train_set_y)

    training_set = SequenceDataset(train_set_x, train_set_y, train_set_meta, train_set_weights)
    validation_set = SequenceDataset(validation_set_x, validation_set_y, validation_set_meta)
    test_set = SequenceDataset(test_set_x, test_set_y, test_set_meta)

    n_features = len(test_set_x[0][0])
    print("Training set label distribution: {:s}".format(str(get_label_distribution(train_set_y, n_categories))))
    print("Validation set label distribution: {:s}".format(str(get_label_distribution(validation_set_y, n_categories))))
    print("Test set label distribution: {:s}".format(str(get_label_distribution(test_set_y, n_categories))))

    return training_set, validation_set, test_set, test_groups, n_categories, n_features
