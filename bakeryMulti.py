#!/usr/bin/python
# -*- coding: utf-8 -*-

# Just putting all the introductions on one page is a fine start.
# Also create archive page(s) for all older entries.
# Doing it like Marco makes sense - one start page and archive pages sorted per month.
# When generating each page, I could also generate an introduction for use on these pages.
# Generate intro either treated as Markdown, or make sure it does not contain anything which needs formatting.

import sys
import markdown
import os
import codecs
import shutil
import datetime
import time
import re
import multiprocessing

def should_skip(name):
	if name.endswith(".txt"):
		return False
	if name.endswith(".mdown"):
		return False
	if name.endswith(".md"):
		return False
	if name.endswith(".markdown"):
		return False
	return True

# Should pass in creation timestamp here I think.
def create_link_object(path, title, intro, modification_time, tags):
	path = path.replace('oven/','')
	#print 'Adding ' + path + ' to links'
	return {'path' : path, 'title': title, 'intro' : intro, 'modified': modification_time, 'tags': tags}

def get_header(bakery, title="Bakery test", scripts=None, root_path=""):
	if(bakery.headerText is None):
		input_file = codecs.open(bakery.source + "/header.template", mode="r", encoding="utf-8")
		bakery.headerText = input_file.read()
	result = bakery.headerText.replace("##TITLE##", title)
	result = result.replace("##ROOT_PATH##", root_path)
	return result

def get_footer(bakery, root_path=""):
	if(bakery.footerText is None):
		input_file = codecs.open(bakery.source + "/footer.template", mode="r", encoding="utf-8")
		bakery.footerText = input_file.read()
	result = bakery.footerText.replace("##ROOT_PATH##", root_path)
	return result

def generate_page_html(inTuple):
	(name, path, bakery) = inTuple
	if should_skip(name):
		return
	input_file = codecs.open(os.path.join(path, name), mode="r", encoding="utf-8")
	m_time = os.stat(os.path.join(path, name)).st_mtime
	modification_time = m_time
	title = input_file.readline().rstrip("\r\n")
	lines = []
	intro = ''
	tags = []
	for line in input_file:
		if line.startswith('TAGS: '):
			tags = line.replace('TAGS: ', '', 1).rstrip("\r\n").split(',')
			tags = map(unicode.strip, tags)
		elif line.startswith('PUBDATE: '):
			modification_time = datetime.datetime.strptime(line.replace('PUBDATE: ', '', 1).rstrip("\r\n"), '%Y-%m-%d')
			modification_time = time.mktime(modification_time.timetuple())
		else:
			lines.append(line)
	text = ''.join(lines)
	file = os.path.join(path, name)
	html = markdown.Markdown().convert(text)
	root_path = path
	root_path = root_path.replace('sources/','')
	#print root_path
	return_path = ''
	for element in root_path.split('/'):
		if(element != 'sources'):
			return_path = return_path + '../'

	html = get_header(bakery, title, None, return_path) + html + get_footer(bakery, return_path)
	# Remove old file extension
	file = file.replace('.txt', '').replace('.mdown','').replace('.md','').replace('.markdown','')
	file = file.replace('sources/','')+'.html'
	result_path = os.path.join(bakery.destination, file)
	if m_time > bakery.lastRun:
		with codecs.open(result_path, mode="w", encoding="utf-8") as dest_file:
			dest_file.write(html)
	if 'hidden' in tags:
		print '*** Hidden page, not adding to links'
		return None
	else:
		return create_link_object(result_path,title, html, modification_time, tags)

