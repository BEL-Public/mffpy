
examples/example_1.mfz: examples/example_1.mff
	# zip -Z store -r -j ./examples/example_1.mfz ./examples/example_1.mff
	-python ./bin/mff2mfz.py ./examples/example_1.mff


# some tests depend on the existence of a zipped version of
# 'examples/example_1.mff/'
test: examples/example_1.mfz
	mypy --ignore-missing-imports mffpy
	pytest --cov

clean:
	-rm examples/example_1.mfz
