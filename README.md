# dbsnap

## Installation

1. Clone to somewhere.
2. `pip install --user -r requirements.txt`
3. Symlink `dbsnap.py` to your $PATH, e.g. `ln -s $PWD/dbsnap.py /usr/local/bin/dbsnap`

## Usage

1. Set your current database using `dbsnap connect`, e.g.

    ```bash
    dbsnap connect mysql://user:password@localhost/dbname
    ```

    Currently, only `mysql` is supported. If you leave the password empty (`mysql://user:@host...`), you'll be prompted for it. If you leave out the colon (`mysql://user@host...`), no password will be used.

    The full string (including password, if any), will be stored locally in a file (`~/.local/share/dbsnap/current`).

2. Create a snapshot:

    ```bash
    dbsnap snap
    ```

3. Break your database.
4. Restore your snapshot:

    ```bash
    dbsnap restore
    ```

    The `restore` command finds the latest snapshot for the current database. You can pass a name for the snapshot file to `snap` and `restore` commands to use a different one. Use `dbsnap list` to see available snapshots of the current database, and `dbsnap clear` to remove all of them.

## License

This work is licensed under the MIT License. See `LICENSE` for details.
