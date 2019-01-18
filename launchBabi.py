from src.RN import RelationNetwork
from src.nlp_utils import read_babi, vectorize_babi
from src.LSTM import LSTM
import torch
import argparse
import os
from itertools import chain
from src.utils import files_names_test, files_names_train, files_names_val, saving_path_models, names_models, load_models, split_train_validation
from src.train import train_single, final_test


parser = argparse.ArgumentParser()
parser.add_argument('--epochs', type=int, default=1, help='epochs to train. Each epoch process all the dataset in input.')
parser.add_argument('--hidden_dims_g', nargs='+', type=int, default=[256, 256, 256], help='layers of relation function g')
parser.add_argument('--output_dim_g', type=int, default=256, help='output dimension of relation function g')
parser.add_argument('--hidden_dims_f', nargs='+', type=int, default=[256, 512], help='layers of final network f')
parser.add_argument('--hidden_dim_lstm', type=int, default=32, help='units of LSTM')
parser.add_argument('--lstm_layers', type=int, default=1, help='layers of LSTM')

parser.add_argument('--emb_dim', type=int, default=50, help='word embedding dimension')
parser.add_argument('--only_relevant', action="store_true", help='read only relevant fact from babi dataset')


# [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
parser.add_argument('--babi_tasks', nargs='+', type=int, default=[1], help='which babi task to train and test')
parser.add_argument('--en_valid', action="store_true", help='Use en-valid-10k instead of en-10k folder of babi')

# optimizer parameters
parser.add_argument('--weight_decay', type=float, default=0, help='optimizer hyperparameter')
parser.add_argument('--learning_rate', type=float, default=2e-4, help='optimizer hyperparameter')

parser.add_argument('--cuda', action="store_true", help='use gpu')
parser.add_argument('--load', action="store_true", help=' load saved model (files must be named rn.pt and lstm.pt inside models/)')
parser.add_argument('--no_save', action="store_true", help='disable model saving')
parser.add_argument('--print_every', type=int, default=500, help='print information every print_every steps')
args = parser.parse_args()

mode = 'cpu'
if args.cuda:
    if torch.cuda.is_available():
        print('Using ', torch.cuda.device_count() ,' GPU(s)')
        mode = 'cuda'
    else:
        print("WARNING: No GPU found. Using CPUs...")
else:
    print('Using 0 GPUs')

batch_size_lstm = 1 # keep 1

device = torch.device(mode)

cd = os.path.dirname(os.path.abspath(__file__))
if args.en_valid:
    path_babi_base = cd + "/babi/en-valid-10k/"
else:
    path_babi_base = cd + "/babi/en-10k/"

print("Reading babi")

to_read_test = [files_names_test[i-1] for i in args.babi_tasks]
to_read_val = [files_names_val[i-1] for i in args.babi_tasks]
to_read_train = [files_names_train[i-1] for i in args.babi_tasks]

if not args.en_valid: # When reading from en-10k and not from en-valid-10k
    stories, dictionary, labels = read_babi(path_babi_base, to_read_train, args.babi_tasks, only_relevant=args.only_relevant)
    stories = vectorize_babi(stories, dictionary, device)
    train_stories, validation_stories = split_train_validation(stories, labels)
else:
    train_stories, dictionary, labels = read_babi(path_babi_base, to_read_train, args.babi_tasks, only_relevant=args.only_relevant)
    train_stories = vectorize_babi(train_stories, dictionary, device)
    validation_stories, _, _ = read_babi(path_babi_base, to_read_val, args.babi_tasks, only_relevant=args.only_relevant)
    validation_stories = vectorize_babi(validation_stories, dictionary, device)

test_stories, _, _ = read_babi(path_babi_base, to_read_test, args.babi_tasks, only_relevant=args.only_relevant)
test_stories = vectorize_babi(test_stories, dictionary, device)

dict_size = len(dictionary)
print("Dictionary size: ", dict_size)
print("Done reading babi!")

lstm = LSTM(args.hidden_dim_lstm, batch_size_lstm, dict_size, args.emb_dim, args.lstm_layers, device)

rn = RelationNetwork(args.hidden_dim_lstm, args.hidden_dims_g, args.output_dim_g, args.hidden_dims_f, dict_size,
                     device)

if args.load:
    load_models([(lstm, names_models[0]), (rn, names_models[1])], saving_path_models)

optimizer = torch.optim.Adam(chain(lstm.parameters(), rn.parameters()), args.learning_rate, weight_decay=args.weight_decay)

criterion = torch.nn.CrossEntropyLoss()

if args.epochs > 0:
    print("Start training")
    avg_train_losses, avg_train_accuracies, val_losses, val_accuracies = train_single(train_stories, validation_stories, args.epochs, lstm, rn, criterion, optimizer, args.print_every, args.no_save)
    print("End training!")

print("Testing...")
avg_test_loss, avg_test_accuracy = final_test(test_stories, lstm, rn, criterion)

print("Test accuracy: ", dict(avg_test_accuracy))
print("Test loss: ", dict(avg_test_loss))

if args.epochs > 0:
    import matplotlib

    if args.cuda:
        matplotlib.use('Agg')

    import matplotlib.pyplot as plt


    plt.figure()
    plt.plot(range(len(avg_train_losses)), avg_train_losses, 'b', label='train')
    plt.plot(range(len(val_losses)), val_losses, 'r', label='val')
    plt.legend(loc='best')

    if args.cuda:
        plt.savefig('loss.png')
    else:
        plt.show()

    plt.figure()
    plt.plot(range(len(avg_train_accuracies)), avg_train_accuracies, 'b', label='train')
    plt.plot(range(len(val_accuracies)), val_accuracies, 'r', label='val')
    plt.legend(loc='best')

    if args.cuda:
        plt.savefig('accuracy.png')
    else:
        plt.show()
