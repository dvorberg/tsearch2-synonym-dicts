CREATE SCHEMA wordlist;

SET search_path = wordlist, public;

CREATE TABLE wordlist (
    language_iso CHAR(2),
    lemma text,
    lexeme text
);

