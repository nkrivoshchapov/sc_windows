import sys,os,glob

for file in glob.glob("iklib/*/*.py"):
    lines = open(file,"r").readlines()
    changed = False
    i = 0
    while i < len(lines):
        if "basedir = os.path.abspath(os.path.dirname(__file__))" in lines[i] or "TLC_libfile = os.path.join(basedir, 'libtlc.so')" in lines[i]:
            del lines[i]
        elif "TLC_dll = CDLL(TLC_libfile)" in lines[i]:
            lines[i] = lines[i].replace("TLC_dll = CDLL(TLC_libfile)", "TLC_dll = CDLL('libtlc.dll')")
            changed = True
            i += 1
        else:
            i += 1
    if changed:
        print(file + " was patched")
        wfile = open(file,"w")
        wfile.write("".join(lines))
        wfile.close()