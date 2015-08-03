import sublime
import sublime_plugin
import os.path
import re

class PastageCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		if not len(self.text): return

		file_name = self.view.file_name()
		self.file_ext = os.path.splitext(file_name)[1] if file_name else ""

		# remove leading and trailing whitespace
		self.text = self.text.strip()
		# remove whitespace from empty lines
		self.text = re.sub(r"^\s+$", "", self.text, 0, re.M)
		# remove zero-width spaces (common to trac links)
		self.text = re.sub(r"\u200B", "", self.text)
		# replace orphaned hyphens with en dashes
		self.text = re.sub(r"(\s+)-(\s+)", r"\1–\2", self.text)

		self.process_lists()
		self.process_links()
		self.process_whitespace()

		for region in self.view.sel(): self.view.replace(edit, region, self.text)

	def process_lists(self):
		# replace bullets with list tags
		self.text = re.sub(r"•\s*(.+)", r"<li>\1</li>", self.text, 0, re.M)
		# remove newlines between list tags
		self.text = re.sub(r"</li>\n<li>", "</li><li>", self.text)

		if self.file_ext == ".xml":
			el = "li"
		else:
			# wrap lists in unordered list tags
			self.text = re.sub(r"(<li>.+</li>)", r"<ul>\1</ul>", self.text, 0, re.M)
			el = "ul"
		
		# replace leading and trailing newlines around lists
		self.text = re.sub(re.compile("\n{2,}(<" + el + ">)"), r"<br><br>\1", self.text)
		self.text = re.sub(re.compile("\n(<" + el + ">)"), r"\1", self.text)
		self.text = re.sub(re.compile("(</" + el + ">)\n+"), r"\1<br>", self.text)

	def process_whitespace(self):
		# replace newlines with break tags
		self.text = re.sub(r"\n", "<br>", self.text)
		# ensure two line breaks between sentences on newlines
		self.text = re.sub(r"([.?!]\s*)<br>(\s*\w)", r"\1<br><br>\2", self.text)
		# disallow more than two break tags
		self.text = re.sub(r"<br><br>(<br>)+", "<br><br>", self.text)
		# normalise whitespace
		self.text = re.sub(r"\s+", " ", self.text)
		# remove leading and trailing whitespace around break tags and lists
		self.text = re.sub(r"\s+(<(br|/?(ul|li))>)", r"\1", self.text)
		self.text = re.sub(r"(<(br|/?(ul|li))>)\s+", r"\1", self.text)

	def process_links(self):
		if self.file_ext == ".json":
			anchor = r"<a href='\1' target='_blank'>\1</a>"
			mailto = r"<a href='mailto:\1'>\1</a>"
		else:
			anchor = r'<a href="\1" target="_blank">\1</a>'
			mailto = r'<a href="mailto:\1">\1</a>'

		# wrap links in anchor tags
		self.text = re.sub(re.compile(
			"((ht|f)tp(s?)\:\/\/[0-9a-zA-Z]([-.\w]*[0-9a-zA-Z])*(:(0-9)*)"
			"*(\/?)([a-zA-Z0-9\-\.\?\,\'\/\\\+&amp;%\$#_]*)?)"
		), anchor, self.text)
		# wrap emails in mailto anchors
		self.text = re.sub(r"(\w+@\w+(?:\.\w+)+)", mailto, self.text)

	def is_enabled(self, **args):
		self.text = sublime.get_clipboard()

		if not len(self.text): return False

		return True