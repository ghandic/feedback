feedback
--------

Small python module which compiles all feedback received into a single static HTML file.

#### Requirements
- Python 3.6+
- Installation of all packages in requirements.txt
- All feedback and (optionally) images follows the API

#### How set up environment
```bash
pip install -r requirements.txt
```

#### How to use
```bash
python3 generate.py -i <image dir> -f <feedback dir>
```

This will generate a file called `index.html` similar to the example below:

![Example output](example_output.png)
