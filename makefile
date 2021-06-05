
examples/example_1.mfz: examples/example_1.mff
	# zip -Z store -r -j ./examples/example_1.mfz ./examples/example_1.mff
	-python ./bin/mff2mfz.py ./examples/example_1.mff

test:
	mypy --ignore-missing-imports mffpy
	pytest --cov

clean:
	-rm examples/example_1.mfz
