# bakery
The Python script I use to generate bjoreman.com from Markdown files and some minimal templates.

Bakery is the simplest possible script which could possibly do the job. It does no caching between runs, no smart tracking, no splitting into pages or anything else smart, really.

In fact, just reading the code might be quicker and more illuminating than reading this.

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
