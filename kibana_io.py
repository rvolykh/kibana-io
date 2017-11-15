# Inspired by: 
# https://github.com/elastic/beats-dashboards
#
# TODO: use GET _search with pagination
# TODO: save config (defaultIndex)


import argparse
import os
import json
import requests


def export_objects(es_kibana, out_directory, doc_type):
    url = '{}/{}/_search?size={}'.format(es_kibana, doc_type, 5000)
    r = requests.get(url)
    if r.status_code == 404:
        print('[WARN] Documents "{}" not found, skipping'.format(doc_type))
        return
    if r.status_code != 200:
        print('[ERR] Failed to create dump "{}", code={} text={}'.format(doc_type, r.status_code, r.text))
        exit(1)
    dir = os.path.join(out_directory, doc_type)
    if not os.path.exists(dir):
        os.makedirs(dir)
    response = r.json()
    total = response['hits']['total']
    successful = 0
    for doc in response['hits']['hits']:
        filepath = os.path.join(dir, doc['_id'] + '.json')
        try:
            with open(filepath, 'w') as f:
                json.dump(doc['_source'], f, indent=2)
            successful += 1
        except IOError as e:
            print('[WARN] Failed to backup {} "{}": {}'.format(doc_type, os.path.basename(filepath), e))
            continue
    if total != successful:   
        print('[ERR] Exported only ({}/{}) {}(-s/-es)'.format(successful, total, doc_type))
    else:
        print("[OK] Exported {} {}".format(total, doc_type))


def import_objects(es_kibana, in_directory, doc_type):
    dir = os.path.join(in_directory, doc_type)
    if not os.path.exists(dir):
        print('[ERR] Folder not found')
        exit(1)
    files = []
    for (dirpath, dirnames, filenames) in os.walk(dir):
        files.extend(filenames)
        break
    total = len(files)
    successful = 0
    for file in files:
        with open(os.path.join(dir, file), 'r') as payload:
            name = os.path.splitext(os.path.basename(file))[0]
            url = '{}/{}/{}'.format(es_kibana, doc_type, name)
            r = requests.put(url, data=payload, verify=False, 
                    headers={'content-type': 'application/json'})
            if not r.status_code in [200, 201]:
                print("[WARN] Failed to import file {} code={}: {}".format(name, r.status_code, r.text))
            else:
                successful += 1
            r.close()
    if total != successful:
        print('[ERR] Imported only ({}/{}) {}(-s/-es)'.format(successful, total, doc_type))
    else:
        print('[OK] Imported all {} {}(-s/-es)'.format(total, doc_type))


# Workaround for: https://github.com/elastic/beats-dashboards/issues/94
# def workaround_before_import(es_kibana):
    # requests.put(es_kibana, verify=False)
    # payload = {"search": {"properties": {"hits": {"type": "integer"}, "version": {"type": "integer"}}}}
    # requests.put('{}/{}'.format(es_kibana, "_mapping/search"), data=payload, verify=False, 
    #                 headers={'content-type': 'application/json'}) 


def main():
    parser = argparse.ArgumentParser(
        description="""
                Export/Import Kibana searches, visualizations, dashboards and 
                index-patterns in json files
                    """, 
        usage = """
                python kibana_io.py export --url http://localhost:9200 --dir ./dump
                python kibana_io.py import --dir ./dump --url http://localhost:9200
                """)
    parser.add_argument('action', choices=['export', 'import'], 
        help="""
            Enter action 'export' - to dump kibana resources
            or action 'import' - to upload dump to elasticsearch
        """)
    parser.add_argument("--url", help="Elasticsearch URL. E.g. " +
                        "http://localhost:9200.", required=True)
    parser.add_argument("--dir", help="Output/Input directory", required=True)
    parser.add_argument("--index", help="Kibana index", default=".kibana")

    args = parser.parse_args()

    es_kibana = '{}/{}'.format(args.url, args.index)
    if args.action == 'import':
        import_objects(es_kibana, args.dir, "index-pattern")
        import_objects(es_kibana, args.dir, "search")
        import_objects(es_kibana, args.dir, "visualization")
        import_objects(es_kibana, args.dir, "dashboard")
    else:
        export_objects(es_kibana, args.dir, "dashboard")
        export_objects(es_kibana, args.dir, "visualization")
        export_objects(es_kibana, args.dir, "search")
        export_objects(es_kibana, args.dir, "index-pattern")
        

if __name__ == "__main__":
    main()
