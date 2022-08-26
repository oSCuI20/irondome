# Irondome

Detect anomalous activity in disk or in path

## Purpose

Create a program that meets the following sepecifications:

* run in background
* work if it is executed by root
* monitor a critical zone. The path must be indicated as an argument
* if more arguments, these will be to the extension of file to monitor (pending/testing)
* detected abuses in disk reading
* detect intensive use of crypto activity
* detect changes in the entropy of the files
* never exceed 100MB of memory in use
* alert should be reported in the /var/log/irondome/irondome.log  (pending)

### Extras

* file changes are notified
* database (sqlite3) for store file hashed

## Usage

```
  irondome.py [OPTIONS] <path1,path2,...> <file-extension>

  OPTIONS:
    -events values separate for comas, default all. Valid values:
        'modify'
        'attrib'
        'create'
        'delete'
        'delete self'
        'move from'
        'move to'
    -init-integrity
    -logfile default, /var/log/irondome/irondome.logs
    -help
```

* Initilize. irondome must be initialized with the -init-integrity argument for database creation and file hash information to monitor.
```
python3 irondome.py -init-integrity /path/to/directory
```
* Debug or Verbose mode.
```
DEBUG=true VERBOSE=true python3 irondome.py [-init-integrity] /path/to/directory
```
