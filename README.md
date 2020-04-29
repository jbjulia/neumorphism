# Neumorpishm

The next Soft UI trend, done Pythonically. 

![Alt text](/images/Comparison.png)  

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install Neumorpishm.

```bash
$ pip install -r requirements.txt
```

## Usage

```python
setGraphicsEffect(neumorphism.NeumorphismEffect())
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## Project Status

This code was compiled from a range of sources in an attempt to mirror the trending CSS design, currently unsupported by QWidgets. For now, the solution is to create a custom subclass of QGraphicsEffect and use gradients. At this time, only rectangular borders are supported.
