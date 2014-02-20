# -*- coding: utf-8 -*-
#
# Ryu book documentation build configuration file, created by
# sphinx-quickstart on Wed Oct 16 15:05:08 2013.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import sys, os

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('.'))

# -- General configuration -----------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['japanesesupport', 'ryubuilder']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
#source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'Ryubook'
copyright = '2014, RYU project team'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '1.0'
# The full version, including alpha/beta/rc tags.
release = '1.0'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None
language = 'ja'

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
#today_fmt = '%B %d, %Y'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = []

# The reST default role (used for this markup: `text`) to use for all documents.
#default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
#modindex_common_prefix = []


# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'default'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#html_theme_options = {}

# Add any paths that contain custom themes here, relative to this directory.
#html_theme_path = []

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
#html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#html_additional_pages = {}

# If false, no module index is generated.
#html_domain_indices = True

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, links to the reST sources are added to the pages.
#html_show_sourcelink = True

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
#html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = None

# Output file base name for HTML help builder.
htmlhelp_basename = 'Ryubookdoc'


# -- Options for LaTeX output --------------------------------------------------

latex_elements = {
'papersize': 'a4paper',
'pointsize': '10pt',
'preamble': r"""
\makeatletter

\renewcommand{\maketitle}{
 \begin{titlepage}
  \begingroup
   \setlength{\unitlength}{1truemm}
   \begin{picture}(210,234)(25,38)
    \begingroup
     \makeatletter
     \ifx\svgwidth\undefined
      \setlength{\unitlength}{595.27558594bp}
      \ifx\svgscale\undefined
       \relax
      \else
       \setlength{\unitlength}{\unitlength * \real{\svgscale}}
      \fi
     \else
      \setlength{\unitlength}{\svgwidth}
     \fi
     \global\let\svgwidth\undefined
     \global\let\svgscale\undefined
     \begin{picture}(1,1.4142857)
      \put(0,0){\includegraphics[width=\unitlength]{cover.eps}}
     \end{picture}
     \makeatother
    \endgroup
   \end{picture}
  \endgroup
  \@thanks
 \end{titlepage}
 \let\thanks\relax\let\maketitle\relax
}

% ---- Header/Footer
\fancypagestyle{normal}{
 \def\chaptermark##1{\markboth{\@chapapp\thechapter\@chappos ##1}{}}
 \fancyhf{}
 \fancyfoot[LE,RO]{{\py@HeaderFamily\thepage}}
 \fancyhead[LE]{{\py@HeaderFamily\nouppercase{\leftmark}}}
 \fancyhead[RO]{{\py@HeaderFamily\nouppercase{\rightmark}}}
 \renewcommand{\headrulewidth}{0.4pt}
 \renewcommand{\footrulewidth}{0.4pt}
}
\fancypagestyle{plainhead}{
 \fancyhf{}
 \fancyfoot[LE,RO]{{\py@HeaderFamily\thepage}}
 \renewcommand{\headrulewidth}{0pt}
 \renewcommand{\footrulewidth}{0.4pt}
}
% ---- Code block
\usepackage{listings,jlisting}
\lstset{
 language={Python},
 frame=single,
 framerule=0pt,
 backgroundcolor={\color[rgb]{0.92,0.92,1}},
 basicstyle={\ttfamily\footnotesize},
 commentstyle={\color[rgb]{0.5,0.5,0.5}},
 keywordstyle={\bfseries\color[rgb]{0,0.4,0.1}},
 emph={self,super}, emphstyle=\color[rgb]{0.4,0.6,0.5},
 showstringspaces=false,
 breaklines=true,
 breakatwhitespace=false,
 breakindent=0pt,
 breakautoindent=false
}
\lstnewenvironment{sourcecode}{}{}
\lstnewenvironment{console}{\lstset{
 language={},
 frame=single,
 framerule=0pt,
 backgroundcolor={\color[rgb]{0.1,0.1,0.1}},
 basicstyle={\ttfamily\footnotesize\color[rgb]{0.9,0.9,0.9}},
 breaklines=true,
 breakatwhitespace=false,
 breakindent=0pt,
 breakautoindent=false
}}{}
% ---- Admonition
\definecolor{notecolor}{rgb}{1,1,.6}
\definecolor{notefrcolor}{rgb}{.6,.6,.3}
\definecolor{hintcolor}{rgb}{.8,1,.8}
\definecolor{hintfrcolor}{rgb}{.5,.6,.5}
\definecolor{importantcolor}{rgb}{1,.8,.8}
\definecolor{importantfrcolor}{rgb}{.6,.4,.4}
\definecolor{tipcolor}{rgb}{.8,1,.8}
\definecolor{tipfrcolor}{rgb}{.5,.6,.5}
\definecolor{warncolor}{rgb}{1,1,0}
\definecolor{warnfrcolor}{rgb}{.5,.5,0}
\definecolor{dangercolor}{rgb}{.8,.2,.2}
\definecolor{dangerfrcolor}{rgb}{.4,.1,.1}
\newcommand{\py@ryubox}[2]{
 \small
 \color[rgb]{.3,.3,.3}
 \setlength\fboxsep{5pt}
 \def\FrameCommand{\fcolorbox{#2}{#1}}
 \MakeFramed {\FrameRestore}
}
\newcommand{\py@endryubox}{
 \endMakeFramed
}
\renewcommand{\py@noticestart@note}{\py@ryubox{notecolor}{notefrcolor}}
\renewcommand{\py@noticeend@note}{\py@endryubox}
\renewcommand{\py@noticestart@hint}{\py@ryubox{hintcolor}{hintfrcolor}}
\renewcommand{\py@noticeend@hint}{\py@endryubox}
\renewcommand{\py@noticestart@important}{\py@ryubox{importantcolor}{importantfrcolor}}
\renewcommand{\py@noticeend@important}{\py@endryubox}
\renewcommand{\py@noticestart@tip}{\py@ryubox{tipcolor}{tipfrcolor}}
\renewcommand{\py@noticeend@tip}{\py@endryubox}
\renewcommand{\py@noticestart@warning}{\py@ryubox{warncolor}{warnfrcolor}}
\renewcommand{\py@noticeend@warning}{\py@endryubox}
\renewcommand{\py@noticestart@caution}{\py@ryubox{warncolor}{warnfrcolor}}
\renewcommand{\py@noticeend@caution}{\py@endryubox}
\renewcommand{\py@noticestart@attention}{\py@ryubox{warncolor}{warnfrcolor}}
\renewcommand{\py@noticeend@attention}{\py@endryubox}
\renewcommand{\py@noticestart@danger}{\py@ryubox{dangercolor}{dangerfrcolor}}
\renewcommand{\py@noticeend@danger}{\py@endryubox}
\renewcommand{\py@noticestart@error}{\py@ryubox{dangercolor}{dangerfrcolor}}
\renewcommand{\py@noticeend@error}{\py@endryubox}

\makeatother
"""
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
  ('index', 'Ryubook.tex', 'RYU SDN Framework',
   'RYU project team', 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# If true, show page references after internal links.
#latex_show_pagerefs = False

# If true, show URL addresses after external links.
#latex_show_urls = False

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_domain_indices = True

latex_docclass = {'manual': 'jsbook'}

latex_additional_files = ['jlisting.sty', 'images/cover.eps']

# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('index', 'ryubook', 'RYU SDN Framework',
     ['RYU project team'], 1)
]

