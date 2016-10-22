# pyOculus
Python set up for Oculus allsky camera on Raspberry Pi. The code is currently running on an Starlight Xpress Oculus installed in the [Observatorio Astronómico de Javalambre](http://oajweb.cefca.es), in Teruel (Spain).
This project is a fork of [https://github.com/zemogle/pyOculus](https://github.com/zemogle/pyOculus) Many thanks! [Dark Matter Sheep](http://darkmattersheep.uk/blog/).

## Setup (Pending changes)
- A Raspberry Pi
- Need to install [INDI server](http://indilib.org/download/category/6-raspberry-pi.html) for Raspberry Pi.
- Install Swig via `sudo apt-get install swig` you may need to do `sudo apt-get install -f` to get the dependencies
- You may need to install `cmake` with `sudo apt-get install cmake` before the next step
- You may also need to install python dev using `sudo apt-get install python-dev`
- Install the [PyINDI client](https://github.com/zemogle/pyindi-client) by doing
```bash
git clone https://github.com/zemogle/pyindi-client
mkdir libindipython
cd libindipython
```

You will probably also need to replace the file `cmake_modules/findINDI.cmake` with the one from [this INDI issue](https://sourceforge.net/p/pyindi-client/tickets/2/).

```bash
cmake -D PYTHON_LIBRARY=/usr/lib/arm-linux-gnueabihf/libpython2.7.so -D PYTHON_INCLUDE_DIR=/usr/include/python2.7/ ../pyindi-client/swig-indi/swig-indi-python
make
sudo make install
```

You should already have `python` and `git` if you are using Raspbian.

## Instructions (Pending changes)
The INDI server handles all the communication with the camera, so the server has to be running for this code to be able to talk to the camera. In my case Oculus uses a Starlight Xpress CCD, so I started the camera with:

`indiserver -v -m 100 indi_sx_ccd`

This needs to be running when you do the next step, so open a new terminal (or if you are running headless, open another ssh session).

`python snapper.py`

will save a file called `latest.fits` after taking an image.

## Testing Setup (Pending changes)

If you are in doubt of whether the camera is connected and working, you can run the following test script (assuming the INDi server is running):

`python pyindi-client/swig-indi/swig-indi-python/test-indiclient.py`
