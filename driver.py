import configparser
from copy import deepcopy
from datetime import date
import random, os, traceback, glob, time, sys
from shutil import copy2
os.add_dll_directory(os.getcwd())
config = configparser.ConfigParser()
configfile = "default.ini"
runtests = False
testKW = "test"
if len(sys.argv) > 1:
    if sys.argv[1] == testKW:
        runtests = True
        if len(sys.argv) > 2:
            configfile = sys.argv[2]
    else:
        configfile = sys.argv[1]
if os.path.isfile(configfile):
    config.read(configfile)
else:
    raise Exception("Config file %s was not found" % configfile)

import builtins
builtins.iklib_pl_console = config["MCDriver"].get("PrintLevelConsole")
builtins.iklib_pl_file = config["MCDriver"].get("PrintLevelFile")
builtins.iklib_logfilename = config["MCDriver"].get("LogFile")

from iklib import IK_Molecule
from iklib.Helpers import createLogger, log_versions, cause

logger = createLogger("MainScript")

try:
    if runtests:
        logger.info("Running tests of the build")
        runid = random.randint(1,10000)
        loglines = []
        log_versions(logger)
        for molfile in glob.glob(config["Testing"].get("TestMolecules")):
            goodtimes = []
            badtimes = []
            inittimes = []
            logger.warning("Starting CS for %s" % molfile)
            for count in range(1):
                start = time.perf_counter()
                mol = IK_Molecule(molfile, config)
                mol.prepare_ik()
                stop = time.perf_counter()
                inittimes.append(stop-start)
            start_total = time.perf_counter()
            while len(goodtimes) < config["Testing"].getint("NumberOfConfs"):
                ps = mol.getPS()
                ps.success = False
                mol.discr_cp = -1
                it = 0
                logger.warning("Generating the initial conformation")
                start = time.perf_counter()
                while it < config["MCDriver"].getint("MaxTries") and not ps.success:
                    for item in ps:
                        if item.isContinuous():
                            item.setValue(random.uniform(-3.141592, 3.141592))
                        if item.isDiscrete():
                            item.setValue(None)
                    ps = mol.applyPS()
                    it += 1
                stop = time.perf_counter()
                newtime = stop - start
                if ps.success:
                    goodtimes.append(newtime)
                else:
                    badtimes.append(newtime)
                    logger.info("Couldn't generate the initial conformation. Trying again.")
                    continue
                backup_ps = deepcopy(mol.getPS())
                mol.startDiscreteRun()
                mol.ccounter.backup_ddof()
                trycount = 0
                prev = ""
                logger.warning("Starting bruteforce of DDOF combinations")
                while not mol.done_all_discr() and len(goodtimes) < 5:
                    logger.warning("New DDOF combination")
                    start = time.perf_counter()
                    check = mol.ccounter.logstate(nocount=True)
                    ps = mol.applyPS(increase_discrete=True)
                    mol.ccounter.checkState()
                    if prev == check:
                        raise Exception("DDOF state repetition!!!")
                    prev = check
                    trycount += 1
                    it = 0
                    # TODO Auto-adaptation of MaxTries working for both small and big molecules
                    while it != config["MCDriver"].getint("MaxTries") and not ps.success and \
                            ps.cause != cause.geomoverlap_ddof and ps.cause != cause.zerosolutions_ddof:
                        for item in ps:
                            if item.isContinuous():
                                logger.info("Setting random torsion on " + repr(item.atoms))
                                item.setValue(random.uniform(-3.141592, 3.141592))
                        ps = mol.applyPS()
                        it += 1
                        if not ps.success and ps.isEmpty():
                            break
                    stop = time.perf_counter()
                    newtime = stop - start
                    if ps.success:
                        goodtimes.append(newtime)
                    else:
                        badtimes.append(newtime)
                    ps = mol.getPS()
                    for i in range(len(ps)):
                        if ps[i].isContinuous():
                            if ps[i].value != backup_ps[i].value:
                                ps[i].setValue(backup_ps[i].value)
                    mol.ccounter.recordState()
                logger.warning("DDOF bruteforce is finished")
                logger.warning("Progress with molecule %d/%d" % (len(goodtimes), config["Testing"].getint("NumberOfConfs")))
            end_total = time.perf_counter()
            print("-" * 40)
            print("| Timings for %s" % molfile)
            print("|%34s : %f s" % (
                "Average time for initialization", sum(inittimes) / len(inittimes)))
            if len(goodtimes) > 0:
                print("|%34s : %d (average time: %f s)" % (
                    "Number of successful iterations", len(goodtimes), sum(goodtimes) / len(goodtimes)))
            else:
                print("|%34s : %d" % (
                    "Number of successful iterations", len(goodtimes)))
            if len(badtimes) > 0:
                print("|%34s : %d (average time: %f s)" % (
                    "Number of unsuccessful iterations", len(badtimes), sum(badtimes)/len(badtimes)))
            else:
                print("|%34s : %d" % (
                    "Number of unsuccessful iterations", len(badtimes)))
            print("-" * 40)

            avergood = -1
            averbad = -1
            avertotal = (end_total-start_total)/len(goodtimes)
            if len(badtimes) > 0:
                averbad = sum(badtimes) / len(badtimes)
            if len(goodtimes) > 0:
                avergood = sum(goodtimes) / len(goodtimes)

            loglines.append("%d,%s,%f,%d,%d,%f,%f,%f\n" % (runid, molfile,
                                                           sum(inittimes) / len(inittimes),
                                                           len(goodtimes), len(badtimes),
                                                           avergood,
                                                           averbad,avertotal))
        logfile = open("timings.csv", "a")
        for line in loglines:
            logfile.write(line)
        logfile.close()
    else:
        molfile = config["MCDriver"].get("InputFile")
        if not os.path.isfile(molfile):
            raise Exception("Input file \"%s\" is not found" % molfile)
        def writeGeom():
            if ".mol" in config["MCDriver"].get("OutputFile"):
                mol.writeToMol(config["MCDriver"].get("OutputFile").replace("%d", str(conf_count)))
                logger.warning("Writing file " + config["MCDriver"].get("OutputFile").replace("%d", str(conf_count)))
            elif ".xyz" in config["MCDriver"].get("OutputFile"):
                mol.writeToXyz(config["MCDriver"].get("OutputFile").replace("%d", str(conf_count)))
                logger.warning("Writing file " + config["MCDriver"].get("OutputFile").replace("%d", str(conf_count)))
            logger.info("Conformer was generated successfully.")
        
        log_versions(logger)
        logger.info("Initializing from file \"%s\"" % molfile)
        mol = IK_Molecule(molfile, config)
        mol.prepare_ik()
        conf_count = 0
        while conf_count < config["MCDriver"].getint("NumberOfConfs"):
            logger.warning("Generated %d conformations. Goal = %d" % (conf_count,
                                                                      config["MCDriver"].getint("NumberOfConfs")))
            ps = mol.getPS()
            ps.success = False
            mol.discr_cp = -1
            it = 0
            logger.warning("Generating the initial conformation")
            while it != config["MCDriver"].getint("MaxTries") and not ps.success:
                for item in ps:
                    if item.isContinuous():
                        item.setValue(random.uniform(-3.141592, 3.141592))
                    if item.isDiscrete():
                        item.setValue(None)
                ps = mol.applyPS()
                it += 1
                if ps.success:
                    writeGeom()
                    conf_count += 1
                    break
                elif ps.isEmpty():
                    it = config["MCDriver"].getint("MaxTries")
                    break
            if it == config["MCDriver"].getint("MaxTries"):
                logger.warning("Couldn't generate the initial conformation. Trying again.")
                continue
            backup_ps = deepcopy(mol.getPS())
            mol.startDiscreteRun()
            trycount = 0
            prev = ""
            logger.warning("Starting bruteforce of DDOF combinations")
            while not mol.done_all_discr():
                logger.warning("New DDOF combination")
                check = mol.ccounter.logstate(nocount=True)
                ps = mol.applyPS(increase_discrete = True)
                mol.ccounter.checkState()
                if prev == check:
                    raise Exception("DDOF state repetition!!!")
                prev = check
                trycount += 1
                it = 0
                while it != config["MCDriver"].getint("MaxTries") and not ps.success and \
                        ps.cause != cause.geomoverlap_ddof and ps.cause != cause.zerosolutions_ddof:
                    for item in ps:
                        if item.isContinuous():
                            logger.info("Setting random torsion on "+repr(item.atoms))
                            item.setValue(random.uniform(-3.141592, 3.141592))
                    ps = mol.applyPS()
                    it += 1
                    if not ps.success and ps.isEmpty():
                        break
                if ps.success:
                    writeGeom()
                    conf_count += 1
                ps = mol.getPS()
                for i in range(len(ps)):
                    if ps[i].isContinuous():
                        if ps[i].value != backup_ps[i].value:
                            ps[i].setValue(backup_ps[i].value)
                mol.ccounter.recordState()
            logger.warning("DDOF bruteforce is finished")
        logger.warning("Normal termination. Generated totally %d conformations." % (conf_count))
