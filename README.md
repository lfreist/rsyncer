# rsyncer
rsyncer is a simple rsync wrapper for python.

## Prerequisites
You need to have an rsync installation on your system and added to your system's path.

## Installation
1. download this repository
2. from within this repo run `make install`
3. test installation by importing `rsyncer` in a python shell

## Usage
You can choose between the simple *One-Function-Call* and the more powerful *Syncer* utility to run rsync commands using
rsyncer.

### The *One-Function-Call*
This is the simplest usage of rsyncer. You can just call the `rsync` function with the necessary arguments to run a
rsync command. This function will return a boolean indicating if the process finished successfully or not:

```python
from rsyncer.rsync import rsync

suc = rsync(...)
if suc:
    print("rsync run successfully.")
else:
    print("There was an error running rsync.")
```

### The more powerful *Syncer* object
With this utility, you get a larger set of functionalities like
- creating a rsync command
- running a rsync command
- get the current progress of a running rsync process
- ...

> *Mark:* `rsyncer.rsync.Syncer` creates a temporary files in `/tmp` where rsync's output is written to. Therefore, a `Syncer` 
> should be closed when you are done working with it (The rsync subprocess will not be killed).

You can either create a `Syncer` object and use its `close()` (or `exit()`, which will kill the rsync process) method in
the end, or you can use a `Syncer` within a `with` statement:
```python
from rsyncer import rsync

s = rsync.Syncer(...)
s.run()
s.get_command()
s.progress()
# and/or other operations
s.close() # or s.exit() if you want to kill the rsync process as well
```
```python
from rsyncer import rsync

with rsync.Syncer(...) as s:
    s.run()
    s.get_command()
    s.progress()
    # and/or other operations
```

## Examples
As far as possible, we provide a *One-Function-Call* and a *Syncer* implementation for each example.

### Syncing a single file
> `$ rsync /path/to/file /path/to/destination`

#### *One-Function-Call*
```python
from rsyncer import rsync

rsync.rsync(source="/path/to/file", dest="/path/to/destination")
```

#### *Syncer*
```python
from rsyncer import rsync

with rsync.Syncer(source="/path/to/file", dest="/path/to/destination") as s:
    s.run()
```

### Syncing a directory
> `$ rsync /path/to/dir /path/to/destination`

#### *One-Function-Call*
```python
from rsyncer import rsync

rsync.rsync(source="/path/to/dir", dest="/path/to/destination")
```

#### *Syncer*
```python
from rsyncer import rsync

with rsync.Syncer(source="/path/to/dir", dest="/path/to/destination") as s:
    s.run()
```

### Syncing a directory using a remote source
> `$ rsync -a user@server.org:/path/to/dir /path/to/destination`

#### *One-Function-Call*
```python
from rsyncer import rsync

rsync.rsync(source="/path/to/dir", dest="/path/to/destination", source_ssh="user@server.org")
```

#### *Syncer*
```python
from rsyncer import rsync

with rsync.Syncer(source="/path/to/dir", dest="/path/to/destination", source_ssh="user@server.org") as s:
    s.run()
```

### Exclude a file
> `$ rsync /path/to/dir /path/to/destination --exclude /path/to/dir/tmp.txt`

#### *One-Function-Call*
```python
from rsyncer import rsync

rsync.rsync(source="/path/to/dir", dest="/path/to/destination", excludes=["/path/to/dir/tmp.txt"])
```

#### *Syncer*
```python
from rsyncer import rsync

with rsync.Syncer(source="/path/to/dir", dest="/path/to/destination", excludes=["/path/to/dir/tmp.txt"]) as s:
    s.run()
```