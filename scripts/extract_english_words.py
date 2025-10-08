import sys, os, re, argparse, pathlib, mmap, getpass
import psycopg2
from sqlclasses import sql

import icecream; icecream.install()

LANGISO="en"

dataset_complete_re = re.compile(
    br"<page>\s+<title>(\w+)</title>.*?<text[^>]*>(.*?)</text>",
    re.DOTALL|re.MULTILINE)
lexeme_re = re.compile(
    r"\{\{(plural||archaic spelling|obsolete form) of"
    r"\|en\|(\w+)[^\}]*\}\}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-dbname", "-d", help="Name of PostgreSQL database "
                        "to connect to.", default=None)
    parser.add_argument("-A", "--archaic",
                        help="Include mappings of archaic spellings.",
                        action="store_true", default=False)
    parser.add_argument("xmlfile", type=pathlib.Path)

    args = parser.parse_args()

    dbconn = psycopg2.connect(dbname=args.dbname)
    backend = sql.Backend(psycopg2, dbconn)

    cursor = dbconn.cursor()
    cursor.execute("DELETE FROM wordlist.wordlist WHERE language_iso = %s",
                   (LANGISO,))

    def is_simple_plural(singular, plural):
        return (plural == singular + "s" or
                singular[-1] == "s" and plural == singular + "es" or
                singular[-1] == "x" and plural == singular + "es" or
                singular[-1] == "y" and plural == singular[:-1] + "ies")


    plurals = {}
    archaic = {}
    def process_dataset_match(match):
        title, dataset = [g.decode("utf-8") for g in match.groups()]
        title = title.split("#", 1)[0].lower()

        for type, reference in lexeme_re.findall(dataset):
            reference = reference.lower()
            if type == "plural":
                #if not is_simple_plural(reference, title):
                #    # Skip simple plurals.
                plurals[title] = reference
            else:
                archaic[title] = reference

    with args.xmlfile.open("br") as fp:
        contents = mmap.mmap(fp.fileno(), 0, prot=mmap.PROT_READ)
        for counter, match in enumerate(dataset_complete_re.finditer(contents)):
            print(counter, end="\r", file=sys.stderr)
            process_dataset_match(match)

        print(file=sys.stderr)

    def fix_plural(plural, singular):
        if singular in archaic:
            return (plural, archaic[singular],)
        else:
            return (plural, singular,)
    if args.archaic:
        plurals = dict([fix_plural(*tpl) for tpl in plurals.items()])

    def entries():
        yield from plurals.items()
        if args.archaic:
            yield from archaic.items()

    cmd = sql.insert("wordlist.wordlist",
                     ("language_iso", "lemma", "lexeme"),
                     [ (sql.string_literal(LANGISO),
                        sql.string_literal(lemma),
                        sql.string_literal(lexeme),)
                       for lexeme, lemma in entries() ])
    cursor.execute(*backend.rollup(cmd))

    dbconn.commit()

main()
