#  ================================================================
#  Created by Gregory Kramida on 8/9/16.
#  Copyright (c) 2016 Gregory Kramida
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#  ================================================================
from enum import Enum
from ext_argparse.argument import Argument


class Arguments(Enum):
    # ================= WORK FOLDER, INPUT & OUTPUT FILES =============================================================#
    folder = Argument(default="/media/algomorph/Data/AMBR_data/ml/", arg_type=str,
                      arg_help="Path to root folder to work in.",
                      setting_file_location=True)
    data_subfolder = Argument(default="cap04", arg_type=str,
                              arg_help="Relative path from the root folder to location of feature and label files.")
    model_file = Argument(default="lstm_model.npz",
                          arg_help="Relative path from the root folder to the file where the trained lstm" +
                                   " model will be saved to and/or loaded from.")
    hidden_unit_count = Argument(default=128, arg_type=int, action='store',
                                 arg_help="Embedding layer size and LSTM number of hidden units.")
    patience = Argument(default=15, arg_type=int,
                        arg_help="Number of epochs to wait before early stop if there is no training progress.")
    max_epochs = Argument(default=300, arg_type=int, arg_help="Maximum number of epochs to run.")

    report_interval = Argument(default=50, arg_type=int,
                               arg_help="Interval (in updates) between re-printing progress to stdout.")
    decay_constant = Argument(default=0., arg_type=float,
                              arg_help="Weight decay for the classifier applied to the U weights.")
    learning_rate = Argument(default=0.0001, arg_type=float,
                             arg_help="Learning rate for sgd (not used for adadelta and rmsprop)")
    # TODO: feature count should be inferred from the input file
    feature_count = Argument(default=4096, arg_type=int, arg_help="Input feature count.")
    optimizer = Argument(default="adadelta", arg_type=str,
                         arg_help="sgd, adadelta and rmsprop available. Sgd very hard to use, not recommended " +
                                  "(probably need momentum and decaying learning rate).")
    validation_interval = Argument(default=20, arg_type=int,
                                   arg_help="Interval (in updates) between re-validating to prevent overfitting.")
    save_interval = Argument(default=20, arg_type=int,
                             arg_help="Interval (in updates) between re-saving trained parameters.")
    batch_size = Argument(default=10, arg_type=int, arg_help="Batch size to use for training.")
    validation_batch_size = Argument(default=5, arg_type=int, arg_help="Batch size to use for validation/testing.")
    noise_std = Argument(default=0., arg_type=float,
                         arg_help="(TODO) amount of artificial noise to introduce to prevent overfitting.")
    use_dropout = Argument(default=False, arg_type='bool_flag', action='store_true',
                           arg_help="If False, training is slightly faster, " +
                                    "but the model yields a worse test error. " +
                                    "\nReference: Srivastava, Nitish, Geoffrey E. Hinton, Alex Krizhevsky, " +
                                    "Ilya Sutskever, and Ruslan Salakhutdinov.\n    Dropout: a simple way to " +
                                    "prevent neural networks from overfitting. Journal of Machine Learning " +
                                    "Research 15, no. 1\n(2014): 1929-1958.")
    weighted = Argument(default=False, arg_type='bool_flag', action='store_true',
                        arg_help="Whether or not to weigh update cost using the inverse combined sequence" +
                                 "count ratio of each category to the total sample count.")
    overwrite_model = Argument(default=False, arg_type='bool_flag', action='store_true',
                               arg_help="Whether or not to overwrite the model at the model file location.")
    random_seed = Argument(default=19350108, arg_type=int,
                           arg_help="Random seed to use for shuffling sample sequences and initializing weights." +
                           "By default set to Elvis Presley's birthday in sortable date format.")
    datasets = Argument(default=["al0"], nargs='+', arg_help="Datasets to process.")
    multiview_labels = Argument(default=None, arg_type=str,
                                arg_help="In case the datasets are coming from multiple views on the same " +
                                         "subject, this argument should specify the name of the multiview label file" +
                                         " residing in the work folder.")
    validation_ratio = Argument(default=0.2, arg_type=float, arg_help="Ratio of the data to use for validation.")
    test_ratio = Argument(default=0.2, arg_type=float, arg_help="Ratio of the data to use for testing.")
    test_entire_data = Argument(default=False, arg_type='bool_flag', action='store_true',
                                arg_help="Whether or not to test on whole dataset.")