class Bakery:
	def __init__(self, source=None, destination=None):
		if source is None:
			source = 'sources'
		self.source = source
		if destination is None:
			destination = 'oven'
		self.destination = destination
		self.lastRun = self.getLastRun(destination)
		self.all_links = []
		self.headerText = None
		self.footerText = None

	def getLastRun(self, destination):
		path = os.path.join(self.destination, '.bakeryData')
		if os.path.isfile(path):
			input_file = codecs.open(path, mode="r", encoding="utf-8")
			lastRun = input_file.read()
			return float(lastRun)
		return None

	def copy_directories_and_files(self):
		if self.lastRun is None:
			shutil.rmtree(self.destination, ignore_errors = True)
			shutil.copytree(self.source, self.destination, ignore=shutil.ignore_patterns('*.txt', '*.md', '*.mdown', '*.markdown', '*.template'))

	def process_folders(self):
		self.process_folder(self.source, None)

	def process_folder(self, folder, parent_folder):
		self.build_pages(folder)

	def zip_with_scalar(self, l, o):
	    return ((i, o, self) for i in l)

	def build_pages(self, folder):
		pool = multiprocessing.Pool()
		for root, dirs, files in os.walk(folder, topdown=False):
			results = pool.map(generate_page_html, self.zip_with_scalar(files, root))
			for result in results:
				if result != None:
					self.all_links.append(result)

	def format_datetime_for_rss(self, datetime):
		return datetime.strftime('%a, %d %b %Y %H:%M:%S') + ' EST'

	def format_datetime_for_page(self, datetime):
		return datetime.strftime('%B %d, %Y')

	def create_news_and_feeds(self):
		input_file = codecs.open(self.source + "/rss.template", mode="r", encoding="utf-8")
		text = input_file.read()
		count = 1;
		content = ''
		for link in self.all_links:
			description = link['intro'];
			description = description.replace('../', '')
			description = description.replace('href="', 'href="http://www.bjoreman.com/')
			description = description.replace('src="', 'src="http://www.bjoreman.com/')
			pattern = re.compile(r'(<img class="retinaImage")(.*?)(">)')
			description = re.sub(pattern, '', description)
			pattern2 = re.compile(r'(<!DOCTYPE)(.*?)(</div></a>)', re.DOTALL)
			description = re.sub(pattern2, '', description)
			pattern3 = re.compile(r'(<p class="footer">)(.*?)(</html>)', re.DOTALL)
			description = re.sub(pattern3, '', description)
			if count > 10:
				break
			# Replace all groups of ../  before /images with nothing
			# and preferably remove retina images too
			content += '<item>\n'
			content += '\t<guid>http://www.bjoreman.com/'+link['path']+'</guid>\n'
			content += '\t<title>'+link['title']+'</title>\n'
			content += '\t<description><![CDATA['+description+']]></description>\n'
			content += '\t<link>http://www.bjoreman.com/'+link['path']+'</link>\n'
			content += '\t<pubDate>'+self.format_datetime_for_rss(datetime.datetime.fromtimestamp(link['modified']))+'</pubDate>\n'
			content += '</item>\n'
			count = count + 1
		text = text.replace("##CONTENT##", content)
		with codecs.open(os.path.join(self.destination, 'rss.rss'), mode="w", encoding="utf-8") as dest_file:
			dest_file.write(text)

	def modified(self, item):
		return item['modified']

	def sort_links(self):
		self.all_links.sort(key=self.modified, reverse=True)

	# Use a nice template file for this one too, right.
	# And skip that template during other generation.
	# And have a placeholder for content links.
	def generate_index(self):
		result = '<ul class="mainList">'
		#count = 1;
		for link in self.all_links:
			result += ('<li><a href="'+link['path']+'">'+link['title']+'</a>')
			if link['tags']:
				for tag in link['tags']:
					result += '<div class="tags '+ tag +'">' + tag + '</div>'
			result += ('<p class="datestamp">'+self.format_datetime_for_page(datetime.datetime.fromtimestamp(link['modified']))+'</p>')
			result += '</li>'
		result += ('</ul>')
		return_path = ''
		result = get_header(self, 'bjoreman.com', None, return_path) + result + get_footer(self, return_path)
		with codecs.open(os.path.join(self.destination, 'index.html'), mode="w", encoding="utf-8") as dest_file:
			dest_file.write(result)

	def bake(self):
		print 'Baking ' + self.source + ' to ' + self.destination
		print 'Creating folders and copying resources'
		self.copy_directories_and_files()
		print 'Processing folders'
		self.process_folders()
		self.sort_links()
		print 'Generating index page'
		self.generate_index()
		print 'Creating news and feeds'
		self.create_news_and_feeds()
		last_run = time.time()
		with codecs.open(os.path.join(self.destination, '.bakeryData'), mode="w", encoding="utf-8") as dest_file:
			dest_file.write(str(last_run))
		print 'Bake finished!'

def main(argv):
	print 'Welcome to the bakery!'
	# Should not require destination, if none exists put it in a folder inside oven named the same as the source
	if 3 > len(argv) < 1:
		print 'Invalid number of arguments.'
		print 'Usage: bakery.py [source_folder=sources] [destination_folder=oven]'
		sys.exit(1)
	if ((len(argv) == 2) and (argv[1] == "help")):
		print 'Usage: bakery.py [source_folder=sources] [destination_folder=oven]'
		sys.exit(1)
	if len(argv) is 1:
		argv.append(None)
	if len(argv) is 2:
		argv.append(None)
	bakery = Bakery(argv[1], argv[2])
	start = time.time()
	bakery.bake()
	print 'Baked for ', time.time()-start, ' seconds.'
	print 'Thanks for using Bakery!'

if __name__ == '__main__':
	main(sys.argv)