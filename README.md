## Downloads



### “Irregular” German Plurals

Iʼm running a full text index using PostgreSQLʼs brilliant `tsearch2` engine containing German as well as English texts. I employ the `hunspel` dictionary easily provided by a Debian package, in conjunction with the `german_stem` Snowball implementation shipped with the RDBMS. That alone yields acceptable results. 

I ran into a problem that some German plurals are not reduced correctly to their (singular) lemma:

```sql
t4w=# SELECT ts_lexize('german_hunspell', 'Gott');
 ts_lexize 
-----------
 {gott}
(1 row)

t4w=# SELECT ts_lexize('german_hunspell', 'Götter');
 ts_lexize 
-----------
 {götter}
(1 row)
```

Those ought to be identical. Hunspell is a spell checker and has only found a secondary use here as a linguistic helper in full text indexing. The solution is a list of German nouns in both singular and plural. Easy. 

The wonderful [Wiktionary Project](http://wiktionary.org) provides such information for German and many other languages. They provide downloadable [dumps of their](https://de.wiktionary.org/wiki/Wiktionary:Download) data in XML format. (Ah, what a time to be alive! With all the enshitification going on this is such a breath of fresh air. But I digress…) I created a namespace and a table in the database with my current `tsearch2` configuration:

```sql
CREATE SCHEMA wordlist;

SET search_path = wordlist, public;

CREATE TABLE wordlist
(
    language_iso CHAR(2),
    lemma TEXT,
    lexeme TEXT
);
```

And ran `extract_german_words.py` on `dewiktionary-20250920-pages-articles.xml` to populate it. The script requires `psycopg2` and my `sqlclasses` module available through [pypi](http://pypi.org). 

Now itʼs time to run `german_synonym_dict_query.sql` and save the result in a synonym file:

```shell
psql t4w -q -A -F ' ' -f german_synonym_dict_query.sql > german_plurals.syn
```

And thatʼs the file you may download here. 

On my 2017 iMac this query over 197204 rows yielding 161103 entries takes less than 3 seconds. Impressive! The resulting list is very large because the source material contains many compound nouns. Most of these are, in all probability, very low frequency. They will use up RAM on you database server with most entries seeing very little use. But hey: That server, in all likelihood, has Gigabytes of RAM and I ainʼt got no time to sort that list by word frequency. And it works well!

```sql
t4w=# SELECT to_tsvector('german', 'Ach, ihr Götter! große Götter
In dem weiten Himmel droben!
Gäbet ihr uns auf der Erde
Festen Sinn und guten Mut,
O wir ließen euch, ihr Guten,
Euren weiten Himmel droben! 
— Goethe');
    
-- yields: 'ach':1 'droben':10,31 'erde':16 'erden':16 'fest':17 'goethe':32 'gott':3,5 'groß':4 'gut':20,27 'gäbe':11 'himmel':9,30 'ließ':24 'mut':21 'o':22 'sinn':18 'weit':8,29 'weite':8,29 'weiten':8,29
```

