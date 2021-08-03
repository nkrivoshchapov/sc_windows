# Build of SC algorithm for Windows

## Clone

```
git clone git@github.com:nkrivoshchapov/sc_windows.git
cd sc_windows
git submodule update --init --recursive --remote
git submodule foreach git pull origin master
git submodule foreach git checkout master
```

## TLC build

1. Install MinGW, make sure `gcc`, `g++` and `gfortran` are in `$PATH`.

2. Setup the minimal installation of Python3 with pip. Using pip install scipy, numpy, networkx and pyinstaller. Fix the path to python and pyinstaller in 13th line of `build.cmd`.

3. Open CMD and change directory to `sc_windows`.

4. Execute

```
build.cmd
```


## Testing

```
cd win_build
driver.exe test
```

## Use


To run generation of conformers:
 
```
driver.exe <name of config file>
```

To run tests:

```
driver.exe test <name of config file>
```

`default.ini` is the name of config file by default.