except Exception:
    if Exception != KeyboardInterrupt:
        logger.error("Exception. Stack trace:\n" + traceback.format_exc())
        logger.error("Creating bug report.")
        i = 0
        while os.path.isdir("bugreport_%s_%d" % (str(date.today()), i)):
            i += 1
        bug_dir = "bugreport_%s_%d" % (str(date.today()), i)
        os.mkdir(bug_dir)
        try:
            copy2(__file__, bug_dir + "/driver.py")
            copy2(molfile, bug_dir + "/starting_geom.mol")
            copy2(config["MCDriver"].get("LogFile"), bug_dir + "/logfile")
        except:
            pass

        # Write values of all the DOFs
        torfile = open(bug_dir + "/parameters_continuous.csv", "w")
        ps = mol.getPS()
        torlines = ["atom1,atom2,side1,side2,value"]
        for param in ps:
            try:
                if param.isContinuous():
                    torlines.append("%d,%d,%d,%d,%f" % (param.atoms[0], param.atoms[1],
                                                        param.sides[0], param.sides[1],
                                                        param.value))
            except:
                torlines.append("Error accessing parameter attributes")
        torfile.close()
finally:
    if config["MCDriver"].getboolean("AutoCleanup") and os.path.isfile(config["MCDriver"].get("LogFile")):
        os.remove(config["MCDriver"].get("LogFile"))