# If true, show URL addresses after external links.
#man_show_urls = False


# -- Options for Texinfo output ------------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
  ('index', 'Ryubook', 'RYU SDN Framework',
   'RYU project team', 'Ryubook', 'RYU SDN Framework',
   'Miscellaneous'),
]

# Documents to append as an appendix to all manuals.
#texinfo_appendices = []

# If false, no module index is generated.
#texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
#texinfo_show_urls = 'footnote'


# -- Options for Epub output ---------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = 'RYU SDN Framework'
epub_author = 'RYU project team'
epub_publisher = 'RYU project team'
epub_copyright = '2014, RYU project team'

# The language of the text. It defaults to the language option
# or en if the language is not set.
#epub_language = ''

# The scheme of the identifier. Typical schemes are ISBN or URL.
#epub_scheme = ''

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#epub_identifier = ''

# A unique identification for the text.
#epub_uid = ''

# A tuple containing the cover image and cover page html template filenames.
epub_cover = ('_static/cover.png', '')

# HTML files that should be inserted before the pages created by sphinx.
# The format is a list of tuples containing the path and title.
#epub_pre_files = []

# HTML files shat should be inserted after the pages created by sphinx.
# The format is a list of tuples containing the path and title.
#epub_post_files = []

# A list of files that should not be packed into the epub file.
#epub_exclude_files = []

# The depth of the table of contents in toc.ncx.
#epub_tocdepth = 3

# Allow duplicate toc entries.
#epub_tocdup = True

epub_use_index = False
