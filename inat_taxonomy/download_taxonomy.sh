#!/bin/bash
#download from https://www.inaturalist.org/taxa/inaturalist-taxonomy.dwca.zip
# then unzip to ../data/inaturalist-taxonomy.dwca
rm -rf ../data/inaturalist-taxonomy.dwca
wget https://www.inaturalist.org/taxa/inaturalist-taxonomy.dwca.zip -P ../data/
unzip ../data/inaturalist-taxonomy.dwca.zip -d ../data/inaturalist-taxonomy.dwca
rm ../data/inaturalist-taxonomy.dwca.zip
