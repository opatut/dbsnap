#!/usr/bin/env python3

import unicodedata, argparse, os, time, sys, re, subprocess, shutil
from urllib.parse import urlparse
from appdirs import AppDirs

# determine and create root directory
dirs = AppDirs("dbsnap", "opatut")
root_dir = dirs.user_data_dir
os.makedirs(root_dir, exist_ok=True)
current_url_file = os.path.join(root_dir, 'current')

def parse_connection_string(url):
    r = urlparse(url)

    if not r.scheme in ("mysql",):
        raise Error("invalid scheme: " + r.scheme)

    return dict(
        username=r.username,
        password=r.password,
        scheme=r.scheme,
        hostname=r.hostname,
        port=r.port,
        name=(r.path or '').lstrip('/'),
        snapshot_dir=os.path.join(root_dir, slug(url)),
    )

def build_mysql_args(connection):
    s = ""
    if connection['username']: s += "-u " + connection['username'] + " "
    if connection['password'] != None: 
        if connection['password']: 
            s += "-p=" + connection['password'] + " "
        else:
            s += '-p '

    if connection['hostname']: s += "-h " + connection['hostname'] + " "
    if connection['port']: s += "--port " + str(connection['port']) + " "
    return s.strip()

def get_connection(required=False):
    try:
        with open(current_url_file, 'r') as f:
            [url] = f.readlines()
    except:
        if required:
            print("Please run 'dbsnap connect' first")
            sys.exit(1)
        else:
            return None

    connection = parse_connection_string(url)
    os.makedirs(connection['snapshot_dir'], exist_ok=True)
    return connection

def slug(s):
    s = unicodedata.normalize('NFKD', s)
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    s = re.sub(r'[-]+', '-', s)
    return s

# -------

def print_help(args):
    parser.print_help()

def connect(args):
    url = args.url

    parse_connection_string(url) # validate

    with open(current_url_file, 'w') as f:
        f.writelines(url)

def list_(args):
    connection = get_connection(True)
    files = list_in_dir(connection['snapshot_dir'])
    print("\n".join(files))

def list_in_dir(d):
    return list(reversed(sorted(os.listdir(d), key=lambda f: os.path.getctime(os.path.join(d, f)))))

def create(args):
    connection = get_connection(True)
    filename = re.sub(r'(\.sql)?$', '.sql', args.name) \
            if args.name else \
            ("{}-{}.sql".format(time.strftime("%Y%m%d-%H%M%S"), slug(connection['name'])))

    filepath = os.path.join(connection['snapshot_dir'], filename)

    cmd = "mysqldump {args} --databases {name} --add-drop-database > {filepath}".format(
            args=build_mysql_args(connection),
            name=connection['name'],
            filepath=filepath
    )

    proc = subprocess.Popen(cmd, shell=True)
    proc.communicate()
    print("Created: {}".format(filename))


def restore(args):
    connection = get_connection(True)

    if args.name:
        filename = args.name
    else:
        files = list_in_dir(connection['snapshot_dir'])
        if not files:
            print("No snapshot found")
            sys.exit(1)
        filename = files[0]

    filepath = os.path.join(connection['snapshot_dir'], filename)
    if not os.path.exists(filepath):
        print("Snapshot not found at: " + filepath)
        sys.exit(1)

    cmd = "mysql {args} {name} < {filepath}".format(
            args=build_mysql_args(connection),
            name=connection['name'],
            filepath=filepath
    )

    proc = subprocess.Popen(cmd, shell=True)
    proc.communicate()
    print("Restored: {}".format(filename))

def clear(args):
    connection = get_connection(True)
    shutil.rmtree(connection['snapshot_dir'])
    print("Cleared: {}".format(connection['snapshot_dir']))

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(title='subcommands')
parser.set_defaults(cmd=print_help)

connect_parser = subparsers.add_parser('connect', help="set current db")
connect_parser.add_argument('url', help='database connection string')
connect_parser.set_defaults(cmd=connect)
 
create_parser = subparsers.add_parser('create', aliases=['snap'], help='create a snapshot')
create_parser.add_argument('-n', '--name', help='snapshot name')
create_parser.set_defaults(cmd=create)

restore_parser = subparsers.add_parser('restore', help="restore a snapshot")
restore_parser.add_argument('-n', '--name', help='snapshot name (defaults to latest)')
restore_parser.set_defaults(cmd=restore)

list_parser = subparsers.add_parser('list', help="list existing snapshots (latest first)")
list_parser.set_defaults(cmd=list_)

clear_parser = subparsers.add_parser('clear', help="clear all snapshots of current db")
clear_parser.set_defaults(cmd=clear)

args = parser.parse_args()
args.cmd(args)
