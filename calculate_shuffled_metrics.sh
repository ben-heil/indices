for FILE in `ls data/shuffled_networks/*.pkl`
do
	BASE=`basename $FILE`
	echo $BASE
	BASE=${BASE%.pkl}
	echo $BASE
	if [ -f "output/shuffle_results/${BASE}-pagerank.pkl" ]; then
    	echo "$BASE pagerank exists"
	else 
    	python indices/run_metric_on_graph.py $FILE pagerank output/shuffle_results/
	fi

	if [ -f "output/shuffle_results/${BASE}-disruption_idx.pkl" ]; then
    	echo "$BASE disruption index exists"
	else 
    	python indices/run_metric_on_graph.py $FILE disruption_idx output/shuffle_results/
	fi
done

