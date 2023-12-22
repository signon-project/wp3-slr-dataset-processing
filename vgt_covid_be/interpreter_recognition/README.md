# Interpreter recognition

This directory contains the code used for the training and application of the interpreter classifier.

The classifier is an ImageNet-pretrained ResNet18 Convolutional Neural Network.
After training, it achieves the following scores on relevant metrics:

| Metric    | Training set | Validation set | Test set |
|-----------|--------------|----------------|----------|
| Accuracy  | 0.9674       | 0.9945         | 0.9938   |
| Recall    | 0.9681       | 0.9940         | 0.9965   |
| Precision | 0.9721       | 0.9958         | 0.9920   |
| F1        | 0.9701       | 0.9949         | 0.9942   |

## Dependencies

- Python 3.8
- PyTorch 1.8
- OpenCV

## Useful scripts

- `train.py`: Train the classifier
- `apply.py`: Apply the classifier to a single video
- `apply_batched.py`: Apply the classifier in a batched manner for when you have access to a GPU
- `get_metadata.py`: Get metadata about a video, automatically extracting FPS and allowing a human to indicate the location of the interpreter spatial bounding box
- `run_*.py`: Run the specific scripts on entire directories

## Useful links

A pre-trained checkpoint of the classifier is available [here](https://cloud.ilabt.imec.be/index.php/s/xdPMKzqNjHxQTJd). It supports only interpreters 1 and 2 at this time.
