import logging
import os
import shutil
import sys
import multiprocessing as mp

logger = logging.getLogger(__name__)


def diff_dir_layout_missing(dir1, dir2):
    for (dirpath, dirnames, filenames) in os.walk(dir1):
        for filename in filenames:
            relative_path = dirpath.replace(dir1, "")[1:]
            if not os.path.exists(os.path.join(dir2, relative_path, filename)):
                yield os.path.join(relative_path, filename)


def diff_dir_layout(dir1, dir2):
    diffplus = list(diff_dir_layout_missing(dir1, dir2))
    diffmin = list(diff_dir_layout_missing(dir2, dir1))
    return diffplus, diffmin


def cpfiles(src, dest, files):
    for f in files:
        logger.info(f"copy file {os.path.join(src, f)} -> {os.path.join(dest, f)}")
        dest_dir = os.path.dirname(os.path.join(dest, f))
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
        shutil.copy2(os.path.join(src, f), os.path.join(dest, f))


def rmfiles(dest, files):
    for f in files:
        logger.info(f"remove file {f}")
        os.remove(os.path.join(dest, f))


def rmemptydirs(path):
    if not os.path.isdir(path):
        return

    files = os.listdir(path)

    if len(files):
        for f in files:
            fullpath = os.path.join(path, f)
            if os.path.isdir(fullpath):
                rmemptydirs(fullpath)

    files = os.listdir(path)
    if len(files) == 0:
        logger.info(f"deleting folder {path}")
        os.rmdir(path)


def sync(src, dest):
    logger.info(f"syncing directory {src} to {dest}")
    files_to_add, files_to_remove = diff_dir_layout(src, dest)
    cpfiles(src, dest, files_to_add)
    rmfiles(dest, files_to_remove)
    rmemptydirs(dest)
    logger.info("synchronization finished")


def process(args):
    # New process requires reinitialization of logging.
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    sync(args[0], args[1])


def main():
    if len(sys.argv) < 3:
        logger.error("invalid arguments")
        sys.exit(1)

    src = sys.argv[1]
    dests = [(src, dest) for dest in sys.argv[2:]]

    with mp.Pool(mp.cpu_count()) as pool:
        pool.map(process, dests)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    main()
