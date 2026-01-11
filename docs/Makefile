# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build
ZHBUILDDIR    = build/zh

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

generate_doc:
	sphinx-apidoc ../pydualsense -f -o ./source  --ext-autodoc --ext-coverage --ext-todo

# Build Chinese-only site (root_doc=zh/index) into build/zh
html-zh:
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(ZHBUILDDIR)" -D root_doc=zh/index $(SPHINXOPTS) $(O)

clean-zh:
	@$(SPHINXBUILD) -M clean "$(SOURCEDIR)" "$(ZHBUILDDIR)" -D root_doc=zh/index $(SPHINXOPTS) $(O)
