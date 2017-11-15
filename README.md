# kibana-io
Python script to Export/Import Kibana dashboards/visualization/searches/index-patterns

### Usage: 
	python kibana_io.py export --url http://localhost:9200 --dir ./dump
	python kibana_io.py import --dir ./dump --url http://localhost:9200
                
required arguments:
```
export - dump kibana resources
import - upload dump to elasticsearch
```

optional arguments:
```
  -h, --help       show this help message and exit
  --url URL        Elasticsearch URL. E.g. http://localhost:9200.
  --dir DIR        Output/Input directory
```
