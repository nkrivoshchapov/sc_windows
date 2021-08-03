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

2. Open CMD

3. Execute

```
build.cmd
```


## Testing

```
cd win_build
driver.exe test
```

## Use


To run generator of conformers:
 
```
driver.exe <name of config file>
```

To run tests:

```
driver.exe test <name of config file>
```

`default.ini` is the name of config file by default.
