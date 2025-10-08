BEGIN;

WITH lexemes AS (
   SELECT LOWER(lexeme) AS lexeme,
          LOWER(lemma) AS lemma,
          to_tsvector('german', lemma) AS lemma_v,
          to_tsvector('german', lexeme) AS lexeme_v
     FROM wordlist.wordlist
     WHERE language_iso = 'de'
),
preped AS (
   SELECT lexeme, (CASE WHEN length(lemma_v) <> 1 THEN '''' || lemma || ''':1'
                        ELSE lemma_v::text
                   END) AS lemma,
          lemma_v, lexeme_v FROM lexemes
    WHERE lemma_v <> lexeme_v
    ORDER BY lemma
)   
SELECT lexeme, substring(lemma from 2 for length(lemma)-4) AS lemma FROM preped;


ROLLBACK
