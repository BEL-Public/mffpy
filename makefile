
examples/zipped_example_1.mff: examples/example_1.mff
	# -Z store : no compression
	# -r : recursive
	# -j : remove relative path names
	zip -Z store -r -j ./examples/zipped_example_1.mff ./examples/example_1.mff
	# zip -r -j ./examples/zipped_example_1.mff ./examples/example_1.mff

# some tests depend on the existence of a zipped version of
# 'examples/example_1.mff/'
test: examples/zipped_example_1.mff
	mypy --ignore-missing-imports mffpy
	pytest --cov

clean:
	rm examples/zipped_example_1.mff
