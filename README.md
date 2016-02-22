anonbox.py
==========
A tiny Python utility and module to access the
[anonbox](https://anonbox.net) one-time email service.

[anonbox.net](https://anonbox.net) was created and is being run by the
[Chaos Computer Club, Germany](https://www.ccc.de) voluntarily.
Please don't abuse it.

Documentation
-------------
See [Read The Docs](http://anonboxpy.readthedocs.org/en/latest/).

Usage
-----
`anonbox --help`
```
usage: anonbox [-h] {create,check,watch} ...

A tiny Python utility and module to access the anonbox.net one-time email
service.

positional arguments:
  {create,check,watch}  The action to perform
    create              create a mailbox and show the access keys
    check               check a mailbox for new messages
    watch               check a mailbox for new messages periodically

optional arguments:
  -h, --help            show this help message and exit

<https://github.com/nucular/anonboxpy>
```

`anonbox create --help`
```
usage: anonbox create [-h] [--host HOST] [--nossl]

optional arguments:
  -h, --help   show this help message and exit
  --host HOST  the host name of the anonbox service used, defaults to
               anonbox.net
  --nossl      don't use SSL when accessing the service
```

`anonbox check --help`
```
usage: anonbox check [-h] [--host HOST] [--nossl]
                     [--mailbox DATEHASH,PRIVATE,PUBLIC] [--browse]

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           the host name of the anonbox service used, defaults to
                        anonbox.net
  --nossl               don't use SSL when accessing the service
  --mailbox DATEHASH,PRIVATE,PUBLIC
                        use an existing mailbox instead of creating a new one
  --browse, -b          open received messages in the browser (HTML messages
                        may compromise your anonymity)
```

`anonbox watch --help`
```
usage: anonbox watch [-h] [--host HOST] [--nossl]
                     [--mailbox DATEHASH,PRIVATE,PUBLIC] [--browse]
                     [--delay DELAY]

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           the host name of the anonbox service used, defaults to
                        anonbox.net
  --nossl               don't use SSL when accessing the service
  --mailbox DATEHASH,PRIVATE,PUBLIC
                        use an existing mailbox instead of creating a new one
  --browse, -b          open received messages in the browser (HTML messages
                        may compromise your anonymity)
  --delay DELAY, -d DELAY
                        delay between checks in seconds, defaults to 30
```
