#!/bin/bash
cd ..
mkdir temp/
for file in tests/samples/*
do
  echo Building $file
  python cli.py build -f $file -o /temp/$(basename $file).tf
done
