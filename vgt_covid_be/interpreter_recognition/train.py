import argparse
import os
import random

import numpy as np
import torch
from torch.utils.data import DataLoader
from torchvision.transforms import transforms
import sklearn.metrics as metrics

from data import Dataset
from log import Logger
from model import Classifier


def main(args):
    _set_seeds(args.seed)

    logger = Logger(args.log_dir)

    train_loader, val_loader, test_loader = _get_data_loaders(args)

    model = Classifier()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'max', patience=10)
    criterion = torch.nn.BCELoss()

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    model = model.to(device)

    epoch = 0
    last_val_accuracy = 0
    while epoch < args.max_epochs:
        # Train.
        model.train()
        scheduler.step(last_val_accuracy)

        for param_group in optimizer.param_groups:
            logger.log(['lr'], param_group['lr'], epoch)
            break

        train_loss, train_accuracy, train_precision, train_recall, train_f1 = _epoch(train_loader, device, optimizer, model, criterion)

        logger.log(['train', 'epoch_loss'], train_loss, epoch, max_steps=args.max_epochs, do_print=True)
        logger.log(['train', 'epoch_acc'], train_accuracy, epoch, max_steps=args.max_epochs, do_print=True)
        logger.log(['train', 'epoch_precision'], train_precision, epoch, max_steps=args.max_epochs, do_print=True)
        logger.log(['train', 'epoch_recall'], train_recall, epoch, max_steps=args.max_epochs, do_print=True)
        logger.log(['train', 'epoch_f1'], train_f1, epoch, max_steps=args.max_epochs, do_print=True)

        # Validate.
        model.eval()
        with torch.no_grad():
            val_loss, last_val_accuracy, val_precision, val_recall, val_f1 = _epoch(val_loader, device, None, model, criterion)

        logger.log(['val', 'epoch_loss'], val_loss, epoch, max_steps=args.max_epochs, do_print=True)
        logger.log(['val', 'epoch_acc'], last_val_accuracy, epoch, max_steps=args.max_epochs, do_print=True)
        logger.log(['val', 'epoch_precision'], val_precision, epoch, max_steps=args.max_epochs, do_print=True)
        logger.log(['val', 'epoch_recall'], val_recall, epoch, max_steps=args.max_epochs, do_print=True)
        logger.log(['val', 'epoch_f1'], val_f1, epoch, max_steps=args.max_epochs, do_print=True)

        epoch += 1

    # Evaluate on test set.
    with torch.no_grad():
        test_loss, test_accuracy, test_precision, test_recall, test_f1 = _epoch(test_loader, device, None, model, criterion)

    logger.log(['test', 'loss'], test_loss, epoch, max_steps=args.max_epochs, do_print=True)
    logger.log(['test', 'acc'], test_accuracy, epoch, max_steps=args.max_epochs, do_print=True)
    logger.log(['test', 'precision'], test_precision, epoch, max_steps=args.max_epochs, do_print=True)
    logger.log(['test', 'recall'], test_recall, epoch, max_steps=args.max_epochs, do_print=True)
    logger.log(['test', 'f1'], test_f1, epoch, max_steps=args.max_epochs, do_print=True)

    # Save checkpoint.
    torch.save(model.state_dict(), os.path.join(args.log_dir, f'checkpoint_{int(test_accuracy * 100)}.pth'))


def _epoch(data_loader, device, optimizer, model, criterion):
    total_loss = 0
    y_true, y_pred = [], []
    total_iterations = len(data_loader)
    for i, (features, targets) in enumerate(data_loader):
        features = features.to(device)
        targets = targets.to(device)

        if optimizer is not None:
            optimizer.zero_grad()

        outputs = model(features)
        loss = criterion(outputs, targets)

        predictions = outputs > 0.5
        for j in range(predictions.shape[0]):
            y_true.append(int(targets[j].item()))
            y_pred.append(int(predictions[j].item()))

        if optimizer is not None:
            loss.backward()
            optimizer.step()

        total_loss += loss.item()

    total_loss /= total_iterations
    total_accuracy = metrics.accuracy_score(y_true, y_pred)
    f1 = metrics.f1_score(y_true, y_pred)
    precision = metrics.precision_score(y_true, y_pred)
    recall = metrics.recall_score(y_true, y_pred)

    return total_loss, total_accuracy, precision, recall, f1


def _get_data_loaders(args):
    train_transforms = transforms.Compose([
        transforms.Resize(256),
        transforms.RandomResizedCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    eval_transforms = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    train_dataset = Dataset(args.data_dir, train_transforms, 'train')
    val_dataset = Dataset(args.data_dir, eval_transforms, 'validate')
    test_dataset = Dataset(args.data_dir, eval_transforms, 'test')
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=4, pin_memory=True,
                              drop_last=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=4, pin_memory=True,
                            drop_last=True)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, num_workers=4, pin_memory=True,
                             drop_last=True)
    return train_loader, val_loader, test_loader


def _set_seeds(seed):
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-s', '--seed', help='Random seed.', type=int, default=42)
    parser.add_argument('-b', '--batch-size', help='Batch size.', type=int, default=256)
    parser.add_argument('-e', '--max-epochs', help='Maximum training epochs.', type=int, default=500)
    parser.add_argument('-d', '--data-dir', help='Directory where clips reside.', type=str, required=True)
    parser.add_argument('-l', '--log-dir', help='Directory where to write logs to.', type=str, required=True)

    args = parser.parse_args()

    main(args)
