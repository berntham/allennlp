#! /usr/bin/env python
"""
Goes through all the inline-links in markdown files and reports the breakages.
"""
import re
import sys
import pathlib
from multiprocessing.dummy import Pool
from typing import Tuple, NamedTuple
import requests

class MatchTuple(NamedTuple):
    source: str
    name: str
    link: str

def url_ok(match_tuple: MatchTuple) -> Tuple[MatchTuple, bool]:
    try:
        result = requests.get(match_tuple.link)
        print(f"  {result.status_code}: {match_tuple.source}")
        return (match_tuple, result.ok)
    except requests.ConnectionError:
        return (match_tuple, False)

if __name__ == "__main__":

    print("Finding all markdown files in the current directory...")

    project_root = (pathlib.Path(__file__).parent / "..").resolve() # pylint: disable=no-member
    markdown_files = project_root.glob('**/*.md')

    all_matches = set()
    url_regex = re.compile(r'\[([^!][^\]]+)\]\((http[s]?[^)(]+)\)')
    for markdown_file in markdown_files:
        with open(markdown_file) as handle:
            for line in handle.readlines():
                matches = url_regex.findall(line)
                for name, link in matches:
                    if 'localhost' not in link:
                        all_matches.add(MatchTuple(source=str(markdown_file), name=name, link=link))
    print(f"  {len(all_matches)} markdown files found")

    print("Checking to make sure we can retrieve each web URL...")

    with Pool(processes=10) as pool:
        results = pool.map(url_ok, [match for match in list(all_matches)])
    unreachable_results = [result for result in results if not result[1]]

    if unreachable_results:
        print(f"Unreachable Links ({len(unreachable_results)}):")
        for index, result in enumerate(unreachable_results):
            print("  " + str(index))
            print("  Source: " + result[0].source)
            print("  Name: " + result[0].name)
            print("  Link: " + result[0].link)
        sys.exit(1)
    print("No Unreachable link found.")
