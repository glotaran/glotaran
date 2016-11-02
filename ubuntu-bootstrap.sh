#!/usr/bin/env bash

sudo apt-get update -y
sudo apt-get upgrade -y

# Install deps
sudo apt-get install python3-pip cython3 python3-scipy libfreetype6-dev -y

# Install Jupyter
sudo pip3 install jupyter

# Install matplotlib

# Bug
sudo ln -s /usr/include/freetype2/ft2build.h /usr/include/ft2build.h

sudo pip3 install matplotlib

# Intall minimal latex environment to allow print to pdf in jupyter
sudo apt-get install --no-install-recommends texlive-latex-base texlive-latex-extra texlive-fonts-recommended cm-super -y
sudo apt-get install --no-install-recommends pandoc -y
# TODO: still needs some more packages to correctly render images

# Install glotaran
cd /vagrant/
sudo python3 setup.py install

