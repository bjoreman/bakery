#!/usr/bin/python
# -*- coding: utf-8 -*-

# Just putting all the introductions on one page is a fine start.
# Also create archive page(s) for all older entries.
# Doing it like Marco makes sense - one start page and archive pages sorted per month.
# When generating each page, I could also generate an introduction for use on these pages.
# Support slug-metadata or something?

import sys
import markdown
import os
import codecs
import shutil
import datetime
import time
import re
import multiprocessing
import traceback
import json
import locale
from email.Utils import formatdate

# TODO Remove the need for this
reload(sys)
sys.setdefaultencoding("utf-8")

def archive_for_tag(tag):
	return 'archive-' + tag.replace(' ', '-') + '.html'

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
def create_link_object(path, title, intro, modification_time, tags, destination):
	path = path.replace(destination + '/','')
	return {'path' : path, 'title': title, 'intro' : intro, 'modified': modification_time, 'tags': tags}

def get_header(bakery, title="Bakery test", root_path=""):
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

def exc_wrapper(inTuple):
	try:
		return generate_page_html(inTuple)
	except Exception:
		print "Exception " + inTuple[0]
		traceback.print_exc()
		raise

def parse_value(value):
	if (value == '[]'):
		return []
	if (value.startswith('[') and value.endswith(']')):
		value = value.rstrip(']').lstrip('[').split(',')
		value = map(unicode.strip, value)
	return value

def remove_indentation(value):
	return value.lstrip('-').lstrip(' ')

def modification_time_from_filename(name, original_time):
	try:
		return time.mktime(datetime.datetime.strptime(name[0:10], '%Y-%m-%d').timetuple())
	except Exception:
		traceback.print_exc()
		# Intentional ignore
	return original_time

def generate_page_html(inTuple):
	(name, path, bakery) = inTuple
	if should_skip(name):
		return None
	input_file = codecs.open(os.path.join(path, name), mode="r", encoding="utf-8")
	m_time = os.stat(os.path.join(path, name)).st_mtime
	modification_time = m_time
	title = input_file.readline().rstrip("\r\n")
	tags = []
	metadata = {}
	if (title == '---'):
		modification_time = modification_time_from_filename(name, modification_time)
		nextLine = input_file.readline().rstrip("\r\n")
		inSubsection = None
		while (nextLine != title):
			newSection = nextLine.endswith(':')
			isIndented = nextLine.startswith((' ', '\t'))
			data = nextLine.split(':')
			data = map(unicode.strip, data)
			if newSection:
				metadata[data[0]] = []
				inSubsection = data[0]
			elif(len(data) > 1):
				if ((inSubsection is not None) and isIndented):
					metadata[inSubsection].append(map(remove_indentation, data))
				else:
					value = parse_value(data[1])
					metadata[data[0]] = value
			elif(len(data) == 1):
				if inSubsection is not None:
					metadata[inSubsection].append(remove_indentation(data[0]))
			nextLine = input_file.readline().rstrip("\r\n")
		if ('title' in metadata):
			title = metadata['title']
		else:
			title = 'Nameless'
	if ('categories' in metadata):
		if (metadata['categories']):
			tags.extend(metadata['categories'])
	if ('tags' in metadata):
		if (metadata['tags']):
			tags.extend(metadata['tags'])
	def strip_quotes(tag):
		return tag.strip('"')
	tags = map(strip_quotes, tags)
	lines = []
	for line in input_file:
		if line.startswith('TAGS: '):
			tags = line.replace('TAGS: ', '', 1).rstrip("\r\n").split(',')
			tags = map(unicode.strip, tags)
		elif line.startswith('PUBDATE: '):
			modification_time = datetime.datetime.strptime(line.replace('PUBDATE: ', '', 1).rstrip("\r\n"), '%Y-%m-%d')
			modification_time = time.mktime(modification_time.timetuple())
		else:
			lines.append(line)
	if (len(lines) == 0):
		return None
	text = ''.join(lines)
	file = os.path.join(path, name)
	html = markdown.Markdown().convert(text)
	root_path = path
	root_path = root_path.replace(bakery.source + '/','')
	return_path = ''
	for element in root_path.split('/'):
		if(element != bakery.source):
			return_path = return_path + '../'

	full_page = get_header(bakery, title, return_path) + html + get_footer(bakery, return_path)
	# Remove old file extension
	file = file.replace('.txt', '').replace('.mdown','').replace('.md','').replace('.markdown','')
	file = file.replace(bakery.source + '/','')+'.html'
	result_path = os.path.join(bakery.destination, file)
	if m_time > bakery.lastRun:
		with codecs.open(result_path, mode="w", encoding="utf-8") as dest_file:
			dest_file.write(full_page)
	if 'hidden' in tags:
		print '*** Hidden page, not adding to links'
		return None
	else:
		return create_link_object(result_path,title, html, modification_time, tags, bakery.destination)

