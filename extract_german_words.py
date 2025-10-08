import sys, os, re, argparse, pathlib, mmap, getpass
import psycopg2
from sqlclasses import sql

LANGISO="de"

dataset_complete_re = re.compile(
    "\\{\\{Deutsch Substantiv Übersicht([^\\}]+)}}".encode("utf-8"))
lexeme_re = re.compile(
    "(?:Nominativ|Genitiv|Dativ|Akkusativ) (?:Singular|Plural)\\*?=(\\w+)")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-dbname", "-d", help="Name of PostgreSQLy database "
                        "to connect to.", default=None)
    parser.add_argument("xmlfile", type=pathlib.Path)

    args = parser.parse_args()

    dbconn = psycopg2.connect(dbname=args.dbname)
    backend = sql.Backend(psycopg2, dbconn)

    cursor = dbconn.cursor()
    cursor.execute("DELETE FROM wordlist.wordlist WHERE language_iso = %s",
                   (LANGISO,))

    def process_dataset_match(match):
        dataset = match.group(1).decode("utf-8")
        lexemes = lexeme_re.findall(dataset)

        if lexemes:
            lemma = lexemes[0]
            lexemes = set(lexemes)
            lexemes.remove(lemma)

        if lexemes:
            cmd = sql.insert("wordlist.wordlist",
                             ("language_iso", "lemma", "lexeme"),
                             [ (sql.string_literal(LANGISO),
                                sql.string_literal(lemma),
                                sql.string_literal(lexeme),)
                               for lexeme in lexemes ])
            cursor.execute(*backend.rollup(cmd))


    with args.xmlfile.open("br") as fp:
        contents = mmap.mmap(fp.fileno(), 0, prot=mmap.PROT_READ)
        for counter, match in enumerate(dataset_complete_re.finditer(contents)):
            print(counter, end="\r", file=sys.stderr)
            process_dataset_match(match)

        print(file=sys.stderr)

    dbconn.commit()

main()
