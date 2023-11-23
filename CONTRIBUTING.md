# CONTRIBUTING

Some general design principles:

- This is a CLI heavy project intended for technical users.
- Users should be expected to configure, make manual entries, and overrides
  via editing text files (vs. any sort of UI or CLI).
- For now, one py file in the main directory should be used for each function.
- Each py file can take input from other py files, but should generally not
  modify them; instead, only creating their own file.
- Files in the output directory should be expected to be overwritten by py
  files.
- Files in other directories should not be overwritten by py files.

Please feel free to create issues and pull requests with any changes. Since
this is a personal project, I won't always fix all issues that I am not
experiencing. But I will try to merge changes reasonably fast.

## TODO

- [x] Consolidate the configuration options and settings. Right now they are spread across multiple toml and py files.
- [x] setup.py to create directories and sample files (DID IN config/__init__.py)
- [x] Add to txns.csv - token id (for defillama pricing)
- [x] Custom designation of income, buy, sell in the txns.py file
- [x] Ability to manually mark / handle transactions known to be weird
- [x] Something may be broken on selling for USDC
- [ ] flatten should incorporate prices from debank json files
- [ ] flatten should cache token address to symbol look up

## GITHUB SETUP

Since contributors may also be using GitHub with their IRL identities,
here are some gotchas to check if/when you want to contribute under your
cryptonym:

- Be sure to create and use the correct GitHub account

- Set your local git config appropriately

```sh
git config --local user.name "Llanero"
git config --local user.email "iamllanero@gmail.com"
```

- Double check your config

```sh
git config --local user.name
git config --local user.email
```

- As an extra layer of precaution, you can change your global config.

```sh
git config --global user.name "Llanero"
git config --global user.email "iamllanero@gmail.com"
```

- And, of coure, check the global config

```sh
git config --global user.name
git config --global user.email
```
