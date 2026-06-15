
examples/example_1.mfz: examples/example_1.mff
	# zip -Z store -r -j ./examples/example_1.mfz ./examples/example_1.mff
	-python ./bin/mff2mfz.py ./examples/example_1.mff

docs:
	pydoc-markdown
	cd build/docs && mkdocs build --site-dir ../../docs/html
	@echo "Docs at docs/html/index.html"

docs-serve:
	pydoc-markdown -s -o

test:
	mypy --ignore-missing-imports mffpy
	pytest --cov

clean:
	-rm examples/example_1.mfz
