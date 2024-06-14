fairseq-preprocess --tokenizer moses -s amr -t words --trainpref $1\_train --validpref $1\_dev --testpref $1\_test
