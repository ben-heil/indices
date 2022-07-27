
for FILE in `ls data/networks/*.pkl`
do
	echo `basename $FILE`
	python indices/shuffle_graph.py $FILE data/shuffled_networks/
done
