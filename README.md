# diffweb
Simple website monitor

```
$ python3 diffweb.py --help
usage: diffweb.py [-h] [-v] [-c CONFIG]

Detect changes in web content

optional arguments:
  -h, --help            show this help message and exit
  -v, --visualize       visualize config html selections
  -c CONFIG, --config CONFIG
                        config file
```

**config.json**
```
[
    {
        "name":"Raspberry Pi Zero",
        "url":"https://rpilocator.com/?cat=PIZERO",
        "selector":"#myTable",
        "del-selector":[
            "#myTable tr [data-sort]"
        ]
    }
]
```
