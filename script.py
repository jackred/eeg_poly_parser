# -*- Mode: Python; tab-width: 8; indent-tabs-mode: nil; python-indent-offset: 4 -*-
# vim:set et sts=4 ts=4 tw=80:

import os
import csv
import requests
from datetime import datetime
from re import findall

data_path = "data"
fmt_path = "formatted"
old_path_files = os.path.join(os.getcwd(), data_path)
new_path_files = os.path.join(os.getcwd(), fmt_path)
new_header = ['Adapted', 'Day', 'Schedule']


def read_csv(name_file):
    with open(os.path.join(old_path_files, name_file), 'r') as f:
        reader = csv.reader(f, delimiter=",")
        headers = next(reader, None)
        column = []
        for row in reader:
            column.append(row)
    return column, headers


def write_csv(rows, headers, name):
    with open(name, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)


def parse_name_file():
    with open("filename.txt", ) as f:
        lines = f.read().splitlines()
    res = {}
    for i in range(len(lines)):
        parse = lines[i].split("@", 1)
        res[parse[1]] = parse[0]
    return res


def getSchedule(date, json):
    b = False
    i = len(json['historicSchedules']) - 1
    fmt_date = datetime.strptime(date, '%m/%d/%Y')
    while not b and i >= 0:
        fmt_schedule_date = datetime.strptime(
            json['historicSchedules'][i]['setAt'].split('T')[0], '%Y-%m-%d')
        b = fmt_date >= fmt_schedule_date
        i -= 1
    if b:
        return json['historicSchedules'][i-1]
    else:
        return -1


def handle_lines(res, name, json, headers):
    for row in res:
        schedule = getSchedule(row[0], json)
        if schedule == -1:
            for i in range(3):
                row.insert(0, '')
            continue
        day = (datetime.strptime(row[0], '%m/%d/%Y')
               - datetime.strptime(schedule['setAt'].split('T')[0], '%Y-%m-%d')
               ).days + 1
        row.insert(0, schedule['adapted'])
        row.insert(0, day)
        row.insert(0, schedule['name'])
    write_csv(res, headers, name)


def handle_file(name_file, key, json):
    name_file = os.path.splitext(name_file)[0]
    in_key = False
    keys = list(key.keys())
    i = 0
    while i < len(keys) and not in_key:
        res = findall("^"+keys[i], name_file)
        in_key = len(res) > 0
        i += 1
    if not in_key:
        return "%s isn't listed in  the mail index" % name_file
    else:
        name_file_re = res[0]
        rest = name_file.split(name_file_re)[1]
    if key[name_file_re] not in json:
        return "Name \"%s\" not in report" % key[name_file]
    else:
        name = "%s.csv" % os.path.join(old_path_files, name_file)
        new_name = ("%s%s.csv" %
                    (os.path.join(new_path_files, key[name_file_re]), rest))
        res, headers = read_csv(name)
        for i in new_header:
            headers.insert(0, i)
        handle_lines(res, new_name, json[key[name_file_re]], headers)
        return ("File %s%s.csv has been created from %s.csv" %
                (key[name_file_re], rest, name_file))


def handle_files(key, json):
    files = os.listdir(old_path_files)
    result = list(map(lambda x: handle_file(x, key, json), files))
    print("\n".join(result))


def get_json():
    r = requests.get("https://cache.polyphasic.net/report.json").json()
    res = {}
    for i in r:
        res[i["tag"]] = i
    return res


def main():
    json = get_json()
    key = parse_name_file()
    handle_files(key, json)


if __name__ == '__main__':
    main()
