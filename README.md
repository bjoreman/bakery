# bakery
The Python script I use to generate bjoreman.com from Markdown files and some minimal templates.

Requires the Python Markdown package to be installed.

Bakery started as the simplest possible script which could possibly do the job. Starting off, it did no caching between runs, no smart tracking, no splitting into pages or anything else smart, really. It has since picked up some capabilities and now uses multiple processes for quicker generation, only writes changed files to disk, and creation of archive pages based on tags. Other than that though, still pretty un-smart.

In fact, just reading the code might be quicker and more illuminating than reading this.

*Note* that there are two scripts: bakery.py and bakeryMulti.py. bakery.py is thoroughly deprecated and kept around for reasons of … nostalgia I guess? It works fine, but does a lot less and only runs in a single process.

Invoked without arguments, Bakery expects to take all content from a folder named "sources" and process them into a folder named "oven".

Bakery expects some template files which it will use as page headers and footers:
  * header.template
  * footer.template
  * rss.template
  
The templates go straight into the sources folder. Example files - the ones I use for bjoreman.com - are included in the repo.

Markdown files - files with the extensions .md, .markdown and .txt are considered Markdown - will be processed into HTML and wrapped with the header and footer templates. Other files, as well as folders, are copied as-is.

In the header, the string ##TITLE## will be replaced with the first line of the Markdown file. Both header and footer can also use ##ROOT_PATH## to link to the root of the site.

The rss template has ##CONTENT## where the items for all generated news items should go.

The Markdown files can also contain two special lines, starting with TAGS: and PUBDATE: TAGS will be displayed on the index page, PUBDATE is simply a publication date in the form YYYY-MM-DD. It is both displayed and used for sorting of generated pages. If not present, the modification date of the file will be used to determine where the page appears on the index page.
If TAGS contain the word hidden, the file will be generated and placed in the site, but not linked from the index page.