class Bakery:
	def __init__(self, source=None, destination=None):
		if source is None:
			source = 'sources'
		self.source = source
		if destination is None:
			destination = 'oven'
		self.destination = destination
		self.lastRun = self.get_last_run(destination)
		self.all_links = []
		self.headerText = None
		self.footerText = None
		self.config = {
			'base_url': 'http://www.bjoreman.com/',
			'rss_filename': 'rss.rss',
			'rss_description': 'Latest updates on bjoreman.com',
			'locale': 'en_US',
			'rss_language': 'en',
			'date_format': '%B %d, %Y',
			'rss_editor': 'editor@bjoreman.com (Fredrik Bj&#246;reman)',
			'rss_webmaster': 'webmaster@bjoreman.com (Fredrik Bj&#246;reman)',
			'index_title': 'bjoreman.com',
			'archive_all_posts': 'All posts',
			'archive_filter_by_tag': 'Filter by tag:',
			'archive_all_posts': 'Archive - all posts',
			'archive_posts_tagged': 'Archive - posts tagged'
		}
		if os.path.isfile('bakery_config.json'):
			strings = json.load(open('bakery_config.json'))
			for key in strings:
				self.config[key] = strings[key]
		locale.setlocale(locale.LC_ALL, str(self.config['locale']))
		json.dump(self.config, open('bakery_config.json', 'w'), sort_keys=True, indent=4)

	def get_string(self, key):
		return self.config[key]

	def get_last_run(self, destination):
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
			results = pool.map(exc_wrapper, self.zip_with_scalar(files, root))
			for result in results:
				if result != None:
					self.all_links.append(result)

	def format_datetime_for_rss(self, datetime):
		return formatdate(float(datetime.strftime('%s')), True)
		#return datetime.strftime('%a, %d %b %Y %H:%M:%S') + ' EST'

	def format_datetime_for_page(self, datetime):
		return datetime.strftime(self.get_string('date_format'))

	def create_news_and_feeds(self):
		input_file = codecs.open(self.source + "/rss.template", mode="r", encoding="utf-8")
		text = input_file.read()
		text = text.replace("##TITLE##", self.get_string('index_title'))
		text = text.replace("##BASE_URL##", self.get_string('base_url'))
		text = text.replace("##RSS_FILENAME##", self.get_string('rss_filename'))
		text = text.replace("##DESCRIPTION##", self.get_string('rss_description'))
		text = text.replace("##LANGUAGE##", self.get_string('rss_language'))
		text = text.replace("##EDITOR##", self.get_string('rss_editor'))
		text = text.replace("##WEBMASTER##", self.get_string('rss_webmaster'))
		count = 1;
		content = ''
		for link in self.all_links:
			description = link['intro'];
			description = description.replace('../', '')
			description = description.replace('href="', 'href="' + self.get_string('base_url'))
			description = description.replace('src="', 'src="' + self.get_string('base_url'))
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
			content += '\t<guid>' + self.get_string('base_url')+link['path']+'</guid>\n'
			content += '\t<title>'+link['title']+'</title>\n'
			content += '\t<description><![CDATA['+description+']]></description>\n'
			content += '\t<link>' + self.get_string('base_url')+link['path']+'</link>\n'
			content += '\t<pubDate>'+self.format_datetime_for_rss(datetime.datetime.fromtimestamp(link['modified']))+'</pubDate>\n'
			content += '</item>\n'
			count = count + 1
		text = text.replace("##CONTENT##", content)
		with codecs.open(os.path.join(self.destination, self.get_string('rss_filename')), mode="w", encoding="utf-8") as dest_file:
			dest_file.write(text)

	def modified(self, item):
		return item['modified']

	def sort_links(self):
		self.all_links.sort(key=self.modified, reverse=True)

	def generate_index(self):
		result = ''
		for index in range(5):
			link = self.all_links[index]
			result += '<div class="post">'
			if link['tags']:
				result += '<div class="tagWrapper">'
				for tag in link['tags']:
					result += '<div class="tags '+ tag +'"><a href="'+ archive_for_tag(tag) +'">' + tag + '</a></div>'
				result += '</div>'
			result += ('<div class="datestamp">'+self.format_datetime_for_page(datetime.datetime.fromtimestamp(link['modified']))+'</div>')
			result += '<a href="'+link['path']+'"><h1>' + link['title'] + '</h1></a>'
			result += link['intro'].replace('../', '')
			result += '</div>'
		return_path = ''
		result = get_header(self, self.get_string('index_title'), return_path) + result + get_footer(self, return_path)
		with codecs.open(os.path.join(self.destination, 'index.html'), mode="w", encoding="utf-8") as dest_file:
			dest_file.write(result)

	def generate_archive_page(self, links, filename, headline, all_tags):
		result = '<p> ' + self.get_string('archive_filter_by_tag')
		for tag in all_tags:
			result += '<a href="' + archive_for_tag(tag) + '">' + tag + '</a> | '
		result += '<a href="archive.html">' + self.get_string('archive_all_posts') + '</a>'
		result += '</p>'
		result += '<ul class="mainList">'
		for link in links:
			result +=  ('<li><a href="'+link['path']+'">'+link['title']+'</a>')
			result += ('<p class="datestamp">'+self.format_datetime_for_page(datetime.datetime.fromtimestamp(link['modified']))+'</p>')
			result += ('</li>')
		result += '</ul>'
		return_path = ''
		result = get_header(self, headline, return_path) + result + get_footer(self, return_path)
		with codecs.open(os.path.join(self.destination, filename), mode="w", encoding="utf-8") as dest_file:
			dest_file.write(result)

	def generate_archive(self):
		all_tags = []
		for link in self.all_links:
			all_tags.extend(link['tags'])
		all_tags = list(set(all_tags))
		all_tags.sort()

		self.generate_archive_page(self.all_links, 'archive.html', self.get_string('archive_all_posts'), all_tags)

		for tag in all_tags:
			tagged_links = []
			for link in self.all_links:
				if tag in link['tags']:
					tagged_links.append(link)
			self.generate_archive_page(tagged_links, archive_for_tag(tag), self.get_string('archive_posts_tagged') + ' "' + tag + '"', all_tags)

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
		print 'Creating archive'
		self.generate_archive()
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