BIO_SUBHEADINGS=("botany" "cell biology" "computational biology" "cryobiology" "developmental biology" "ecology" "exobiology" "genetics" "laboratory animal science" "microbiology" "natural history" "neurobiology" "parasitology" "photobiology" "radiobiology" "sociobiology" "synthetic biology" "zoology")
INFORMATICS=("cheminformatics" "computational biology" "consumer health informatics" "dental informatics" "medical informatics" "nursing informatics" "public health informatics")
ALGORITHMS=("artificial intelligence" "latent class analysis" "cellular automata")

for HEADING in "${BIO_SUBHEADINGS[@]}"
do
	python src/download_article_metadata.py "$HEADING"
done

for HEADING in "${INFORMATICS[@]}"
do
	python src/download_article_metadata.py "$HEADING"
done

for HEADING in "${ALGORITHMS[@]}"
do
	python src/download_article_metadata.py "$HEADING"
done
