from torch.utils.tensorboard import SummaryWriter


class Logger(object):
    def __init__(self, log_dir):
        self.writer = SummaryWriter(log_dir=log_dir)

    def log(self, categories, value, step, max_steps=None, do_print=False):
        """
        Log a value.

        :param categories: A list of strings indicating the nested categories to which this value belongs.
        :param value: The value (a number).
        :param step: The current step, be it an epoch, minibatch index... as long as you are consistent between categories.
        :param max_steps: The maximum number of steps (e.g., number of minibatches in an epoch or number of epochs). Only used for printing to stdout.
        :param do_print: Whether to also print to stdout.
        """
        self.writer.add_scalar('/'.join(categories), value, step)
        if do_print:
            assert max_steps is not None
            print('{} [{}/{}]: {}'.format('/'.join(categories), step % max_steps, max_steps, value))
