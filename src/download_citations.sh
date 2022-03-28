# Download the citation data from the COCI version 14 citation dump
mkdir data/

wget https://figshare.com/ndownloader/articles/6741422/versions/14 -P data/
mv data/14 data/citations.zip
unzip data/citations.zip
rm citations.zip

for file in `ls data/*.zip`; do unzip $file; done
