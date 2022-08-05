#!/bin/bash
cd ..
mkdir temp/
cd tf_generator
for file in tests/samples/*
do
  echo Building $file
  python cli.py build -f $file -o /temp/$(basename $file).tf
done
