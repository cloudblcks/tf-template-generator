#!/bin/bash
cd ..
cd ..
mkdir temp/
cd tf_generator
for file in tests/samples/*
do
  echo Building $file
  python main.py build -f $file > ../temp/$(basename $file).tf
done
