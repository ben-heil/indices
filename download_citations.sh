# Download the citation data from the COCI version 14 citation dump
mkdir data/ -p

wget https://figshare.com/ndownloader/articles/6741422/versions/14 -P data/
mv data/14 data/citations.zip

unzip data/citations.zip -d data/
rm data/citations.zip

for file in `ls data/20*.zip`; do unzip $file -d data/; done
for file in `ls data/20*.zip`; do rm $file -d data/; done

