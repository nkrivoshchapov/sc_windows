@ECHO OFF
TITLE Build TLC library

cp simple_condensation/tlc_src/* .
gcc -c -o sturm.o sturm.c -fPIC -static -lgfortran
g++ -c -o main.o main.cpp -fPIC -static -lgfortran
gfortran -c -o tripep_closure.o tripep_closure.f90 -fPIC -static -lgfortran
gfortran -c -o main_pep.o main_pep.f90 -fPIC -static -lgfortran
g++ -o libtlc.dll sturm.o main.o main_pep.o tripep_closure.o -shared -static -fPIC -lgfortran -lquadmath

cp -r simple_condensation/iklib .
python patch_iklib.py
python38 "C:\Program Files\Python38\Lib\site-packages\PyInstaller\__main__.py" --onefile --icon=app.ico driver.py
mkdir win_build
mv dist/driver.exe win_build
mv libtlc.dll win_build
cp default.ini win_build
